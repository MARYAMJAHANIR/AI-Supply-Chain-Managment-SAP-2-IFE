import logging
from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np
import plotly.graph_objects as go

#Variate the standard deviation to see their impact on the KPI and how the suggested solution changes

# Configure logging
logging.basicConfig(
    filename="sensitivity_analyation.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load Input Data
file_path = "updated_bike_data_with_crossover_variants.xlsx"
df = pd.read_excel(file_path)

logging.info("Loaded dataset with %d rows and %d columns.", df.shape[0], df.shape[1])

# Preprocess Data
bike_types = df["Bike Type"].unique()
components = df["Component"].unique()
logging.info("Identified %d unique bike types and %d unique components.", len(bike_types), len(components))

# Define Parameters
required_qty = {
    (bike_type, component): 0 for bike_type in bike_types for component in components
}
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

logging.info("Processed required quantities and available inventories for all components.")

# Selling Prices and WASP
markup_percentage = 0.2
selling_prices = {}
probability_distributions = {
    "Full Price": {"mean": 0.1, "std": 0.02},
    "10% Discount": {"mean": 0.7, "std": 0.05},
    "15% Discount": {"mean": 0.2, "std": 0.03},
}

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
        selling_prices[bike_type][category] * probability_distributions[category]["mean"]
        for category in probability_distributions
    )

# Build MILP Model
model = Model("Enhanced Bike Optimization")
x = {bike_type: model.addVar(vtype=GRB.INTEGER, name=f"Produce_{bike_type}") for bike_type in bike_types}
unused_inventory = {component: model.addVar(vtype=GRB.CONTINUOUS, name=f"Unused_{component}") for component in components}

profit_term = quicksum(
    (wasp[bike_type] - df[df["Bike Type"] == bike_type]["Unit Cost (€)"].sum()) * x[bike_type]
    for bike_type in bike_types
)
unused_inventory_term = quicksum(unused_inventory[component] for component in components)
production_time_term = quicksum(production_time[bike_type] * x[bike_type] for bike_type in bike_types)
bike_quantity_term = quicksum(priority_weights[bike_type] * x[bike_type] for bike_type in bike_types)

# Set Objective Function
model.setObjective(
    profit_term * 0.01 - unused_inventory_term * 2.0 - production_time_term * 3.0 + bike_quantity_term * 1.0,
    GRB.MAXIMIZE
)

# Add Inventory Constraints
for component in components:
    total_required = quicksum(required_qty[(bike_type, component)] * x[bike_type] for bike_type in bike_types)
    model.addConstr(total_required + unused_inventory[component] == available_inventory[component])

logging.info("All constraints added. Starting optimization...")
model.optimize()

# Sensitivity Analysis: Impact of Standard Deviation
def perform_sensitivity_analysis_with_std(
    bike_types, selling_prices, wasp, df, probability_distributions, x, production_time
):
    sensitivity_results = []

    # Define variations: mean ± std
    variations = [-1, 0, 1]  # -1 std, base probabilities, +1 std

    # Perform sensitivity analysis for each bike type
    for bike_type in bike_types:
        produced = x[bike_type].x if x[bike_type].x else 0  # Production quantity from the base optimization
        baseline_revenue = wasp[bike_type] * produced
        total_cost = df[df["Bike Type"] == bike_type]["Unit Cost (€)"].sum() * produced
        baseline_profit = baseline_revenue - total_cost
        production_time_hours = production_time[bike_type] * produced  # Calculate production time

        logging.info(f"--- Sensitivity Analysis for Bike Type: {bike_type} ---")
        logging.info(f"Produced: {produced}, Baseline WASP (€): {wasp[bike_type]:.2f}, "
                     f"Baseline Revenue (€): {baseline_revenue:.2f}, Total Cost (€): {total_cost:.2f}, "
                     f"Baseline Profit (€): {baseline_profit:.2f}, Production Time (hours): {production_time_hours:.2f}")

        # Analyze each variation
        for variation in variations:
            logging.info(f"--- Variation: {variation:+.1f} std ---")

            # Adjust probabilities for each price tier
            adjusted_probabilities = {}
            for category in probability_distributions:
                adjusted_prob = max(0, probability_distributions[category]["mean"] +
                                    variation * probability_distributions[category]["std"])
                adjusted_probabilities[category] = adjusted_prob
                logging.info(f"Price Tier: {category}, Base Prob: {probability_distributions[category]['mean']:.2f}, "
                             f"Adjusted Prob: {adjusted_prob:.2f}")

            # Normalize adjusted probabilities
            total_adjusted = sum(adjusted_probabilities.values())
            normalized_adjusted_probabilities = {
                category: prob / total_adjusted
                for category, prob in adjusted_probabilities.items()
            }
            logging.info(f"Normalized Adjusted Probabilities: {normalized_adjusted_probabilities}")

            # Recalculate WASP with adjusted probabilities
            adjusted_wasp = 0
            for price_category in selling_prices[bike_type]:
                contribution = selling_prices[bike_type][price_category] * normalized_adjusted_probabilities[price_category]
                adjusted_wasp += contribution
                logging.info(f"Price Tier: {price_category}, Selling Price (€): {selling_prices[bike_type][price_category]:.2f}, "
                             f"Normalized Prob: {normalized_adjusted_probabilities[price_category]:.2f}, "
                             f"Contribution to WASP (€): {contribution:.2f}")

            logging.info(f"Adjusted WASP (€): {adjusted_wasp:.2f}")

            # Calculate new revenue and profit
            adjusted_revenue = adjusted_wasp * produced
            adjusted_profit = adjusted_revenue - total_cost

            logging.info(f"Adjusted Revenue (€): {adjusted_revenue:.2f}, Adjusted Profit (€): {adjusted_profit:.2f}")

            # Append results for reporting
            sensitivity_results.append({
                "Bike Type": bike_type,
                "Produced": int(produced),
                "Baseline WASP (€)": round(wasp[bike_type], 2),
                "Variation (std)": f"{variation:+.1f}",
                "Adjusted WASP (€)": round(adjusted_wasp, 2),
                "Adjusted Revenue (€)": round(adjusted_revenue, 2),
                "Adjusted Profit (€)": round(adjusted_profit, 2),
                "Production Time (hours)": round(production_time_hours, 2),
            })

    # Return results as a DataFrame
    return pd.DataFrame(sensitivity_results)

# Run Sensitivity Analysis
sensitivity_results = perform_sensitivity_analysis_with_std(
    bike_types, selling_prices, wasp, df, probability_distributions, x, production_time
)

# Display Results in a Table
def plot_sensitivity_table(df, title):
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns), fill_color="paleturquoise", align="left"),
        cells=dict(values=[df[col] for col in df.columns], fill_color="lavender", align="left")
    )])
    fig.update_layout(title_text=title, title_x=0.5, width=1200, height=700)
    fig.show()

plot_sensitivity_table(sensitivity_results, "Sensitivity Analysis Results with Varying Standard Deviations")
