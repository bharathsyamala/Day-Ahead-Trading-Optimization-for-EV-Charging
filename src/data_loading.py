from .utils import *
from .data_cleaning import *
import pandas as pd
import glob

def load_raw_data():
    # Loading Actual and Forecasted Energy Demand

    all_load_files = glob.glob(f'{RAW_DATA_DIR}/GUI_TOTAL_LOAD_DAYAHEAD_20*')
    df_load_data = pd.concat([transform_load_data(f) for f in all_load_files]).sort_index()

    # Loading Renewable Generation Data

    all_rwe_files = glob.glob(f'{RAW_DATA_DIR}/AGGREGATED_GENERATION_PER_TYPE_GENERATION_20*')
    df_rwe_generation_data = pd.concat([transform_renewables_load_data(f) for f in all_rwe_files]).sort_index()
    
    # Loading Price Data from Multiple CSVs

    all_price_files = glob.glob(f'{RAW_DATA_DIR}/GUI_ENERGY_PRICES_20*')
    df_price_data = pd.concat([transform_price_data(f) for f in all_price_files]).sort_index()
    

    df_load_data = df_load_data.loc[df_price_data.index.min():df_price_data.index.max()].sort_index()

    df_rwe_generation_data = df_rwe_generation_data.loc[df_price_data.index.min():df_price_data.index.max()].sort_index()

    df_final_data = df_price_data.join(df_load_data, how='inner')
    df_final_data = df_final_data.join(df_rwe_generation_data, how='inner')
    
    return df_final_data



