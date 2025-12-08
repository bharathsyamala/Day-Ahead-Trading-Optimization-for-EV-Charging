from .utils import *
import pandas as pd
import numpy as np


def modify_ev_data(forecasted_prices):
    df_forecasted = forecasted_prices.drop(columns=['hour', 'dayofmonth', 'dayofyear', 'lag_1h', 'lag_24h', 'lag_168h', 'rolling_mean_2h', 'rolling_mean_3h', 'rolling_mean_6h']).copy()

    #sim_start = df_forecasted["timestamp"].min()
    sim_start = df_forecasted.index.min()
    sim_end   = df_forecasted.index.max()
    #sim_end   = df_forecasted["timestamp"].max()

    price_temp = df_forecasted.copy()
    price_temp['date'] = pd.to_datetime(price_temp['date']).dt.strftime('%Y-%m-%d')
    uniq_dates = price_temp['date'].unique()
    days_df = price_temp.loc[price_temp['date'].isin(uniq_dates)]
    days_df = days_df[['date','dayofweek']].drop_duplicates()

    df_ev_data = pd.DataFrame()

    for date in days_df["date"]:
        df_ev_data = pd.concat([
            df_ev_data,
            extract_ev_data(date, days_df, sim_start, sim_end, max_stay_days=2)
        ])

    summarize_ev_data(df_ev_data)

    print('Visualization of Arrival and Departure instances of EVs.')

    plot_EV_data(df_ev_data, df_forecasted)

    return df_ev_data, df_forecasted



def extract_ev_data(date_val, days_df, sim_start, sim_end, max_stay_days=2):

    # Identify weekday from master calendar
    day = days_df.loc[days_df["date"] == date_val, "dayofweek"].values[0]

    # Load EV CSV for that weekday
    temp_df = pd.read_csv(f"{EV_DATA_DIR}/EVData_day{day}.csv")
    temp_df["day"] = day
    temp_df["date"] = pd.to_datetime(date_val)

    # Rename columns
    temp_df = temp_df.rename(columns={
        "EV ID": "ev_id",
        "Time of Arrival": "toa",
        "Time of Departure": "tod",
        "Initial SOC": "i_soc",
        "Desired SOC": "d_soc",
        "Maximum Battery Capacity": "max_battery_capacity",
        "Duration of Stay": "dos",
    })

    # ---------------------------------------------------
    # 1. Convert ToA, ToD, DoS
    # ---------------------------------------------------
    base_date = pd.to_datetime(date_val)

    temp_df["toa"] = base_date + pd.to_timedelta(temp_df["toa"] + ":00")
    temp_df["dos"] = pd.to_timedelta(temp_df["dos"] + ":00")
    temp_df["tod"] = temp_df["toa"] + temp_df["dos"]

    # ---------------------------------------------------
    # 2. Clamp ToD to max_stay_days && simulation horizon
    # ---------------------------------------------------
    max_stay = pd.Timedelta(days=max_stay_days)

    # Enforce max stay rule (48 hours max)
    temp_df["tod"] = temp_df.apply(
        lambda row: min(row["tod"], row["toa"] + max_stay),
        axis=1
    )

    # Clamp toa/tod to simulation window
    temp_df["toa"] = temp_df["toa"].clip(lower=sim_start, upper=sim_end)
    temp_df["tod"] = temp_df["tod"].clip(lower=sim_start, upper=sim_end)

    # ---------------------------------------------------
    # 3. Hour-floor versions (for time_to_idx)
    # ---------------------------------------------------
    #temp_df["toa"] = temp_df["toa"].dt.floor("h")
    #temp_df["tod"] = temp_df["tod"].dt.floor("h")

    return temp_df


def plot_EV_data(df_ev, df_fc):
    df_ev_all = df_ev.copy()
    df_ev_all["arrival_hour"] = df_ev_all["toa"].dt.floor("h")
    df_ev_all["departure_hour"] = df_ev_all["tod"].dt.floor("h")

    arrivals = df_ev_all.groupby("arrival_hour").size().rename("arrivals")
    departures = df_ev_all.groupby("departure_hour").size().rename("departures")

    df_fc = df_fc.reset_index(drop=False)
    df_full = df_fc[["timestamp"]].copy()
    df_full["timestamp"] = pd.to_datetime(df_full["timestamp"])


    df_full = df_full.merge(arrivals.rename("arrivals"), left_on="timestamp", right_index=True, how="left")
    df_full = df_full.merge(departures.rename("departures"), left_on="timestamp", right_index=True, how="left")
    df_full = df_full.fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_full['timestamp'], y=df_full['arrivals'], name="Arrivals"))
    fig.add_trace(go.Bar(x=df_full['timestamp'], y=df_full['departures'], name="Departures"))

    fig.update_layout(
        title="Arrivals & Departures Over Entire Optimization Horizon",
        barmode="stack",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Count"),
        template="plotly_white"
    )
    fig.show()


def summarize_ev_data(df_ev):

    if df_ev.empty:
        print("EV summary: No EV records found.")
        return

    df_tmp = df_ev.copy()

    # Ensure timestamps are parsed correctly
    df_tmp["toa"] = pd.to_datetime(df_tmp["toa"])
    df_tmp["tod"] = pd.to_datetime(df_tmp["tod"])
    df_tmp["date"] = pd.to_datetime(df_tmp["date"]).dt.date

    # Duration in hours
    df_tmp["duration_hours"] = (df_tmp["tod"] - df_tmp["toa"]).dt.total_seconds() / 3600

    # EV count per day
    evs_per_day = df_tmp.groupby("date")["ev_id"].nunique()

    # Compute means
    avg_duration = df_tmp["duration_hours"].mean()
    avg_capacity = df_tmp["max_battery_capacity"].mean()

    # Print clean summary
    print("\n=== EV DATA SUMMARY ===")

    print("EVs per day:")
    for day, count in evs_per_day.items():
        print(f"  {day}: {count}")

    print(f"Average stay duration: {avg_duration:.2f} hours")
    print(f"Average battery capacity: {avg_capacity:.2f} kWh")
    print("====================================\n")
