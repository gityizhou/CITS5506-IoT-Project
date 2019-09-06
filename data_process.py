from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The google sheet ID
SAMPLE_SPREADSHEET_ID = '1q53WTNloSUgEsD2g31wr74CSmvVTSDRmUVhR9dKXT_w'
# range of spreadsheet
# (if you only write the sheet name, it means the whole sheet)
SAMPLE_RANGE_NAME = 'test_data'


def get_google_sheet():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    return result


# convert google sheet to pandas data frame
def gsheet2df(result):
    """ Converts Google sheet data to a Pandas DataFrame.
    Note: This script assumes that your data contains a header file on the first row.
    Also note that the Google API returns 'none' from empty cells - in order for the code
    below to work, you'll need to make sure your sheet doesn't contain empty cells,
    or update the code to account for such instances.
    """
    header = result.get('values', [])[0]  # Assumes first line is header
    values = result.get('values', [])[1:]  # Everything else is data.
    if not values:
        print('No data found.')
    else:
        all_data = []
        for col_id, col_name in enumerate(header):
            column_data = []
            for row in values:
                column_data.append(row[col_id])
            ds = pd.Series(data=column_data, name=col_name)
            all_data.append(ds)
        df = pd.concat(all_data, axis=1)
        return df


# one test demo for playing data on dash
def dash_test1(app, data):
    # choose data from raw data sets
    y = np.array(data['WA'])
    x = np.array(data['Year'])
    colors = {
        'background': '#111111',
        'text': '#7FDBFF'
    }
    app.layout = html.Div(style={'backgroundColor': colors['background']},
                          children=[
                              html.H1(children='Hello Megan, Lin! ', style={'textAlign': 'center', 'color': '#7FDBFF'}),
                              dcc.Graph(
                                  id='line',
                                  config={'showAxisRangeEntryBoxes': True},
                                  figure={
                                      'data': [
                                          {'x': x, 'y': y, 'type': 'Scatter', 'name': 'Line'},
                                      ],
                                      'layout': {
                                          'plot_bgcolor': colors['background'],
                                          'paper_bgcolor': colors['background'],
                                          'font': {
                                              'color': colors['text']
                                          },
                                          'title': 'Number of small-scale PV systems installed in WA'

                                      }
                                  }
                              )
                          ])


if __name__ == '__main__':
    df = gsheet2df(get_google_sheet())
    data = df[['Year', 'WA']]
    app = dash.Dash()
    dash_test1(app, data)
    app.run_server(debug=True)
