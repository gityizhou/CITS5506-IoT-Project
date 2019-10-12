from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import numpy as np
import settings

def get_google_data(SHEET_RANGE):
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
                'credentials.json', settings.SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=settings.SPREADSHEET_ID,
                                range=SHEET_RANGE).execute()
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


# function to run calculations - takes in a dataframe of solar data, area of panels to install, tariffs and calculates generation, costs and savings

def runcalcs(df, InstalledPanelA, TariffFeedIn, TariffOffPeak, TariffShoulder, TariffPeak):
    df_tariffs = pd.Series([TariffOffPeak, TariffShoulder, TariffPeak], index=[0, 1, 2]) # grid tariffs in c/kWh: 0 = offpeak, 1 = shoulder, 2 = peak

    print(df.shape)
    print(list(df))

    df["Generation(kW)"] = df["Generation(W/m2)"] * InstalledPanelA / 1000  # calculate generation from installed panels (hypothetical m2)
    df["SolarConsumed(kW)"] = df[["House(kW)", "Generation(kW)"]].min(axis=1)
        #df[["House(kW)", "Generation(kW)"]].min(axis=1)  # based on what the house consumed, calculate how much solar is consumed
    df["SolarExported(kW)"] = (df["Generation(kW)"] - df["House(kW)"]).clip(lower=0)  # if there is solar exceeding what the house needs, export that to the grid
    df["GridConsumed(kW)"] = (df["House(kW)"] - df["Generation(kW)"]).clip(lower=0)  # if not enough solar is generated, will need electricity from the grid
    Interval = pd.Timedelta(df["Timestamp"][1] - df["Timestamp"][0]).seconds / 60
    df["Weekday"] = df["Timestamp"].dt.dayofweek  # Monday = 0, Sunday = 6
    df["Month"] = df["Timestamp"].dt.month # month in number format - for use in summarising results
    df["Hour"] = df["Timestamp"].dt.hour # hour of this interval in number format - for determining appropriate tariff

    # map days of the week to weekdays/weekend - used to determine appropriate tariff
    df_days = pd.Series([0, 0, 0, 0, 0, 1, 1], index=[0, 1, 2, 3, 4, 5, 6])  # 0 = weekday, 1 = weekend
    df["DayType"] = df["Weekday"].map(df_days) # m

    # this sets up the timings for peak/offpeak tariffs from the grid
    # uses times from Synergy current rates
    # 0 = offpeak, 1 = shoulder, 2 = peak
    conditions = [
        (df["Hour"] < 7) | (df["Hour"] >= 21),  # before 7am or after 9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 7) & (df["Hour"] < 15),  # weekdays from 7am-3pm
        (df["Weekday"] == 1) & (df["Hour"] >= 7) & (df["Hour"] < 21),  # weekends from 7am-9pm
        (df["Weekday"] == 0) & (df["Hour"] >= 15) & (df["Hour"] < 21)]  # weekdays from 3pm-9pm
    choices = [0, 1, 1, 2]

    df["TariffType"] = np.select(conditions, choices) # identify which tariff applies in each interval
    df["Tariff"] = df["TariffType"].map(df_tariffs)  # map actual tariffs in c/kWh onto the intervals

    df["RevenueFeedIn"] = df["SolarExported(kW)"] / (60 / Interval) * TariffFeedIn / 100  # how much money is made from exporting solar
    df["SavingsSolar"] = df["SolarConsumed(kW)"] / (60 / Interval) * df["Tariff"] / 100  # how much money is saved from using solar instead of grid
    df["BillReduction"] = df["RevenueFeedIn"] + df["SavingsSolar"]  # total reduction in electricity bill
    return df
