import logging
from gurobipy import Model, GRB, quicksum
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


# Configure logging
logging.basicConfig(
    filename="weight_experiment.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load Input Data
file_path = "updated_bike_data_with_crossover_variants.xlsx"  # Path to the updated dataset
df = pd.read_excel(file_path)

logging.info("Loaded dataset with %d rows and %d columns.", df.shape[0], df.shape[1])

# Preprocess Data
bike_types = df["Bike Type"].unique()
components = df["Component"].unique()

# Define Parameters
required_qty = {(bike_type, component): 0 for bike_type in bike_types for component in components}
available_inventory = {component: 0 for component in components}
production_time = {bike_type: 0 for bike_type in bike_types}
priority_weights = {bike_type: 0 for bike_type in bike_types}

# Populate Parameters
for bike_type in bike_types:
    bike_df = df[df["Bike Type"] == bike_type]
    production_time[bike_type] = bike_df["Production Time (hours)"].iloc[0]
    priority_weights[bike_type] = bike_df["Priority Weight"].iloc[0]
    for component in bike_df["Component"].unique():
        required_qty[(bike_type, component)] = bike_df.loc[bike_df["Component"] == component, "Required Quantity"].sum()
        available_inventory[component] += bike_df.loc[bike_df["Component"] == component, "Available Inventory"].sum()

# Selling Prices and WASP
markup_percentage = 0.2
selling_prices = {}
normalized_probabilities = {"Full Price": 0.1, "10% Discount": 0.7, "15% Discount": 0.2}

for bike_type in bike_types:
    base_price = df[df["Bike Type"] == bike_type]["Unit Cost (€)"].sum() * (1 + markup_percentage)
    selling_prices[bike_type] = {
        "Full Price": base_price,
        "10% Discount": base_price * 0.9,
        "15% Discount": base_price * 0.85
    }

wasp = {}
for bike_type in bike_types:
    wasp[bike_type] = sum(
        selling_prices[bike_type][category] * normalized_probabilities[category]
        for category in normalized_probabilities
    )

# Crossover Variants
crossover_variants = [
    {"Bike Type": "Hybrid_Crossover", "Component Mix": {"Frame": "Type B", "Wheels": "Type A", "Saddle": "Type C"}},
    {"Bike Type": "Gravel_Crossover", "Component Mix": {"Frame": "Type C", "Wheels": "Type B", "Saddle": "Type A"}}
]

crossover_bike_types = [variant["Bike Type"] for variant in crossover_variants]
bike_types = list(bike_types) + crossover_bike_types

for variant in crossover_variants:
    bike_type = variant["Bike Type"]
    for component, quality in variant["Component Mix"].items():
        required_qty[(bike_type, component)] = df.loc[
            (df["Component"] == component) & (df["Quality"] == quality), "Required Quantity"
        ].sum()
    production_time[bike_type] = df["Production Time (hours)"].mean()
    priority_weights[bike_type] = 1.0

# Experiment with Weight Configurations
profit_weights = [0.01, 0.05, 0.1]
inventory_weights = [-1.0, -2.0, -3.0]
time_weights = [-1.0, -3.0, -5.0]
quantity_weights = [0.5, 1.0, 2.0]

results = []

for pw in profit_weights:
    for iw in inventory_weights:
        for tw in time_weights:
            for qw in quantity_weights:
                # Build MILP Model
                model = Model("Bike Optimization Experiment")
                x = {bike_type: model.addVar(vtype=GRB.INTEGER, name=f"Produce_{bike_type}") for bike_type in bike_types}
                unused_inventory = {component: model.addVar(vtype=GRB.CONTINUOUS, name=f"Unused_{component}") for component in components}

                # Objective Function
                profit_term = quicksum(
                    (wasp[bike_type] - df[df["Bike Type"] == bike_type]["Unit Cost (€)"].sum()) * x[bike_type]
                    for bike_type in bike_types
                )
                unused_inventory_term = quicksum(unused_inventory[component] for component in components)
                production_time_term = quicksum(production_time[bike_type] * x[bike_type] for bike_type in bike_types)
                bike_quantity_term = quicksum(priority_weights[bike_type] * x[bike_type] for bike_type in bike_types)

                model.setObjective(
                    profit_term * pw - unused_inventory_term * iw - production_time_term * tw + bike_quantity_term * qw,
                    GRB.MAXIMIZE
                )

                # Constraints
                total_bikes = quicksum(x[bike_type] for bike_type in bike_types)
                for component in components:
                    total_required = quicksum(required_qty[(bike_type, component)] * x[bike_type] for bike_type in bike_types)
                    model.addConstr(total_required + unused_inventory[component] == available_inventory[component])

                # Optimization
                model.optimize()

                if model.status == GRB.OPTIMAL:
                    # Calculate revenue
                    revenue = sum(wasp[bike_type] * x[bike_type].x for bike_type in bike_types)

                    results.append({
                        "Profit Weight": pw,
                        "Inventory Weight": iw,
                        "Time Weight": tw,
                        "Quantity Weight": qw,
                        "Objective Value": model.objVal,
                        "Total Bikes Produced": total_bikes.getValue(),
                        "Unused Inventory": sum(unused_inventory[component].x for component in components),
                        "Production Time": production_time_term.getValue(),
                        "Profit": profit_term.getValue(),
                        "Revenue (€)": revenue
                    })

# Convert Results to DataFrame
results_df = pd.DataFrame(results)

# Display Results in Plotly Table
fig = go.Figure(data=[go.Table(
    header=dict(values=list(results_df.columns), fill_color='paleturquoise', align='left'),
    cells=dict(values=[results_df[col] for col in results_df.columns], fill_color='lavender', align='left')
)])
fig.update_layout(title="Weight Experiment Results", title_x=0.5)
fig.show()


# Generate a unique configuration identifier
results_df["Weight Configuration"] = results_df.apply(
    lambda row: f"P:{row['Profit Weight']} | I:{row['Inventory Weight']} | T:{row['Time Weight']} | Q:{row['Quantity Weight']}",
    axis=1
)

# Plot Objective Value vs Weight Configurations
fig = px.line(
    results_df,
    x="Weight Configuration",
    y="Objective Value",
    color="Profit Weight",
    title="Objective Value vs Weight Configurations",
    labels={"Objective Value": "Objective Value", "Weight Configuration": "Weight Configurations"},
    markers=True
)

fig.update_layout(
    xaxis_title="Weight Configurations (P=Profit, I=Inventory, T=Time, Q=Quantity)",
    yaxis_title="Objective Value",
    showlegend=True
)

# Save the plot as an HTML file for interactive viewing
plot_file_path = "Objective_Value_vs_Weight_Configurations.html"
fig.write_html(plot_file_path)

plot_file_path
# Display the graph interactively
fig.update_layout(
    title="Weight Experiment Results",
    title_x=0.5
)
fig.show()
