import os
import numpy as np
import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from datetime import date, datetime

"""File Path"""
"""The visualization state is not integrated with S3 yet"""
BASE_PATH = r'Your local file path goes here'
COL_NAMES = ['DATETIME','LOCATION','TREND_NAME','TREND_NUMBER','TWEET_VOLUME']

concatenated_df = pd.concat([pd.read_csv(os.path.join(BASE_PATH,x),names=COL_NAMES,encoding="utf-8")
                             for x in os.listdir(BASE_PATH) if os.path.splitext(x)[1] == ".csv"],
                            axis=0,ignore_index=True)

concatenated_df = concatenated_df.astype({'DATETIME':np.datetime64})
Date = pd.to_datetime(concatenated_df['DATETIME']).dt.strftime('%Y%m%d')
concatenated_df['DATE'] = pd.to_datetime(Date, infer_datetime_format=True)

# Get list of all countries
all_countries = concatenated_df.LOCATION.unique()
trend_positions = concatenated_df.TREND_NUMBER.unique()

#app = dash.Dash(__name__)
app = dash.Dash(external_stylesheets = [dbc.themes.BOOTSTRAP])
app.title = "Trend Visualization"
server = app.server

row1 = html.Div(
    [
        """ Title """
        html.Div([
            html.H1("Twitter Trend Visualization", style={'text-align': 'center'}),
         ]),
        dbc.Row([
            """ Arrange the selections as a single Row """
            dbc.Col([
                dcc.Dropdown(
                    id='dropdown',
                    options=[
                        {'label': x, 'value': x}
                        for x in all_countries
                    ],
                    style={'width': '250px'},
                    value='Worldwide',)
            ]),
            dbc.Col([
                dcc.DatePickerSingle(
                    id='my-date-picker-single',
                    min_date_allowed=date(2020, 12, 28),
                    initial_visible_month=date(2020, 12, 28),
                    date=datetime.today().strftime('%Y-%m-%d'),
                    style={'width': '250px'})
            ]),
            dbc.Col([
                dcc.Dropdown(
                    id='dropdown_trend',
                    options=[
                        {'label': x, 'value': x}
                        for x in trend_positions
                        ],
                    style={'width': '100px'},
                    placeholder='Top X')
            ])
        ], align="center"),
        dcc.Graph(id="line-chart"),
    ]
)

app.layout = dbc.Container(children=[row1, html.Br()])

""" Choices / Selections Input"""
@app.callback(
    Output('line-chart', 'figure'),
    [Input('dropdown', 'value'),
     Input('my-date-picker-single', 'date'),
     Input('dropdown_trend', 'value')])

""" Update the line chart as chosen by user."""
def update_line_chart(country, start_date, trend_position):
    country_df = concatenated_df.loc[(concatenated_df['LOCATION'] == country)
                                    & (concatenated_df['TREND_NUMBER'] <= int(trend_position))
                                    & (concatenated_df['DATE'] == start_date)
                                   ]

    graph_df = country_df.loc[country_df['TREND_NAME'].
        isin(country_df.loc[country_df['DATETIME'] == country_df['DATETIME'].min()]['TREND_NAME'])]

    fig = px.line(graph_df, x="DATETIME", y="TWEET_VOLUME", color='TREND_NAME', hover_name='TREND_NAME')
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)