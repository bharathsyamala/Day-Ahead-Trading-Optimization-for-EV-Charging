from .utils import *
import pandas as pd
import plotly.graph_objects as go

### Function for Cleaning Raw Load Data, mainly the timestamp ###

def transform_load_data(name_of_file):
    temp_df = pd.read_csv(name_of_file)
    if 'MTU (UTC)' in temp_df.columns.tolist():
        temp_df = temp_df.rename(
            columns={
                'Actual Total Load (MW)': 'DA_actual_load', 
                'Day-ahead Total Load Forecast (MW)': 'DA_forecast_load', 
                'MTU (UTC)': 'timestamp',
            }
    )
    else:
        temp_df = temp_df.rename(
            columns={
                'Actual Total Load (MW)': 'DA_actual_load', 
                'Day-ahead Total Load Forecast (MW)': 'DA_forecast_load', 
                'MTU (CET/CEST)': 'timestamp',
            }
        )
    temp_df = temp_df.drop(columns=({'Area'}))
    
    temp_df['timestamp'] = temp_df['timestamp'].replace(r'\s*\(CET\)|\s*\(CEST\)', '', regex=True)
    temp_df['timestamp'] = temp_df['timestamp'].replace(r':.*','',regex=True)
    temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], dayfirst=True).dt.strftime('%Y-%m-%d %H')

    df_temp = pd.DataFrame(temp_df.groupby('timestamp').agg(
        actual_load=('DA_actual_load','sum'),
        forecast_load=('DA_forecast_load','sum'),
    ))

    return df_temp


### Function for Renewable Energy Generation Transformation ###

def transform_renewables_load_data(name_of_file):
    df_rwe_data = pd.read_csv(name_of_file)

    temp_df = df_rwe_data.loc[(
        df_rwe_data['Production Type']=='Solar'
    )]
    if 'MTU (UTC)' in temp_df.columns.tolist():
        temp_df = temp_df.rename(columns={
            'MTU (UTC)': 'timestamp',
            'Generation (MW)': 'solar_generation'
        })
    else:
        temp_df = temp_df.rename(columns={
            'MTU (CET/CEST)': 'timestamp',
            'Generation (MW)': 'solar_generation'
        })
    temp_df = temp_df.drop(columns={'Area','Production Type'})

    temp_df['solar_generation'] = pd.to_numeric(temp_df['solar_generation'])

    temp_df['wind_on_generation'] = list(df_rwe_data['Generation (MW)'].loc[(
        df_rwe_data['Production Type']=='Wind Onshore'
    )])

    temp_df['wind_off_generation'] = list(df_rwe_data['Generation (MW)'].loc[(
        df_rwe_data['Production Type']=='Wind Offshore'
    )])

    temp_df['fossil_hard_coal_generation'] = list(pd.to_numeric(df_rwe_data['Generation (MW)'].loc[(
        df_rwe_data['Production Type']=='Fossil Hard coal'
    )]))

    temp_df['fossil_gas_generation'] = list(pd.to_numeric(df_rwe_data['Generation (MW)'].loc[(
        df_rwe_data['Production Type']=='Fossil Gas'
    )]))

    temp_df.reset_index()

    temp_df['timestamp'] = temp_df['timestamp'].replace(r'\s*\(CET\)|\s*\(CEST\)', '', regex=True)
    temp_df['timestamp'] = temp_df['timestamp'].replace(r':.*','',regex=True)
    temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], dayfirst=True).dt.strftime('%Y-%m-%d %H')

    df_temp = pd.DataFrame(temp_df.groupby('timestamp').agg(
        solar_generation=('solar_generation','sum'),
        wind_on_generation=('wind_on_generation','sum'),
        wind_off_generation=('wind_off_generation','sum'),
        fossil_hard_coal_generation=('fossil_hard_coal_generation','sum'),
        fossil_gas_generation=('fossil_gas_generation','sum'),
    ))

    return df_temp


### Function for Cleaning Raw Price Data, mainly the timestamp ###

def transform_price_data(name_of_file):
    temp_df = pd.read_csv(name_of_file)
    if 'MTU (UTC)' in temp_df.columns.tolist():
        temp_df = temp_df.rename(
            columns={
                'MTU (UTC)': 'timestamp', 
                'Day-ahead Price (EUR/MWh)':'DA_Price'
            }
        )
        temp_df = temp_df.drop(columns={'Intraday Period (UTC)', 'Intraday Price (EUR/MWh)', 'Area', 'Sequence'})
    else:
        temp_df = temp_df.rename(
            columns={
                'MTU (CET/CEST)': 'timestamp', 
                'Day-ahead Price (EUR/MWh)':'DA_Price'
            }
        )
        temp_df = temp_df.drop(columns={'Intraday Period (CET/CEST)', 'Intraday Price (EUR/MWh)', 'Area', 'Sequence'})
    temp_df['timestamp'] = temp_df['timestamp'].replace(r'\s*\(CET\)|\s*\(CEST\)', '', regex=True)
    temp_df['timestamp'] = temp_df['timestamp'].replace(r' -.*', '', regex=True)
    temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'], dayfirst=True).dt.strftime('%Y-%m-%d %H')

    

    temp_df = temp_df.set_index('timestamp')

    return temp_df


### Function for processing input data - merging load and price data, performing data quality checks, and exporting it into the processed folder ###

def export_processed_data(df_final_data):
    return df_final_data.to_csv(PROCESSED_DATA_DIR/'processed_data.csv')



