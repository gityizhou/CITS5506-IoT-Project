import numpy as np
import dash_core_components as dcc
import dash_html_components as html


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

