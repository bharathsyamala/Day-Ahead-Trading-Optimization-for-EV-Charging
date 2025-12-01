from src.data_loading import *
from src.data_cleaning import *

### Loading Raw Data into Variables ###

print('Step 1 - Loading, Cleaning, and Merging Raw Data into a Processed Data File')

processed_data = load_raw_data()

print('Step 1 Finished! Raw Data Loaded!')


### Performing Data Quality Checks, Cleaning, and Combining them into a single Processed File ###


print('Step 2 - Exporting Processed Data into a CSV File')

#processed_data = process_raw_data(raw_load_data, raw_price_data)
#print(processed_data)

print(export_processed_data(processed_data))
print(processed_data)

print('Step 2 Finished! Raw Data Cleaned and Processed Data!')



