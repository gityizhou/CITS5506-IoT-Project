# Global variables
from datetime import datetime as dt

SENSOR_RANGE = 'real_data!A1:D'
TEST_RANGE = 'test_data!A1:C'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1hgnyrI9G6eB5pcBvBAaubaRcMFuLoAR0iLC_-aotFrY' # manually set from Google Sheets

# frequency between checking google sheets/updating the dash
wait_seconds = 5

# number of points to plot on the live sensor data
numlive = 100

# Panel constants
PanelW = 70  # panel width in mm
PanelL = 55  # panel length in mm
PanelA = (PanelW / 1000) * (PanelL / 1000) # panel area in m2

# default inputs for dash

default_area = 5
default_panelcost = 1500
default_feedin = 7.135
default_offpeak = 15.1002
default_shoulder = 28.7076
default_peak = 54.8142

default_startdate = dt(2018, 1, 29)
default_enddate = dt(2018, 1, 31)
