# batch22-sap 2!IFE
# 🚲 AI-Powered Bicycle Production Optimization Dashboard

## Overview
This project was developed as part of the **DPS x SAP Innovation Challenge (2024)**.  
The goal: **help bicycle manufacturers optimize the use of leftover components** by applying AI-driven analysis and scenario planning.  

The dashboard enables planners to:  
- Upload enhanced production and sales data (CSV).  
- Analyze **sales, inventory, and leftover components**.  
- Run **scenario-based simulations** to decide which bicycle types (e.g., Mountain, City, BMX) can be built from existing stock.  
- Forecast potential revenues and inventory reduction strategies.

## 🔑 Key Features

- **MILP Optimization** with Gurobi:
  - Maximize profit
  - Minimize unused inventory
  - Minimize production time
  - Control premium vs. non-premium mix
- **Crossover Variants**: Introduces hybrid/gravel bikes using shared components across different types.
- **Sales Probabilities**:
  - Weighted average selling price (WASP)
  - Fixed probability distributions for full-price and discount tiers
  - Sensitivity analysis with varying standard deviations
- **Weight Experiments**: Compare different objective weight configurations.
- **Extensible with Neural Networks**:
  - (Planned) predictive sales modeling with historical data
  - Integrating ML forecasts into optimization loop


---

## ⚙️ Installation & Setup

### 1. Clone Repo
```bash
git clone https://github.com/yourusername/bike-optimization.git
cd bike-optimization

