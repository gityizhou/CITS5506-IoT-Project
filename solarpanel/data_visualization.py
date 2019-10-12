import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime as dt
from solarpanel.data_processing import get_google_data, gsheet2df, runcalcs
import settings

def dash_test1(app, df_annual):

    # layout for the description and payback at the top
    def description_card():
        """
        :return: A Div containing dashboard title & descriptions.
        """
        return html.Div(
            id="description-card",
            children=[
                html.H1("Residential Solar Installation Explorer"),
  #              html.H3("Put some subheading text here if needed"),
                html.Div(
                    id="intro",
                    children="Explore the impact of the proposed size of installed solar panels and electricity pricing structures for the solar data collected.",
                ),
                # Payback period and annual savings text
                html.Div(dcc.Markdown(id='payback')),

            ],
        )

    # layout for all of the controls
    def generate_control_card():
        return html.Div(
            id="control-card",
            # all of the controls for the dash
            children=[
                html.B("Dashboard controls"),
                html.P("Area of panels to install (m2):"),
                dcc.Input(id='input-area', value=settings.default_area, type='number'), # default is 5m2
                html.Br(),
                html.Br(),
                html.P("Cost of panels to install ($/m2):"),
                dcc.Input(id='input-panelcost', value= settings.default_panelcost, type='number'),  # default is $1500/m2
                html.Br(),
                html.Br(),
                html.P("Feed in tariff (c/kWh):"),
                dcc.Input(id='input-feedin', value=settings.default_feedin, type='number'),  # default is 7.135c/kWh
                html.Br(),
                html.Br(),
                html.P("Off peak tariff (c/kWh):"),
                dcc.Input(id='input-offpeak', value=settings.default_offpeak, type='number'),  # default is 15.1002c/kWh
                html.Br(),
                html.Br(),
                html.P("Shoulder tariff (c/kWh):"),
                dcc.Input(id='input-shoulder', value=settings.default_shoulder, type='number'),  # default is 28.7076c/kWh
                html.Br(),
                html.Br(),
                html.P("Peak tariff (c/kWh):"),
                dcc.Input(id='input-peak', value=settings.default_peak, type='number'),  # default is 54.8142c/kWh
                html.Br(),
                html.Br(),
                html.P("Select date range:"),
                dcc.DatePickerRange(
                    id="date-picker-select",
                    start_date=dt(2018, 1, 1),
                    end_date=dt(2018, 1, 15),
                    min_date_allowed=dt(2018, 1, 1),
                    max_date_allowed=dt(2018, 12, 31),
                    initial_visible_month=dt(2018, 1, 1),
                ),
                html.Br(),
               html.Br(),
                html.Div(
                    id="reset-btn-outer",
                    children=html.Button(id="reset-btn", children="Reset all", n_clicks=0),
                ),
            ]
        )

    # overall layout
    app.layout = html.Div(
        id="app-container",
        children=[
            html.Div(
                id="titlebox",
                className="twelve columns",
                children=[description_card()],
                style={'marginBottom': 50, 'marginTop': 25}
            ),
            html.Div(
                id="left-column",
                className="three columns",
                children=[generate_control_card()],
                style={'marginLeft': 20, 'marginRight': 0}
            ),

            # Middle column
            html.Div(
                id="mid-column",
                className="four columns",
                children=[

                    # Live sensor data
                    html.Div(
                        id="sensor-graph",
                        children=[
                            html.B("Live sensor data"),
                            dcc.Graph(id="sensorstream", style={'height': '300px', 'marginBottom':'5px'}),
                            dcc.Interval(id='interval-component',interval=settings.wait_seconds*1000), # interval is in milliseconds so x1000
                            html.Hr(),
                        ],
                    ),

                    # Annual sensor data
                    html.Div(
                        id="third-graph",
                        children=[
                            html.B("Annual sensor data"),
                            dcc.Graph(id="sensorgraph", style={'height': '300px'}),
                            html.Hr(),
                        ],
                    ),
                ],
                style={'marginLeft': 0, 'marginRight': 0}
            ),

            # Right column
            html.Div(
                id="right-column",
                className="four columns",
                children=[
                    # First chart
                    html.Div(
                        id="first-graph",
                        children=[
                            html.B("Monthly savings - reduction in electricity bill"),
                            dcc.Graph(id="monthlysavingsgraph", style={'height': '250px'}),
                            html.Hr(),
                        ],
                    ),

                    # Second chart
                    html.Div(
                        id="second-graph",
                        children=[
                            html.B("Monthly electricity breakdown by source"),
                            dcc.Graph(id="monthlydetailedgraph", style={'height': '250px'}),
                            html.Hr(),
                        ],
                    ),

                    # Fourth chart
                    html.Div(
                        id="fourth-graph",
                        children=[
                            html.B("Anticipated profile"),
                            dcc.Graph(id="profilegraph"),
                            html.Hr(),
                        ],
                    ),
                ],
            ),
        ],
    className='row'
    )

    # update live sensor data
    @app.callback(Output('sensorstream', 'figure'),
                  [Input('interval-component', 'n_intervals')])
    def update_live(n):
        df_actual = gsheet2df(get_google_data(settings.SENSOR_RANGE))
        df_actual.rename(columns={'Solar power generated (W)': 'Solar(W)'}, inplace=True)
        df_actual["Solar(W)"] = pd.to_numeric(df_actual["Solar(W)"])
        df_actual["Generation(W/m2)"] = df_actual["Solar(W)"] / settings.PanelA
        df_actual["Timestamp"] = pd.to_datetime(df_actual["Timestamp"].str.slice(0, 19),format='%d/%m/%Y %H:%M:%S')  # convert timestamp to a datetime format that Python understands

        df_chart = df_actual.iloc[-settings.numlive:] # just get last 100 entries

        livedata = [go.Scatter(x=df_chart["Timestamp"], y=df_chart["Generation(W/m2)"], mode='lines')]

        return {
            'data': livedata,
            'layout': go.Layout(
                xaxis={'title': 'Timestamp'},
                yaxis={'title': 'Solar power (W/m2)'},
                margin=go.layout.Margin(
                    b=50,
                    t=10)
            ),
        }

    # update all charts that depend on dash inputs
    @app.callback(
        [Output('monthlysavingsgraph', 'figure'),
         Output('monthlydetailedgraph', 'figure'),
         Output('payback', 'children'),
         Output('sensorgraph', 'figure'),
         Output('profilegraph', 'figure')],
        [Input('input-area', 'value'),
         Input('input-feedin','value'),
         Input('input-offpeak','value'),
         Input('input-shoulder','value'),
         Input('input-peak','value'),
         Input('input-panelcost','value'),
         Input("date-picker-select", "start_date"),
         Input("date-picker-select", "end_date")])
    def update_figures(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak, selected_panelcost, start_date, end_date):
        df_1 = runcalcs(df_annual, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)
        df_1_agg = df_1.groupby('Month', as_index=False).agg({"BillReduction": "sum"})

        df_2_agg = df_1.groupby('Month', as_index=False).agg(
            {"SolarConsumed(kW)": "sum", "GridConsumed(kW)": "sum", "SolarExported(kW)": "sum"})

        savings = df_1["BillReduction"].sum()
        payback = selected_area * selected_panelcost / savings
        years, months = divmod(payback, 1)
        months = months * 12

        df_3 = df_annual.set_index("Timestamp")[start_date:end_date]
        df_3 = df_3.reset_index()

        df_4 = df_1.set_index("Timestamp")[start_date:end_date]
        df_4 = df_4.reset_index()

        # bar chart by month for reduction in electricity bill
        plotdata1 = go.Bar(x=df_1_agg['Month'], y=df_1_agg['BillReduction'])
        data1return = {'data': [plotdata1],
                       'layout': go.Layout(
                           xaxis={'title': 'Month'},
                           yaxis={'title': 'Bill reduction ($)'},
                           margin=go.layout.Margin(b=50, t=10))}

        # bar chart by month showing split by solar consumed, grid consumed and solar exported
        plotdata2 = [go.Bar(name='Solar consumed', x=df_2_agg['Month'], y=df_2_agg['SolarConsumed(kW)']),
                     go.Bar(name='Solar exported', x=df_2_agg['Month'], y=df_2_agg['SolarExported(kW)']),
                     go.Bar(name='Grid consumed', x=df_2_agg['Month'], y=df_2_agg['GridConsumed(kW)'])]
        data2return = {'data': plotdata2,
                       'layout': go.Layout(
                           xaxis={'title': 'Month'},
                           yaxis={'title': 'Electricity (kW)'},
                           margin=go.layout.Margin(b=50,t=10))}

        # text for payback period at the top
        data3return = '''Based on the inputs below the payback period is _**{:.0f} years and {:.0f} month(s)**_, with annual savings of _**${:,.2f}**_'''.format(
            years, months, savings)

        # annual sensor data graph
        plotdata3 = [go.Scatter(x=df_3["Timestamp"], y=df_3["Generation(W/m2)"], mode='lines')]
        data4return =  {'data': plotdata3,
                        'layout': go.Layout(
                            xaxis={'title': 'Timestamp'},
                            yaxis={'title': 'Solar power (W/m2)'},
                            margin=go.layout.Margin(b=50,t=10))}

        # detailed profile line chart
        plotdata4 = [go.Scatter(name='Solar consumed', x=df_4["Timestamp"], y=df_4["SolarConsumed(kW)"], mode='lines'),
                     go.Scatter(name='Solar exported', x=df_4["Timestamp"], y=df_4["SolarExported(kW)"], mode='lines'),
                     go.Scatter(name='Grid consumed', x=df_4["Timestamp"], y=df_4["GridConsumed(kW)"], mode='lines'),]
        data5return = {'data': plotdata4,
                       'layout': go.Layout(
                           xaxis={'title': 'Timestamp'},
                           yaxis={'title': 'Electricity (kW)'},
                           margin=go.layout.Margin(b=50,t=10))}

        return data1return, data2return, data3return, data4return, data5return

    # reset all inputs back to default values
    @app.callback(
        [Output('input-area', 'value'),
         Output('input-feedin', 'value'),
         Output('input-offpeak', 'value'),
         Output('input-shoulder', 'value'),
         Output('input-peak', 'value'),
         Output('input-panelcost','value'),
         Output("date-picker-select", "start_date"),
         Output("date-picker-select", "end_date")],
        [Input('reset-btn', 'n_clicks')])
    def resetall(n):
        return settings.default_area, \
               settings.default_feedin, \
               settings.default_offpeak, \
               settings.default_shoulder, \
               settings.default_peak, \
               settings.default_panelcost, \
               settings.default_startdate, \
               settings.default_enddate