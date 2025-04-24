import logging
from gurobipy import Model, GRB, quicksum
import pandas as pd

#Currently the model gravitates towards suggesting only premium models (except mountain bikes). To address this we need to introduce more crossover bike variants that can use parts from different types (Type A, Type B, Type C,...)
#Introduce individual sales probabilities (full price and discount prices) for each bike type
#Fix sales probabilities so they don't change on each model run
#Variate the standard deviation to see their impact on the KPI and how the suggested solution changes
#@Maryam Jahangir will push her code to the repository and add test data there as well
#Objective function should: maximize profit, minimize production time and minimize unused inventory after the production, optionally maximize bike quantity

# Configure logging
logging.basicConfig(
    filename="milp_bike_optimization.log",
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
normalized_probabilities = {"Full Price": 0.1, "10% Discount": 0.7, "15% Discount": 0.2}   #Fix sales probabilities so they don't change on each model run
                                                                                           #Introduce individual sales probabilities (full price and discount prices) for each bike type

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

# Add Crossover Variants       (introduce more crossover bike variants that can use parts from different types (Type A, Type B, Type C,...))
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
    production_time[bike_type] = df["Production Time (hours)"].mean()  # Use average production time
    priority_weights[bike_type] = 1.0  # Default weight for new variants

logging.info("Added crossover variants: %s", crossover_bike_types)

# Build MILP Model   (maximize profit, minimize production time and minimize unused inventory after the production, optionally maximize bike quantity)
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

# Add Quota Constraints
quota_lower_bound = 0.2  # At least 20% non-premium
quota_upper_bound = 0.8  # No more than 80% premium

premium_bike_types = [bike for bike in bike_types if "Premium" in bike]
non_premium_bike_types = [bike for bike in bike_types if bike not in premium_bike_types]

total_bikes = quicksum(x[bike_type] for bike_type in bike_types)
non_premium_bikes = quicksum(x[bike_type] for bike_type in non_premium_bike_types)
premium_bikes = quicksum(x[bike_type] for bike_type in premium_bike_types)

model.addConstr(non_premium_bikes >= quota_lower_bound * total_bikes, name="MinNonPremiumQuota")
model.addConstr(premium_bikes <= quota_upper_bound * total_bikes, name="MaxPremiumQuota")

# Add Penalty for Skewed Production
diversity_penalty = quicksum((x[bike_type] - total_bikes / len(bike_types))**2 for bike_type in bike_types)

# Set Objective Function
model.setObjective(
    profit_term * 0.01 - unused_inventory_term * 2.0 - production_time_term * 3.0 + bike_quantity_term * 1.0 - diversity_penalty * 0,
    GRB.MAXIMIZE
)

# Add Inventory Constraints
for component in components:
    total_required = quicksum(required_qty[(bike_type, component)] * x[bike_type] for bike_type in bike_types)
    model.addConstr(total_required + unused_inventory[component] == available_inventory[component])

logging.info("All constraints added. Starting optimization...")
model.optimize()

# Output Results
if model.status == GRB.OPTIMAL:
    logging.info("Optimal solution found.")
    
    # Objective Function Breakdown
    profit_term_value = profit_term.getValue() * 0.05
    unused_inventory_term_value = unused_inventory_term.getValue() * -2.0
    production_time_term_value = production_time_term.getValue() * -4.0
    bike_quantity_term_value = bike_quantity_term.getValue() * 1.0
    diversity_penalty_value = diversity_penalty.getValue() * 0  # No penalty in this case

    print("\nObjective Function Breakdown:")
    print(f"Profit Term (weighted 0.05): {profit_term_value:.2f}")
    print(f"Unused Inventory Term (weighted -2.0): {unused_inventory_term_value:.2f}")
    print(f"Production Time Term (weighted -4.0): {production_time_term_value:.2f}")
    print(f"Bike Quantity Term (weighted 1.0): {bike_quantity_term_value:.2f}")
    print(f"Diversity Penalty (weighted 0): {diversity_penalty_value:.2f}")
    total_objective_value = (
        profit_term_value +
        unused_inventory_term_value +
        production_time_term_value +
        bike_quantity_term_value +
        diversity_penalty_value
    )
    print(f"Total Objective Value: {total_objective_value:.2f}")

    # Production Results
    production_results = []
    total_production_time = 0
    for bike_type in bike_types:
        produced = int(x[bike_type].x if x[bike_type].x else 0)
        revenue = wasp[bike_type] * produced
        cost = df[df["Bike Type"] == bike_type]["Unit Cost (€)"].sum() * produced
        profit = revenue - cost
        production_time_hours = production_time[bike_type] * produced
        total_production_time += production_time_hours

        production_results.append({
            "Bike Type": bike_type,
            "Produced": produced,
            "WASP (€)": round(wasp[bike_type], 2),
            "Revenue (€)": round(revenue, 2),
            "Profit (€)": round(profit, 2),
            "Production Time (hours)": round(production_time_hours, 2),
        })

    production_df = pd.DataFrame(production_results)
    print("\nProduction Results:")
    print(production_df)

    # Inventory Utilization Results
    inventory_results = []
    for component in components:
        initial_inventory = available_inventory[component]
        utilized_inventory = sum(required_qty[(bike_type, component)] * x[bike_type].x for bike_type in bike_types)
        remaining_inventory = initial_inventory - utilized_inventory

        inventory_results.append({
            "Component": component,
            "Initial Inventory": int(initial_inventory),
            "Utilized Inventory": int(utilized_inventory),
            "Remaining Inventory": int(remaining_inventory),
        })

    inventory_df = pd.DataFrame(inventory_results)
    print("\nInventory Utilization Results:")
    print(inventory_df)

    # Utilized Components Breakdown
    formatted_results = []
    for bike_type in bike_types:
        produced_quantity = int(x[bike_type].x if x[bike_type].x else 0)
        bike_df = df[df["Bike Type"] == bike_type]
        utilized_details = []

        for component in bike_df["Component"].unique():
            required_quantity_per_bike = bike_df.loc[bike_df["Component"] == component, "Required Quantity"].sum()
            utilized_quantity = required_quantity_per_bike * produced_quantity
            component_quality = bike_df.loc[bike_df["Component"] == component, "Quality"].iloc[0]
            utilized_details.append(f"{component} (Quality: {component_quality}): {int(utilized_quantity)}")

        formatted_results.append({
            "Bike Type": bike_type,
            "Produced Bikes": produced_quantity,
            "Utilized Components": ", ".join(bike_df["Component"].unique()),
            "Utilized Quantities (with Quality)": ", ".join(utilized_details),
        })

    formatted_results_df = pd.DataFrame(formatted_results)
    print("\nBike Production and Utilized Components Breakdown:")
    print(formatted_results_df)

else:
    logging.error("No optimal solution found.")
    print("No optimal solution found. Check the log file for details.")

