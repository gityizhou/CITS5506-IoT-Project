from solarpanel.data_processing import get_google_sheet, gsheet2df
from solarpanel.data_visualization import dash_test1
import dash
import numpy as np
import pandas as pd

# main function of the app
if __name__ == '__main__':
    df = gsheet2df(get_google_sheet())

    # inputs to go on the dash later
    InstalledPanelA = 5  # area of panels to be installed in m2
    TariffFeedIn = 7.135  # feed in tariff, in c/kWh

    # grid tariffs in c/kWh
    # 0 = offpeak, 1 = shoulder, 2 = peak
    df_tariffs = pd.Series([15.1002, 28.7076, 54.8142], index=[0, 1, 2])

    # Panel constants
    PanelW = 70  # panel width in mm
    PanelL = 55  # panel length in mm
    Rating = 0.5  # cell rating in W
    PanelA = (PanelW / 1000) * (PanelL / 1000)

    df.rename(columns={'Solar power generated (W)': 'Solar(W)',
                       'Household consumption (kW)': 'House(kW)'}, inplace=True)

    df["Solar(W)"] = pd.to_numeric(df["Solar(W)"])
    df["House(kW)"] = pd.to_numeric(df["House(kW)"])

    df["Generation(W/m2)"] = df["Solar(W)"] / PanelA
    df["Generation(kW)"] = df["Generation(W/m2)"] * InstalledPanelA / 1000
    df["SolarConsumed(kW)"] = df[["House(kW)", "Generation(kW)"]].min(axis=1)
    df["SolarExported(kW)"] = df["Generation(kW)"] - df["House(kW)"]
    df["SolarExported(kW)"] = df["SolarExported(kW)"].clip(lower=0)

    df["GridConsumed(kW)"] = df["House(kW)"] - df["Generation(kW)"]
    df["GridConsumed(kW)"] = df["GridConsumed(kW)"].clip(lower=0)

    df["Timestamp"] = pd.to_datetime(df["Timestamp"].str.slice(0, 19), format='%d/%m/%Y %H:%M:%S')

    Interval = pd.Timedelta(df["Timestamp"][1] - df["Timestamp"][0]).seconds / 60
    df["Weekday"] = df["Timestamp"].dt.dayofweek  # Monday = 0, Sunday = 6
    df["Month"] = df["Timestamp"].dt.month
    df["Hour"] = df["Timestamp"].dt.hour

    df_days = pd.Series([0, 0, 0, 0, 0, 1, 1], index=[0, 1, 2, 3, 4, 5, 6])
    df["DayType"] = df["Weekday"].map(df_days)  # 0 = weekday, 1 = weekend

    # 0 = offpeak, 1 = shoulder, 2 = peak
    conditions = [
        (df["Hour"] < 7) | (df["Hour"] >= 21),  # before 7am or after 9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 7) & (df["Hour"] < 15),  # weekdays from 7am-3pm
        (df["Weekday"] == 1) & (df["Hour"] >= 7) & (df["Hour"] < 21),  # weekends from 7am-9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 15) & (df["Hour"] < 21)]
    choices = [0, 1, 1, 2]

    df["TariffType"] = np.select(conditions, choices)
    df["Tariff"] = df["TariffType"].map(df_tariffs)

    df["RevenueFeedIn"] = df["SolarExported(kW)"] / (60 / Interval) * TariffFeedIn / 100
    df["SavingsSolar"] = df["SolarConsumed(kW)"] / (60 / Interval) * df["Tariff"] / 100
    df["BillReduction"] = df["RevenueFeedIn"] + df["SavingsSolar"]

    df_plot = df.groupby('Month', as_index=False).agg({"BillReduction": "sum"})

    app = dash.Dash()
    dash_test1(app, df_plot)
    app.run_server(debug=True)
