#%%

from src.data_loading import *
from src.data_cleaning import *
from src.data_forecasting import *
from src.generate_ev_data import *
from src.optimization_model import *
from time import sleep
import warnings
warnings.filterwarnings("ignore")

### Loading Raw Data into Variables ###

print('Step 1 - Loading, Cleaning, and Merging Raw Data into a Processed Data File', '\n')

processed_data = load_raw_data()

sleep(5)

print('Step 1 Finished! Raw Data Loaded!', '\n')


print('--------------------------------------------------', '\n')

### Performing Data Quality Checks, Cleaning, and Combining them into a single Processed File ###

#%%
print('Step 2 - Exporting Processed Data into a CSV File', '\n')

#processed_data = process_raw_data(raw_load_data, raw_price_data)
#print(processed_data)

print(export_processed_data(processed_data))
print(processed_data.head())

sleep(5)

print('Step 2 Finished! Raw Data Cleaned and Processed Data!', '\n')

print('--------------------------------------------------', '\n')


### Performing Day Ahead Price Forecasting ###

from src.data_forecasting import *

no_of_days_to_forecast = 9

print(f'Step 3 - Day Ahead Price Forecasting for {no_of_days_to_forecast} days!', '\n')

# Currently tuning parameters are already set based on some pretesting, if you'd like to play around with the no of days and get optimized forecasting results, set the tuning_required parameter to True.

split_point, df_forecasted = perform_forecasting(processed_data, no_of_days_to_forecast, tuning_required=False)

sleep(2)

print('Step 3 Finished! Day Ahead Price Forecasting Completed!', '\n')

print('--------------------------------------------------', '\n')


### Generating EV data for a week ###

print('Step 4 - Fetching EV data', '\n')

df_ev_data, df_forecasted = modify_ev_data(df_forecasted)

sleep(2)

print('Step 4 Finished! EV Data Fetched!', '\n')

print('--------------------------------------------------', '\n')


### Running the Optimization Model for a week ###

print('Step 5 - Optimization', '\n')

print('Forecasting Horizon - 23rd December 2024 -> 31st December 2024 | 9 days. \n')
print('Optimization Horizon - 24th December 2024 -> 30th December 2024 | 1 week. \n')
print('Reason: To take into account the initial EV data warmup and avoid pile up of EVs that have not reached their departure times by the end of optimization horizon (Observe the number of departures on 31st December). \n')

#sleep(1)

print('Launching Optimization Model!!', '\n')

#df_opti_data = launch_optimization(df_ev_data, df_forecasted)

#sleep(1)

summary = launch_optimization(df_ev_data, df_forecasted)

print("\n=== Optimization Summary ===")
print("Total Charging Cost:", summary["total_charging_cost"])
print("EVs not fully charged:", summary["num_ev_tardy"])


print('Step 5 Finished! Day Ahead Bids Optimized!', '\n')

print('--------------------------------------------------', '\n')



