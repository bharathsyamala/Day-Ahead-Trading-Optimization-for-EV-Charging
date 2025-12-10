# Day Ahead Trading Optimization for EV Charging

## Objective and Purpose  
This project provides a full stack forecasting and optimization workflow for scheduling EV charging based on day ahead electricity market signals. The goal is to minimize charging cost while encouraging green energy consumption by aligning charging with periods of high renewable generation availability. The system is designed for the Dutch electricity market using ENTSOe data and supports large scale EV fleet modeling.

## High Level Description  
The project uses four years of historical Dutch day ahead price and generation data from ENTSOe [1]. These data are cleaned and processed into a machine learning ready dataset that is used to train an XGBoost based day ahead price forecasting model. EV arrival and departure sessions are generated using statistical patterns drawn from published literature [2]. The optimization model schedules charging for 300 to 500 EVs per day using a mixed integer linear programming formulation implemented in Pyomo and solved using HiGHS. The model balances three objectives: meeting user SOC requirements, reducing charging costs, and taking advantage of renewable generation availability [3]. The final outputs include optimized charging schedules, SOC trajectories, tardiness metrics, and visual analysis notebooks.

## System Flow Diagram  

<img width="4564" height="900" alt="image" src="https://github.com/user-attachments/assets/8cbd010d-0eef-4840-a801-93e2c6935b8d" />


## Optimization Model Formulation

### Sets

$I$: Electric vehicles

$T = {0,\ldots,T_{max}}$: Time steps

$T_i \subseteq T$: Time steps when EV $i$ can charge

### Parameters

$p_t$: Electricity price at time $t$

$R_t$: Renewable energy fraction at time $t$

$MP_i$: Max charging power for EV $i$

$MC_i$: Battery capacity for EV $i$

$SOC_{i,0}$: Initial state of charge

$SOC_{i,des}$: Desired state of charge

$t_{i,a}$: Arrival time

$t_{i,d}$: Departure time

$avail_{i,t} \in {0,1}$: Availability

$\eta$: Charging efficiency

$\lambda_{carb}$: Carbon penalty coefficient

$W$: Slack penalty weight

### Decision Variables

$$PD_{i,t} \ge 0$$: Charging power

$$SOC_{i,t} \ge 0$$: State of charge

$$slack_i \ge 0$$: Slack for unmet SOC

### Objective

$$\min\ \displaystyle \sum_{t\in T} \left( p_t + \lambda_{carb}(1 - R_t) \right)\left(\frac{1}{1000}\sum_{i:\ t\in T_i} PD_{i,t}\right) + W\sum_{i\in I} slack_i$$

### Constraints

#### Power limit
$$0 \le PD_{i,t} \le MP_i \cdot avail_{i,t} \quad \forall i,\ t \in T_i$$

#### Arrival SOC
$$SOC_{i, t_{i,a}} = SOC_{i,0} + \eta, PD_{i,t_{i,a}}$$

#### SOC dynamics
$$SOC_{i,t} = SOC_{i,t-1} + \eta, PD_{i,t} \quad \forall i,\ t\in T_i,\ t > t_{i,a}$$

#### Capacity constraint
$$SOC_{i,t} \le MC_i \quad \forall i,\ t\in T_i$$

#### Departure SOC requirement
$$SOC_{i,t_{i,d}} + slack_i \ge SOC_{i,des} \quad \forall i$$

#### Nonnegativity
$$PD_{i,t} \ge 0,\quad SOC_{i,t} \ge 0,\quad slack_i \ge 0$$


## Project Architecture  

```
Day-Ahead-Trading-Optimization-for-EV-Charging
│
├── main.py # End-to-end pipeline execution
├── environment.yml # Reproducible Conda environment
│
├── src/
│ ├── data_loading.py # Load ENTSOe price & generation data
│ ├── data_cleaning.py # Clean & merge datasets
│ ├── data_forecasting.py # XGBoost day-ahead price forecasting
│ ├── generate_ev_data.py # Generate EV sessions
│ ├── optimization_model.py # Pyomo MILP model (HiGHS solver)
│ └── utils.py # Utility functions
│
├── data/
│ ├── raw/ # ENTSOe inputs
│ ├── processed/ # Cleaned dataset
│ ├── forecasted/ # Forecasted prices
│ ├── ev/ # EV session data
│ └── optimized/ # Optimization results
│
├── analysis_notebooks/
│ ├── exploratory_analysis.ipynb # Pre-forecasting EDA
│ └── optimization_visualization.ipynb # Results visualization
│
└── README.md

```

## Input Data Requirements  

### ENTSOe Data Inputs  
Required fields include  
- timestamp  
- day ahead price  
- solar generation  
- wind generation: onshore and offshore  
- fossil generation: hard coal and gas  
- load data: actual and forecasted
- date metadata

### EV Session Data  
EV session data provided in this repository is generated using statistical patterns from academic literature (see references). Each EV entry includes  
- arrival time  
- departure time  
- initial SOC  
- desired SOC  
- maximum battery capacity  
- unique EV identifier  

## Running the Pipeline  

### 1. Create and activate the environment  

conda env create -f environment.yml
conda activate ev_opti_modelling

### 2. Run the full workflow  

python main.py

This runs the complete pipeline:  
1. Load ENTSOe market and generation data  
2. Clean and merge datasets  
3. Train and apply XGBoost day ahead forecasting  
4. Generate EV sessions for all modeled days  
5. Solve the MILP optimization using Pyomo and HiGHS  
6. Export all outputs to `data/optimized`  
7. Print key results to the console  

### 3. Visualize results  
Use notebooks in `analysis_notebooks` to explore  
- EV charging and SOC profiles  
- fleet load curves  
- prices versus charging activity  
- renewable versus non renewable consumption  
- EV arrival and departure patterns  

## Outputs  

The following files are generated in `data/optimized`  
- `pd_solution.csv` charging power per EV per hour  
- `soc_solution.csv` SOC per EV per hour  
- `ev_data.csv` all EV session inputs aligned with the optimization horizon  
- `forecast_generation_and_prices.csv` price forecast and full generation mix  

Notebook visualizations illustrate charging behavior, renewable alignment, and model performance.

## Intended Audience  
This project is intended for  
- energy system researchers  
- EV integration and smart charging analysts  
- grid flexibility and market modeling professionals  
- hiring managers evaluating forecasting and optimization skills  
- students and engineers studying EV energy systems  

## References  

[1] ENTSOe Transparency Platform - https://transparency.entsoe.eu/ 

[2] Helmus, Jurjen R., Michael H. Lees, and Robert van den Hoed.  
A data driven typology of electric vehicle user types and charging sessions.  
Transportation Research Part C: Emerging Technologies 115 (2020): 102637.

[3] Vagropoulos, Stylianos I., and Anastasios G. Bakirtzis. 
Optimal bidding strategy for electric vehicle aggregators in electricity markets. 
IEEE Transactions on power systems 28.4 (2013): 4031-4041.
