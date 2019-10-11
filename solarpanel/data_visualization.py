import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime as dt
from solarpanel.data_processing import get_google_data, gsheet2df, runcalcs
import config

def dash_test1(app, df_annual):

    def description_card():
        """
        :return: A Div containing dashboard title & descriptions.
        """
        return html.Div(
            id="description-card",
            children=[
                html.H1("Solar Installation Explorer"),
  #              html.H3("Put some subheading text here if needed"),
                html.Div(
                    id="intro",
                    children="Based on sensor data collected, explore the impact of the proposed size of installed solar panels and electricity pricing structures.",
                ),
                html.Br(),
            ],
        )

    def generate_control_card():
        """
        :return: A Div containing controls for graphs.
        """
        return html.Div(
            id="control-card",
            # all of the controls for the dash
            children=[
                html.P("Area of panels to install (m2):"),
                dcc.Slider(id='input-area', min=1, max=20, value=5, marks={i: '{}'.format(i) for i in range(20)}), # default is 5m2
                html.Br(),
                html.Br(),
                html.P("Cost of panels to install ($/m2):"),
                dcc.Input(id='input-panelcost', value=1500, type='number'),  # default is $1500/m2
                html.Br(),
                html.Br(),
                html.P("Feed in tariff (c/kWh):"),
                dcc.Input(id='input-feedin', value=7.135, type='number'),  # default is 7.135c/kWh
                html.Br(),
                html.Br(),
                html.P("Off peak tariff (c/kWh):"),
                dcc.Input(id='input-offpeak', value=15.1002, type='number'),  # default is 15.1002c/kWh
                html.Br(),
                html.Br(),
                html.P("Shoulder tariff (c/kWh):"),
                dcc.Input(id='input-shoulder', value=28.7076, type='number'),  # default is 28.7076c/kWh
                html.Br(),
                html.Br(),
                html.P("Peak tariff (c/kWh):"),
                dcc.Input(id='input-peak', value=54.8142, type='number'),  # default is 54.8142c/kWh
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
                    children=html.Button(id="reset-btn", children="Reset", n_clicks=0),
                ),
            ],
        )

    app.layout = html.Div(
        id="app-container",
        children=[
            # Left column - header, description and controls
            html.Div(
                id="left-column",
                className="four columns",
                children=[description_card(), generate_control_card()],
                style={'marginBottom': 50, 'marginTop': 25}
            ),
            # Right column - charts
            html.Div(
                id="right-column",
                className="eight columns",
                children=[
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Hr(),

                    # Payback period and annual savings text
                    html.B("Payback period and annual savings"),
                    html.Div(id='payback'),
                    html.Hr(),

                    # Zeroth chart - live sensor data
                    html.Div(
                        id="sensor-graph",
                        children=[
                            html.B("Live sensor data"),
                            dcc.Graph(id="sensorstream"),
                            dcc.Interval(id='interval-component',interval=5*1000),
                            html.Hr(),
                        ],
                    ),

                   # First chart
                    html.Div(
                        id="first-graph",
                        children=[
                            html.B("Monthly savings"),
                            dcc.Graph(id="monthlysavingsgraph"),
                            html.Hr(),
                        ],
                    ),

                    # Second chart
                    html.Div(
                        id="second-graph",
                        children=[
                            html.B("Monthly electricity splits"),
                            dcc.Graph(id="monthlydetailedgraph"),
                            html.Hr(),
                        ],
                    ),

                    # Third chart
                    html.Div(
                        id="third-graph",
                        children=[
                            html.B("Annual sensor data"),
                            dcc.Graph(id="sensorgraph"),
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

    @app.callback(Output('sensorstream', 'figure'),
                  [Input('interval-component', 'n_intervals')])
    def update_metrics(n):
        df_actual = gsheet2df(get_google_data(SENSOR_RANGE))
        df_actual.rename(columns={'Solar power generated (W)': 'Solar(W)'}, inplace=True)
        df_actual["Solar(W)"] = pd.to_numeric(df_actual["Solar(W)"])
        df_actual["Generation(W/m2)"] = df_actual["Solar(W)"] / PanelA
        df_actual["Timestamp"] = pd.to_datetime(df_actual["Timestamp"].str.slice(0, 19),format='%d/%m/%Y %H:%M:%S')  # convert timestamp to a datetime format that Python understands

        df_chart = df_actual.iloc[-100:] # just get last 100 entries

        livedata = [go.Scatter(x=df_chart["Timestamp"], y=df_chart["Generation(W/m2)"], mode='lines')]

        return {
            'data': livedata,
            'layout': go.Layout(
                xaxis={'title': 'Timestamp'},
                yaxis={'title': 'Generation (W/m2)'}
            ),
        }

    @app.callback(
        Output('monthlysavingsgraph', 'figure'),
        [Input('input-area', 'value'),
         Input('input-feedin','value'),
         Input('input-offpeak','value'),
         Input('input-shoulder','value'),
         Input('input-peak','value')])

    def update_figure(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak):
        df_1 = runcalcs(df_annual, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)
        df_1_agg = df_1.groupby('Month', as_index=False).agg({"BillReduction": "sum"})
        plotdata = go.Bar(x=df_1_agg['Month'], y=df_1_agg['BillReduction'])

        return {
            'data': [plotdata],
            'layout': go.Layout(
                xaxis={'title': 'Month'},
                yaxis={'title': 'Reduction in electricity bill ($)'}
            ),
        }

    @app.callback(
        Output('monthlydetailedgraph', 'figure'),
        [Input('input-area', 'value'),
         Input('input-feedin','value'),
         Input('input-offpeak','value'),
         Input('input-shoulder','value'),
         Input('input-peak','value')])

    def update_figure2(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak):

        df_4 = runcalcs(df_annual, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)
        df_4_agg = df_4.groupby('Month', as_index=False).agg({"SolarConsumed(kW)": "sum","GridConsumed(kW)": "sum", "SolarExported(kW)": "sum"})

        plotdata1 = [go.Bar(name='Solar consumed', x=df_4_agg['Month'], y=df_4_agg['SolarConsumed(kW)']),
                     go.Bar(name='Solar exported', x=df_4_agg['Month'], y=df_4_agg['SolarExported(kW)']),
                     go.Bar(name='Grid consumed', x=df_4_agg['Month'], y=df_4_agg['GridConsumed(kW)'])]
        return {
            'data': plotdata1,
            'layout': go.Layout(
                xaxis={'title': 'Month'},
                yaxis={'title': 'Electricity (kW)'}
            ),
        }

    @app.callback(
        Output('payback', 'children'),
        [Input('input-area', 'value'),
         Input('input-feedin','value'),
         Input('input-offpeak','value'),
         Input('input-shoulder','value'),
         Input('input-peak','value'),
         Input('input-panelcost','value')])

    def update_payback(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak, selected_panelcost):
        df_2 = runcalcs(df_annual, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)
        savings = df_2["BillReduction"].sum()
        payback = selected_area*selected_panelcost/savings
        years, months = divmod(payback, 1)
        months = months*12
        return "The payback period is {:.0f} years and {:.0f} month(s), with annual savings of ${:,.2f}".format(years, months, savings)

    @app.callback(
        Output('sensorgraph', 'figure'),
        [Input("date-picker-select", "start_date"),
         Input("date-picker-select", "end_date")])

    def update_figure3(start_date, end_date):
        df_5 = df_annual.set_index("Timestamp")[start_date:end_date]
        df_5 = df_5.reset_index()

        plotdata2 = [go.Scatter(x=df_5["Timestamp"], y=df_5["Generation(W/m2)"], mode='lines')]

        return {
            'data': plotdata2,
            'layout': go.Layout(
                xaxis={'title': 'Timestamp'},
                yaxis={'title': 'Solar power measured (W/m2)'}
            ),
        }

    @app.callback(
        Output('profilegraph', 'figure'),
        [Input('input-area', 'value'),
         Input('input-feedin', 'value'),
         Input('input-offpeak', 'value'),
         Input('input-shoulder', 'value'),
         Input('input-peak', 'value'),
         Input("date-picker-select", "start_date"),
         Input("date-picker-select", "end_date")
         ])

    def update_figure4(selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak, start_date, end_date):
        df_6 = runcalcs(df_annual, selected_area, selected_feedin, selected_offpeak, selected_shoulder, selected_peak)
        df_6 = df_6.set_index("Timestamp")[start_date:end_date]
        df_6 = df_6.reset_index()

        plotdata3 = [go.Scatter(name='Solar generated', x=df_6["Timestamp"], y=df_6["Generation(kW)"], mode='lines'),
                     go.Scatter(name='Consumption', x=df_6["Timestamp"], y=df_6["House(kW)"], mode='lines')]

        return {
            'data': plotdata3,
            'layout': go.Layout(
                xaxis={'title': 'Timestamp'},
                yaxis={'title': 'Electricity (kW)'}
            ),
        }