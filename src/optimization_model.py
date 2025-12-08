from .utils import *
import pandas as pd
import numpy as np
from pyomo.environ import *
import plotly.graph_objects as go
from highspy import Highs


def launch_optimization(df_ev_data, df_forecasted):
    #def ready_the_data(df_ev_data, df_forecasted):
    df_ev = df_ev_data.copy()
    df_fc = df_forecasted.copy().reset_index(drop=False)
    #df_fc = df_fc.reset_index(drop=False)

    df_ev['toa'] = pd.to_datetime(df_ev['toa'])
    df_ev['tod'] = pd.to_datetime(df_ev['tod'])

    start_ts = pd.Timestamp("2024-12-24 00:00")
    end_ts   = pd.Timestamp("2024-12-31 00:00")

    df_ev["toa_hr"] = df_ev["toa"].dt.floor("h")
    df_ev["tod_hr"] = df_ev["tod"].dt.floor("h")

    df_ev = df_ev[
        (df_ev["toa_hr"] >= start_ts) &
        (df_ev["tod_hr"] <  end_ts)
    ].copy()

    df_fc['timestamp'] = pd.to_datetime(df_fc['timestamp'])

    df_fc = df_fc[(df_fc["timestamp"] >= start_ts) &
              (df_fc["timestamp"] <  end_ts)].copy()

    df_fc = df_fc.sort_values('timestamp').reset_index(drop=True)
    T_max = len(df_fc) - 1
    #T_max = 23

    time_to_idx = {ts: idx for idx, ts in enumerate(df_fc['timestamp'])}

    price_dict = {t: df_fc.loc[t, "forecasted_prices"] for t in range(T_max+1)}

    df_fc['total_gen'] = (
        df_fc['solar_generation'] +
        df_fc['wind_on_generation'] +
        df_fc['wind_off_generation'] +
        df_fc['fossil_hard_coal_generation'] +
        df_fc['fossil_gas_generation']
    )

    df_fc['R'] = (
        df_fc['solar_generation'] +
        df_fc['wind_on_generation'] +
        df_fc['wind_off_generation']
    ) / df_fc['total_gen'].replace(0, np.nan)

    R_dict = {
        t: float(df_fc.loc[t, 'R']) for t in range(T_max+1)
    }

    df_ev['unique_ev'] = df_ev['ev_id'] + '_' + df_ev['date'].astype(str)

    EV_list = df_ev['unique_ev'].tolist()


    #SOC_init_energy = {}
    #SOC_desired_energy = {}
    arrival = {}
    departure = {}
    SOC_init = {}
    SOC_desired = {}
    MC = {}
    MP = {}
    availability = {}
    T_ev_pairs = []


    for _, row in df_ev.iterrows():
        ev = row['unique_ev']
        toa = row["toa"]
        tod = row["tod"]
        cap = float(row['max_battery_capacity'])


        #t_a = time_to_idx.get(pd.Timestamp(toa.))

        t_a = time_to_idx.get(pd.Timestamp(toa.replace(minute=0, second=0)))
        t_d = time_to_idx.get(pd.Timestamp(tod.replace(minute=0, second=0)))
        #T_ev_init[ev] = list(range(int(t_a), int(t_d)+1))

        for t in range(int(t_a), int(t_d)+1):
            T_ev_pairs.append((ev, t))

        #print(ev, t_a, t_d)

        frac_a = (60 - toa.minute)/60 if toa.minute != 0 else 1.0
        frac_d = tod.minute/60 if tod.minute != 0 else 0.0


        for t in range(T_max + 1):
            if t < t_a:
                availability[(ev, t)] = 0
            elif t == t_a == t_d:
                availability[(ev, t)] = min(frac_a, frac_d)
            elif t == t_a:
                availability[(ev, t)] = frac_a
            elif t_a < t < t_d:
                availability[(ev, t)] = 1
            elif t == t_d:
                availability[(ev, t)] = frac_d
            else:
                availability[(ev, t)] = 0

        #print('-----------------------------------------')
        

        arrival[ev] = t_a
        departure[ev] = t_d
        SOC_init[ev] = row['i_soc'] / 100.0 * cap
        SOC_desired[ev] = row['d_soc'] / 100.0 * cap
        MC[ev] = float(row['max_battery_capacity'])
        MP[ev] = 11.0


    ## Model

    model = ConcreteModel()

    model.EV = Set(initialize=EV_list)
    model.T = RangeSet(0, T_max)
    model.T_EV = Set(dimen=2, initialize=T_ev_pairs)

    # parameters
    model.price = Param(model.T, initialize=price_dict, within=Reals)
    model.R = Param(model.T, initialize=R_dict, within=NonNegativeReals)

    # EV parameters
    model.MP = Param(model.EV, initialize=MP)
    model.MC = Param(model.EV, initialize=MC)

    model.SOC_init = Param(model.EV, initialize=SOC_init)
    model.SOC_desired = Param(model.EV, initialize=SOC_desired)

    model.arrival = Param(model.EV, initialize=arrival)
    model.departure = Param(model.EV, initialize=departure)

    model.avail = Param(model.EV, model.T, initialize=availability)

    model.eta = Param(initialize=0.85)

    # Carbon penalty coefficient
    model.lambda_carbon = Param(initialize=50.0)  

    # Decision variables
    model.PD = Var(model.T_EV, within=NonNegativeReals)
    model.SOC = Var(model.T_EV, within=NonNegativeReals)
    model.slack = Var(model.EV, within=NonNegativeReals)


    ## Objective

    model.Obj = Objective(rule=obj_rule, sense=minimize)


    ## Constraints
    # power draw
    
    model.PowerLimit = Constraint(model.T_EV, rule=power_limit_rule)

    # SOC logic
    
    model.SOCDynamics = Constraint(model.T_EV, rule=soc_rule)

    # SOC battery capacity limits

    #model.CapLimit = Constraint(model.EV, model.T, rule=cap_rule)
    model.CapLimit = Constraint(
        model.T_EV,
        rule=lambda m, ev, t: m.SOC[ev, t] <= m.MC[ev]
    )

    # Desired SOC logic

    model.DepSOC = Constraint(model.EV, rule=dep_rule)

    model.write("model.lp", io_options={"symbolic_solver_labels": True})

    #solver = SolverFactory('highs')
    solver = SolverFactory("highs")
    solver.options["presolve"] = "off"
    solver.options["simplex_strategy"] = 1
    solver.options["primal_feasibility_tolerance"] = 0.0001


    #print("Solver type:", type(solver))

    print('solver defined \n')

    print('starting solver \n')

    results = solver.solve(model, tee=False)
    # Results

    PD_solution = {(ev, t): value(model.PD[ev, t]) 
               for (ev, t) in model.T_EV}

    SOC_solution = {(ev, t): value(model.SOC[ev, t]) 
                    for (ev, t) in model.T_EV}
    
    new_cost = compute_cost_new(df_fc, PD_solution, model, time_to_idx)
    #print("NEW MODEL monetary charging cost:", new_cost)

    export_visualization_data(df_fc, df_ev, model, PD_solution, SOC_solution)
    #export_visualization_data(df_fc, model, PD_solution, SOC_solution)

    tardy = calculate_tardiness(model)

    #if tardy==None:
    #    tardy = 0

    summary = {
        "total_charging_cost": new_cost,
        "num_ev_tardy": len(tardy),
        "tardiness_details": tardy,
    }

    return summary


    
## Objective
def obj_rule(m):
    SOC_penalty_weight = 100

    return sum(
        (m.price[t] + m.lambda_carbon * (1 - m.R[t])) *
        (sum(m.PD[ev, t] for (ev, tt) in m.T_EV if tt == t) / 1000)
        for t in m.T
    ) + SOC_penalty_weight * sum(m.slack[ev] for ev in m.EV)


## Constraints

# power draw
def power_limit_rule(m, ev, t):
    return m.PD[ev, t] <= m.MP[ev] * m.avail[ev, t]

# SOC logic
def soc_rule(m, ev, t):
    t_a = m.arrival[ev]
    if t == t_a:
        return m.SOC[ev, t] == m.SOC_init[ev] + m.eta * m.PD[ev, t]
    else:
        return m.SOC[ev, t] == m.SOC[ev, t-1] + m.eta * m.PD[ev, t]



# Desired SOC logic

def dep_rule(m, ev):
    t_d = m.departure[ev]
    return m.SOC[ev, t_d] + m.slack[ev] >= m.SOC_desired[ev]


# Calculating effective aggregated charging cost
def compute_cost_new(df_fc, PD_solution, model, time_to_idx):
    total_cost = 0.0
    for idx, row in df_fc.iterrows():
        t = time_to_idx[row['timestamp']]
        price = model.price[t]
        
        total_pd = sum(PD_solution.get((ev, t), 0.0) for ev in model.EV)
        total_cost += (total_pd / 1000) * price
        
    return total_cost


def calculate_tardiness(model):
    tardy = []
    for ev in model.EV:
        t_d = int(model.departure[ev])
        soc_dep = value(model.SOC[ev, t_d])
        desired = value(model.SOC_desired[ev])
        shortfall = max(0, desired - soc_dep)
        if shortfall > 1e-3:
            tardy.append((ev, shortfall))

    return tardy


def export_visualization_data(df_fc, df_ev, model, PD_solution, SOC_solution):

    


    df_pd = (
        pd.DataFrame([(ev, t, PD_solution.get((ev, t), 0.0))
                      for ev in model.EV for t in model.T],
                     columns=["ev", "t", "PD_kW"])
    )
    df_pd.to_csv(f"{OPTIMIZED_DATA_DIR}/pd_solution.csv", index=False)


    df_soc = (
        pd.DataFrame([(ev, t, SOC_solution.get((ev, t), 0.0))
                      for ev in model.EV for t in model.T],
                     columns=["ev", "t", "SOC_kWh"])
    )
    df_soc.to_csv(f"{OPTIMIZED_DATA_DIR}/soc_solution.csv", index=False)


    df_fc_out = df_fc.copy()
    df_fc_out.to_csv(f"{OPTIMIZED_DATA_DIR}/forecast_generation_and_prices.csv", index=False)


    df_ev_out = df_ev.copy()
    df_ev_out.to_csv(f"{OPTIMIZED_DATA_DIR}/ev_data.csv", index=False)

    print("Results data export complete.")


