from solarpanel.data_processing import get_google_sheet, gsheet2df
from solarpanel.data_visualization import dash_test1
import dash

# main function of the app
if __name__ == '__main__':
    df = gsheet2df(get_google_sheet())
    data = df[['Year', 'WA']]
    app = dash.Dash()
    dash_test1(app, data)
    app.run_server(debug=True)
