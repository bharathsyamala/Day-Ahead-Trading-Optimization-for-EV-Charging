# Day Ahead Trading Optimization for EV Charging

## Objective and Purpose  
This project provides a full stack forecasting and optimization workflow for scheduling EV charging based on day ahead electricity market signals. The goal is to minimize charging cost while encouraging green energy consumption by aligning charging with periods of high renewable generation availability. The system is designed for the Dutch electricity market using ENTSOe data and supports large scale EV fleet modeling.

## High Level Description  
The project uses four years of historical Dutch day ahead price and generation data from ENTSOe [1]. These data are cleaned and processed into a machine learning ready dataset that is used to train an XGBoost based day ahead price forecasting model. EV arrival and departure sessions are generated using statistical patterns drawn from published literature [2]. The optimization model schedules charging for 300 to 500 EVs per day using a mixed integer linear programming formulation implemented in Pyomo and solved using HiGHS. The model balances three objectives: meeting user SOC requirements, reducing charging costs, and taking advantage of renewable generation availability [3]. The final outputs include optimized charging schedules, SOC trajectories, tardiness metrics, and visual analysis notebooks.

## System Flow Diagram  

<img width="4564" height="900" alt="image" src="https://github.com/user-attachments/assets/8cbd010d-0eef-4840-a801-93e2c6935b8d" />

## Project Architecture  

Day-Ahead-Trading-Optimization-for-EV-Charging

│

├── main.py End to end pipeline execution

├── environment.yml Reproducible Conda environment

│

├── src/

│ ├── data_loading.py    # Load ENTSOe price and generation data

│ ├── data_cleaning.py    # Clean and merge processed dataset

│ ├── data_forecasting.py    # XGBoost day ahead price forecasting

│ ├── generate_ev_data.py    # Generate EV arrival and departure sessions

│ ├── optimization_model.py    # Pyomo MILP model and HiGHS solution

│ └── utils.py    # General utility functions

│

├── data/

│ ├── raw/    # Raw ENTSOe inputs

│ ├── processed/    # Cleaned merged dataset

│ ├── forecasted/    # Forecasted Price dataset

│ ├── ev/    # EV dataset

│ └── optimized/    # Optimization results

│

├── analysis_notebooks/    # Plotly based EDA and validation notebooks

│ ├── exploratory_analysis.ipynb    # Post-cleaning, pre-forecasting data analysis notebook

│ └── optimization_visualization.ipynb    # Optimization results visualization

│

└── README.md

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
