from solarpanel.data_processing import get_google_sheet, gsheet2df
from solarpanel.data_visualization import dash_test1
import dash
import pandas as pd

# main function of the app
if __name__ == '__main__':
    df = gsheet2df(get_google_sheet())

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
    df["Timestamp"] = pd.to_datetime(df["Timestamp"].str.slice(0, 19),
                                     format='%d/%m/%Y %H:%M:%S')  # convert timestamp to a datetime format that Python understands

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    dash_test1(app, df)
    app.run_server(debug=True)
