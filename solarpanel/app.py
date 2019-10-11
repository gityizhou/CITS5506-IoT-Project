from solarpanel.data_processing import get_google_data, gsheet2df
from solarpanel.data_visualization import dash_test1
import dash
import pandas as pd
import settings

if __name__ == '__main__':

    df1 = gsheet2df(get_google_data(settings.TEST_RANGE))

    df1.rename(columns={'Solar power generated (W)': 'Solar(W)',
                       'Household consumption (kW)': 'House(kW)'}, inplace=True)

    df1["Solar(W)"] = pd.to_numeric(df1["Solar(W)"])
    df1["House(kW)"] = pd.to_numeric(df1["House(kW)"])
    df1["Generation(W/m2)"] = df1["Solar(W)"] / settings.PanelA
    df1["Timestamp"] = pd.to_datetime(df1["Timestamp"].str.slice(0, 19),
                                     format='%d/%m/%Y %H:%M:%S')  # convert timestamp to a datetime format that Python understands

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    dash_test1(app, df1)
    app.run_server(debug=True)
