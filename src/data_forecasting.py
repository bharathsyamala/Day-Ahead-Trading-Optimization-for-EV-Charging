from .utils import *
import pandas as pd
import numpy as np
import xgboost
from xgboost import XGBRegressor
from xgboost import plot_importance, plot_tree
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
import plotly.graph_objects as go
from sklearn.model_selection import GridSearchCV


def perform_forecasting(data, pred_no_of_days, tuning_required=False):
    data_df = data.copy()
    
    # Adding Features for forecasting
    data_df = create_features(data_df)

    # Train/Test Split
    pred_hours = pred_no_of_days*24
    total_hours = len(data_df['DA_Price'])
    no_of_training_data_points = int(total_hours * (1-pred_hours/total_hours))

    X = data_df.drop(['DA_Price', 'date'], axis=1).copy()
    y = data_df['DA_Price'].copy()

    X_train = X.iloc[:no_of_training_data_points]
    X_test = X.iloc[no_of_training_data_points:]

    y_train = y.iloc[:no_of_training_data_points]
    y_test = y.iloc[no_of_training_data_points:]

    if tuning_required:
        best_params = parameter_tuning(X_train, y_train)
        xgb_model = XGBRegressor(**best_params)
    else:
        xgb_model = XGBRegressor(
            objective='reg:squarederror', 
            learning_rate=0.1,
            n_estimators=1000,
            max_depth=7,
            subsample=0.9
        )
    
    xgb_model.fit(X_train, y_train)
    xgb_predictions = xgb_model.predict(X_test)

    print('Price Forecasting Completed!','\n')

    calculate_error_metrices(xgb_predictions, y_test)

    print('\n','Plotting Data...','\n')

    #data_df = data_df.set_index('timestamp')    

    plotting_forecasted_prices(data_df, no_of_training_data_points, xgb_predictions, y_test, pred_no_of_days)

    new_df = update_df(data_df, no_of_training_data_points, xgb_predictions)

    plot_DA_data(new_df)

    new_df.to_csv(FORECASTED_DATA_DIR/'forecasted_data.csv')

    return no_of_training_data_points, new_df


def calculate_error_metrices(xgb_predictions, y_test):

    mae = mean_absolute_error(y_test, xgb_predictions)
    rmse = root_mean_squared_error(y_test, xgb_predictions)

    smape = round(
        np.mean(
            np.abs(xgb_predictions - y_test)/
            (
                (
                    np.abs(xgb_predictions) + np.abs(y_test)
                )/2
            )
        )*100, 2
    )

    print('Error Metrices:','\n')
    print(f'MAE: {mae}')
    print(f'RMSE: {rmse}')
    print(f'sMAPE: {smape}')


def create_features(df):
    # time based features

    df['date'] = pd.to_datetime(df.index)
    df['hour'] = df['date'].dt.hour
    df['dayofweek'] = df['date'].dt.dayofweek
    df['dayofmonth'] = df['date'].dt.day
    df['dayofyear'] = df['date'].dt.dayofyear

    # adding lags
    df['lag_1h'] = df['DA_Price'].shift(1)
    df['lag_24h'] = df['DA_Price'].shift(24)
    df['lag_168h'] = df['DA_Price'].shift(168)

    # adding rolling mean
    df['rolling_mean_2h'] = df['DA_Price'].rolling(window=2).mean()
    df['rolling_mean_3h'] = df['DA_Price'].rolling(window=3).mean()
    df['rolling_mean_6h'] = df['DA_Price'].rolling(window=6).mean()

    return df


def parameter_tuning(xtrain, ytrain):
    param_grid = {
        'learning_rate': [0.01, 0.1, 0.25, 0.5, 1],
        'max_depth': [3, 5, 7],
        'subsample': [0.8, 0.9, 1.0],
        'n_estimators': [1000],
        'objective': ['reg:squarederror']
    }

    grid_search = GridSearchCV(XGBRegressor(), param_grid, cv=3)
    grid_search.fit(xtrain, ytrain)

    return grid_search.best_params_

### Plotting data

def plot_DA_data(df_fc):

    print("Visualizing Actual vs Forecasted DA Prices across actual DA Load and Generation.\n")
    
    df_full = df_fc.copy().reset_index(drop=False)

    fig = go.Figure()

    # Sort by time to avoid zig-zag areas
    df_full = df_full.sort_values("timestamp")

    # Stacked AREA (MW)
    # First trace uses 'tozeroy', others use 'tonexty' with same stackgroup
    first = True
    for col, label in [
        ('actual_load','Load Demand'),
        ('solar_generation','Solar'),
        ('wind_on_generation','Wind Onshore'),
        ('wind_off_generation','Wind Offshore'),
        ('fossil_hard_coal_generation','Coal'),
        ('fossil_gas_generation','Gas'),
    ]:
        fig.add_trace(go.Scatter(
            x=df_full['timestamp'],
            y=df_full[col],
            name=label,
            mode="lines",
            line=dict(width=0),          # no outline, pure area; increase if you want borders
            stackgroup="gen",           # same stack group for stacking
            fill="tonexty" if not first else "tozeroy",
            hoverinfo="x+y+name"
        ))
        first = False

    # Actual DA price
    fig.add_trace(go.Scatter(
        x=df_full["timestamp"],
        y=df_full["DA_Price"],
        mode="lines",
        name="Actual DA Price (EUR/MWh)",
        yaxis="y2",
        line=dict(width=3, color='black')
    ))

    # Forecasted DA price
    fig.add_trace(go.Scatter(
        x=df_full["timestamp"],
        y=df_full["forecasted_prices"],
        mode="lines",
        name="Forecasted DA Price (EUR/MWh)",
        yaxis="y2",
        line=dict(width=3, color='red')
    ))

    fig.update_layout(
        title="Generation Mix, Load, and Day-Ahead Price — All Days",
        xaxis=dict(title="Time"),

        yaxis=dict(
            title="Generation / Load (MW)",
            side="left",
            anchor="x",
            position=0
        ),

        yaxis2=dict(
            title="DA Price (EUR/MWh)",
            overlaying="y",
            side="right",
            anchor="x",
            position=1,
            showgrid=False,
        ),
        height=600,
        margin=dict(r=120),
        template="plotly_white",
        legend=dict(
            title="Legend",
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5
        )
    )

    fig.show()



def plotting_forecasted_prices(df2, no_of_training_data_points, xgb_predictions, y_test, no_of_days):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(df2.index[no_of_training_data_points:]),
        y=y_test,
        name='actual prices'
    ))

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(df2.index[no_of_training_data_points:]),
        y=xgb_predictions,
        name='predicted prices'
    ))

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Prices [Eur/MWh]',
        title_text=f'Actual vs Forecasted DA Prices for the next {no_of_days} days.'
    )

    fig.show()


def update_df(data_df, no_of_training_data_points, xgb_predictions):
    new_df = data_df.iloc[no_of_training_data_points:].copy()
    new_df['forecasted_prices'] = xgb_predictions

    return new_df