import streamlit as st
import pandas as pd
import plotly.express as px

# User Instructions
st.title("Bicycle Production Dashboard")

st.write("""
This dashboard allows users to visualize bicycle production metrics and analyze scenarios based on leftover components. 
To get started, please upload your enhanced bicycle data CSV file below.
""")

# File uploader for users to upload their data
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Load the enhanced dummy data from the uploaded file
    data = pd.read_csv(uploaded_file)

    # Ensure 'Date' is in datetime format
    data['Date'] = pd.to_datetime(data['Date'])

    # Process data to extract relevant information
    # Monthly sales and inventory data
    monthly_sales = data.groupby(data['Date'].dt.to_period('M')).agg({'Total Sales (€)': 'sum'}).reset_index()
    monthly_sales['Date'] = monthly_sales['Date'].dt.to_timestamp()  # Convert Period to timestamp for Plotly

    monthly_inventory = data.groupby(data['Date'].dt.to_period('M')).agg({
        'Frames': 'sum',
        'Wheels': 'sum',
        'Gears': 'sum',
        'Handlebars': 'sum'
    }).reset_index()
    monthly_inventory['Date'] = monthly_inventory['Date'].dt.to_timestamp()  # Convert Period to timestamp for Plotly

    # Merge sales and inventory data
    combined_data = pd.merge(monthly_sales, monthly_inventory, on='Date')

    # Display Summary Metrics
    st.subheader("Summary Metrics")
    total_sales = combined_data['Total Sales (€)'].sum()
    total_frames = combined_data['Frames'].sum()
    total_wheels = combined_data['Wheels'].sum()
    total_gears = combined_data['Gears'].sum()
    total_handlebars = combined_data['Handlebars'].sum()

    st.metric(label="Total Sales (€)", value=f"€{total_sales:,.2f}")
    st.metric(label="Total Frames Available", value=total_frames)
    st.metric(label="Total Wheels Available", value=total_wheels)
    st.metric(label="Total Gears Available", value=total_gears)
    st.metric(label="Total Handlebars Available", value=total_handlebars)

    # Sales and Inventory Visualization
    st.subheader("Monthly Sales and Inventory Trends")
    fig = px.line(combined_data, x='Date', 
                  y=['Total Sales (€)', 'Frames', 'Wheels', 'Gears', 'Handlebars'],
                  title='Monthly Sales and Inventory Trends',
                  labels={'value': 'Count', 'Date': 'Month'},
                  markers=True)

    st.plotly_chart(fig)

    # Scenario Analysis
    st.subheader("Scenario Analysis for Utilizing Leftover Components")

    # Define scenarios based on leftover components
    scenarios = {
        'Scenario 1': {
            'description': 'Produce additional Mountain Bikes from leftover components',
            'potential_revenue': total_sales * 1.1,  # 10% increase
            'expected_inventory_reduction': '10% of Frames and Wheels',
        },
        'Scenario 2': {
            'description': 'Utilize all leftover inventory to produce City Bikes',
            'potential_revenue': total_sales * 1.15,  # 15% increase
            'expected_inventory_reduction': 'Complete utilization of Gears and Handlebars',
        },
        'Scenario 3': {
            'description': 'Maximize production of BMX Bikes using all leftovers',
            'potential_revenue': total_sales * 1.2,  # 20% increase
            'expected_inventory_reduction': 'Complete utilization of all components',
        },
    }

    # Dropdown for scenario selection
    selected_scenario = st.selectbox("Select a Scenario:", list(scenarios.keys()))

    # Display selected scenario details
    if selected_scenario:
        details = scenarios[selected_scenario]
        st.markdown(f"### **{selected_scenario}:** {details['description']}")
        st.markdown(f"**Potential Revenue:** €{details['potential_revenue']:.2f}")
        st.markdown(f"**Expected Inventory Reduction:** {details['expected_inventory_reduction']}")

    # Button to visualize scenario revenue
    if st.button('Show Potential Revenue for Selected Scenario'):
        st.success(f"Potential Revenue for {selected_scenario}: €{details['potential_revenue']:.2f}")

    # Visualization of scenario potential revenues
    scenario_names = list(scenarios.keys())
    potential_revenues = [details['potential_revenue'] for details in scenarios.values()]

    # Bar chart for scenario potential revenues
    fig_scenarios = px.bar(x=scenario_names, y=potential_revenues,
                            labels={'x': 'Scenario', 'y': 'Potential Revenue (€)'},
                            title='Potential Revenue by Scenario')
    st.plotly_chart(fig_scenarios)

else:
    st.info("Please upload your CSV file to see the dashboard.")

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import numpy as np

# # User Instructions
# st.title("Bicycle Production Dashboard")

# # Tabbed interface
# tab1, tab2, tab3, tab4, tab5 = st.tabs(["Inventory", "Sales", "Components", "Machines", "Leftover Components"])

# # Mock Data for Inventory, Sales, and Components
# def load_data():
#     # Generate mock data for demonstration
#     data = {
#         'Date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
#         'Total Sales (€)': np.random.randint(5000, 20000, size=12),
#         'Frames': np.random.randint(50, 100, size=12),
#         'Wheels': np.random.randint(100, 200, size=12),
#         'Gears': np.random.randint(20, 50, size=12),
#         'Handlebars': np.random.randint(10, 30, size=12),
#         'Machine Status': ['Active', 'Idle', 'Active', 'Under Maintenance', 'Active'] * 2 + ['Idle'] * 2,
#         'Next Idle Date': pd.date_range(start='2023-01-15', periods=12, freq='5D'),
#         'Next Maintenance Date': pd.date_range(start='2023-02-01', periods=12, freq='10D')
#     }
#     return pd.DataFrame(data)

# # Load data
# data = load_data()

# # Tab 1: Inventory
# with tab1:
#     st.subheader("Current Inventory Levels")
#     st.dataframe(data[['Frames', 'Wheels', 'Gears', 'Handlebars']])
    
# # Tab 2: Sales
# with tab2:
#     st.subheader("Historical Sales Data")
#     fig_sales = px.bar(data, x='Date', y='Total Sales (€)', title='Total Sales Over Time')
#     st.plotly_chart(fig_sales)

# # Tab 3: Components
# with tab3:
#     st.subheader("Components Trend Analysis")
#     fig_components = px.line(data, x='Date', 
#                               y=['Frames', 'Wheels', 'Gears', 'Handlebars'],
#                               title='Monthly Components Trends',
#                               labels={'value': 'Quantity', 'Date': 'Month'},
#                               markers=True)
#     st.plotly_chart(fig_components)
    
#     # Pie chart for leftover components
#     leftover_data = {
#         'Component Type': ['Frames', 'Wheels', 'Gears', 'Handlebars'],
#         'Quantities': [data['Frames'].sum() * 0.1, data['Wheels'].sum() * 0.1, data['Gears'].sum() * 0.1, data['Handlebars'].sum() * 0.1]
#     }
#     df_leftover = pd.DataFrame(leftover_data)
#     fig_pie = px.pie(df_leftover, values='Quantities', names='Component Type', title='Distribution of Leftover Components')
#     st.plotly_chart(fig_pie)

# # Tab 4: Machines
# with tab4:
#     st.subheader("Machine Schedules")
#     st.dataframe(data[['Machine Status', 'Next Idle Date', 'Next Maintenance Date']])

# # Tab 5: Leftover Components
# with tab5:
#     st.subheader("Leftover Components Analysis")
    
#     # Button to generate scenarios
#     if st.button("Generate Scenarios"):
#         # Simulate AI analysis
#         st.success("AI is analyzing current inventory and suggesting potential uses for leftover components...")
        
#         # Display mock results
#         st.markdown("### New Product Scenarios:")
#         st.markdown("1. Foldable City Bike - Utilize leftover frames and wheels.")
#         st.markdown("2. Electric Bicycle - Use leftover gears and handlebars.")
        
#         # Nearby retailers mock data
#         st.markdown("### Nearby Retailers:")
#         st.markdown("1. Retailer A - Demand for Frames.")
#         st.markdown("2. Retailer B - Demand for Wheels.")
        
#         # Add a map view simulation (mock)
#         st.markdown("### Retailer Map")
#         st.write("Map displaying retailers and their demand for components would be here.")

#     # User selects a new product scenario
#     selected_product = st.selectbox("Select a New Product Scenario:", ["Foldable City Bike", "Electric Bicycle"])
    
#     if selected_product:
#         st.markdown(f"You selected: **{selected_product}**")
#         st.markdown("Analyzing production planning...")

#         # Display production planning mock data
#         st.markdown("### Production Planning Schedule:")
#         st.write("""
#             - Machine 1: Active from Jan 15 to Feb 10
#             - Machine 2: Scheduled for maintenance on Feb 20
#             - Estimated Completion: 100 units by Mar 1
#             - Potential Revenue: €15,000
#         """)

#         if st.button("Confirm Production Plan"):
#             st.success("Production plan confirmed for the selected scenario!")

# # Footer
# st.write("Dashboard developed for Bicycle Manufacturing Company")


# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import numpy as np

# # User Instructions
# st.title("Bicycle Production Dashboard")

# # Tabbed interface
# tab1, tab2, tab3, tab4, tab5 = st.tabs(["Inventory", "Sales", "Components", "Machines", "Leftover Components"])

# # File uploader for sales data
# sales_file = st.file_uploader("Upload Sales CSV file", type=["csv"], key="sales")

# # File uploader for inventory data
# inventory_file = st.file_uploader("Upload Inventory CSV file", type=["csv"], key="inventory")

# # Load Data Function
# def load_data():
#     # Generate mock data for demonstration
#     data = {
#         'Date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
#         'Total Sales (€)': np.random.randint(5000, 20000, size=12),
#         'Frames': np.random.randint(50, 100, size=12),
#         'Wheels': np.random.randint(100, 200, size=12),
#         'Gears': np.random.randint(20, 50, size=12),
#         'Handlebars': np.random.randint(10, 30, size=12),
#         'Machine Status': ['Active', 'Idle', 'Active', 'Under Maintenance', 'Active'] * 2 + ['Idle'] * 2,
#         'Next Idle Date': pd.date_range(start='2023-01-15', periods=12, freq='5D'),
#         'Next Maintenance Date': pd.date_range(start='2023-02-01', periods=12, freq='10D')
#     }
#     return pd.DataFrame(data)

# # Initialize data variable
# data = None

# # Load data from uploaded files
# if sales_file is not None and inventory_file is not None:
#     sales_data = pd.read_csv(sales_file)
#     inventory_data = pd.read_csv(inventory_file)

#     # Ensure 'Date' is in datetime format
#     sales_data['Date'] = pd.to_datetime(sales_data['Date'])
#     inventory_data['Date'] = pd.to_datetime(inventory_data['Date'])

#     # Merge the dataframes if needed or handle them separately
#     data = {'sales': sales_data, 'inventory': inventory_data}
# else:
#     # Load mock data if no files are uploaded
#     data = load_data()

# # Tab 1: Inventory
# with tab1:
#     st.subheader("Current Inventory Levels")
#     if 'inventory' in data:
#         st.dataframe(data['inventory'][['Frames', 'Wheels', 'Gears', 'Handlebars']])
#     else:
#         st.dataframe(data[['Frames', 'Wheels', 'Gears', 'Handlebars']])
    
# # Tab 2: Sales
# with tab2:
#     st.subheader("Historical Sales Data")
#     if 'sales' in data:
#         fig_sales = px.bar(data['sales'], x='Date', y='Total Sales (€)', title='Total Sales Over Time')
#         st.plotly_chart(fig_sales)
#     else:
#         fig_sales = px.bar(data, x='Date', y='Total Sales (€)', title='Total Sales Over Time')
#         st.plotly_chart(fig_sales)

# # Tab 3: Components
# with tab3:
#     st.subheader("Components Trend Analysis")
#     if 'inventory' in data:
#         fig_components = px.line(data['inventory'], x='Date', 
#                                   y=['Frames', 'Wheels', 'Gears', 'Handlebars'],
#                                   title='Monthly Components Trends',
#                                   labels={'value': 'Quantity', 'Date': 'Month'},
#                                   markers=True)
#         st.plotly_chart(fig_components)
        
#         # Pie chart for leftover components
#         leftover_data = {
#             'Component Type': ['Frames', 'Wheels', 'Gears', 'Handlebars'],
#             'Quantities': [data['inventory']['Frames'].sum() * 0.1, 
#                            data['inventory']['Wheels'].sum() * 0.1, 
#                            data['inventory']['Gears'].sum() * 0.1, 
#                            data['inventory']['Handlebars'].sum() * 0.1]
#         }
#         df_leftover = pd.DataFrame(leftover_data)
#         fig_pie = px.pie(df_leftover, values='Quantities', names='Component Type', title='Distribution of Leftover Components')
#         st.plotly_chart(fig_pie)

# # Tab 4: Machines
# with tab4:
#     st.subheader("Machine Schedules")
#     if 'inventory' in data:
#         st.dataframe(data['inventory'][['Machine Status', 'Next Idle Date', 'Next Maintenance Date']])
#     else:
#         st.dataframe(data[['Machine Status', 'Next Idle Date', 'Next Maintenance Date']])

# # Tab 5: Leftover Components
# with tab5:
#     st.subheader("Leftover Components Analysis")
    
#     # Button to generate scenarios
#     if st.button("Generate Scenarios"):
#         # Simulate AI analysis
#         st.success("AI is analyzing current inventory and suggesting potential uses for leftover components...")
        
#         # Display mock results
#         st.markdown("### New Product Scenarios:")
#         st.markdown("1. Foldable City Bike - Utilize leftover frames and wheels.")
#         st.markdown("2. Electric Bicycle - Use leftover gears and handlebars.")
        
#         # Nearby retailers mock data
#         st.markdown("### Nearby Retailers:")
#         st.markdown("1. Retailer A - Demand for Frames.")
#         st.markdown("2. Retailer B - Demand for Wheels.")
        
#         # Add a map view simulation (mock)
#         st.markdown("### Retailer Map")
#         st.write("Map displaying retailers and their demand for components would be here.")

#     # User selects a new product scenario
#     selected_product = st.selectbox("Select a New Product Scenario:", ["Foldable City Bike", "Electric Bicycle"])
    
#     if selected_product:
#         st.markdown(f"You selected: **{selected_product}**")
#         st.markdown("Analyzing production planning...")

#         # Display production planning mock data
#         st.markdown("### Production Planning Schedule:")
#         st.write(""" 
#             - Machine 1: Active from Jan 15 to Feb 10 
#             - Machine 2: Scheduled for maintenance on Feb 20 
#             - Estimated Completion: 100 units by Mar 1 
#             - Potential Revenue: €15,000 
#         """)

#         if st.button("Confirm Production Plan"):
#             st.success("Production plan confirmed for the selected scenario!")

# # Footer
# st.write("Dashboard developed for Bicycle Manufacturing Company")

