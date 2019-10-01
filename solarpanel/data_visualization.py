import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# one test demo for playing data on dash

def runcalcs(df, InstalledPanelA, TariffFeedIn, TariffOffPeak, TariffShoulder, TariffPeak):

    df_tariffs = pd.Series([TariffOffPeak, TariffShoulder, TariffPeak], index=[0, 1, 2]) # grid tariffs in c/kWh: 0 = offpeak, 1 = shoulder, 2 = peak

    df["Generation(kW)"] = df[
                               "Generation(W/m2)"] * InstalledPanelA / 1000  # calculate generation from installed panels (hypothetical m2)
    df["SolarConsumed(kW)"] = df[["House(kW)", "Generation(kW)"]].min(
        axis=1)  # based on what the house consumed, calculate how much solar is consumed
    df["SolarExported(kW)"] = df["Generation(kW)"] - df[
        "House(kW)"]  # if there is solar exceeding what the house needs, export that to the grid
    df["SolarExported(kW)"] = df["SolarExported(kW)"].clip(lower=0)
    df["GridConsumed(kW)"] = df["House(kW)"] - df[
        "Generation(kW)"]  # if not enough solar is generated, will need electricity from the grid
    df["GridConsumed(kW)"] = df["GridConsumed(kW)"].clip(lower=0)
    Interval = pd.Timedelta(df["Timestamp"][1] - df["Timestamp"][0]).seconds / 60
    df["Weekday"] = df["Timestamp"].dt.dayofweek  # Monday = 0, Sunday = 6
    df["Month"] = df["Timestamp"].dt.month
    df["Hour"] = df["Timestamp"].dt.hour

    df_days = pd.Series([0, 0, 0, 0, 0, 1, 1], index=[0, 1, 2, 3, 4, 5, 6])  # 0 = weekday, 1 = weekend
    df["DayType"] = df["Weekday"].map(df_days)

    # this sets up the timings for peak/offpeak tariffs from the grid. We could use these as inputs on the dash but that might be too complicated
    # 0 = offpeak, 1 = shoulder, 2 = peak
    conditions = [
        (df["Hour"] < 7) | (df["Hour"] >= 21),  # before 7am or after 9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 7) & (df["Hour"] < 15),  # weekdays from 7am-3pm
        (df["Weekday"] == 1) & (df["Hour"] >= 7) & (df["Hour"] < 21),  # weekends from 7am-9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 15) & (df["Hour"] < 21)]  # weekdays from 3pm-9pm
    choices = [0, 1, 1, 2]

    df["TariffType"] = np.select(conditions, choices)
    df["Tariff"] = df["TariffType"].map(df_tariffs)  # map actual tariffs in c/kWh onto the intervals

    df["RevenueFeedIn"] = df["SolarExported(kW)"] / (
                60 / Interval) * TariffFeedIn / 100  # how much money is made from exporting solar
    df["SavingsSolar"] = df["SolarConsumed(kW)"] / (60 / Interval) * df[
        "Tariff"] / 100  # how much money is saved from using solar instead of grid
    df["BillReduction"] = df["RevenueFeedIn"] + df["SavingsSolar"]  # total reduction in electricity bill
    return df

def dash_test1(app, sensor_df):

    def_InstalledPanelCost = 1000 # cost of panels, in $/m2
#    payback = def_InstalledPanelA*def_InstalledPanelCost/sum(df["BillReduction"])

    app.layout = html.Div(children=[
        html.Label('Monthly savings'),
        dcc.Graph(id='graph-with-input'),

        html.Label('Area of panels to install (m2):'),
        html.Div(dcc.Slider(id='input-area', min=1, max=20, value=5, marks={i: '{} m2'.format(i) for i in range(20)}), # default is 5m2
                 style={'height': '50px', 'width': '100%', 'display': 'inline-block'}
                 ),
        html.Label('Feed in tariff (c/kWh):'),
        dcc.Input(id='input-feedin', value=7.135, type='number'), # default is 7.135c/kWh

        html.Label('Off peak tariff (c/kWh):'),
        dcc.Input(id='input-offpeak', value=15.1002, type='number'),  # default is 15.1002c/kWh

        html.Label('Shoulder tariff (c/kWh):'),
        dcc.Input(id='input-shoulder', value=28.7076, type='number'),  # default is 28.7076c/kWh

        html.Label('Peak tariff (c/kWh):'),
        dcc.Input(id='input-peak', value=54.8142, type='number')  # default is 54.8142c/kWh

    ])

    @app.callback(
        Output('graph-with-input', 'figure'),
        [Input('input-area', 'value'),
         Input('input-feedin','value'),
         Input('input-offpeak','value'),
         Input('input-shoulder','value'),
         Input('input-peak','value')])

    def update_figure(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak):
        new_df = runcalcs(sensor_df, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)

        new_df_agg = new_df.groupby('Month', as_index=False).agg({"BillReduction": "sum"})

        plotdata = go.Bar(x=new_df_agg['Month'], y=new_df_agg['BillReduction'])

        return {
            'data': [plotdata],
            'layout': go.Layout(
                xaxis={'title': 'Month'},
                yaxis={'title': 'Reduction in electricity bill ($)'}
            ),
        }

