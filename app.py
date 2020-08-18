import requests
from pandas import json_normalize
import json
import pandas as pd
from urllib.request import urlopen
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly
import numpy
import array as arr
import dash_table

from functools import reduce


external_stylesheets = ['https://codepen.io/lt47/pen/MWyamZe.css']
#external_scripts = []
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



colnames = ['Restaurant', 'Borough', 'Building', 'Street', 'Zipcode', 'Phone Number',
            'Cuisine Description', 'Inspection Date', 'Action',
            'Violation Code', 'Violation Description', 'Critical Flag',
            'Score', 'Record Date', 'Inspection Type',
            'Latitude', 'Longitude', 'Community Board', 'Council District',
            'Census Tract', 'Bin', 'Bbl', 'Nta', 'Grade', 'Grade Date']

nyc_df = pd.read_csv('https://raw.githubusercontent.com/lt47/nyc-restaurant-inspections/master/smaller-nyc-rest.csv',
                     names=colnames, header=None, skiprows=1)
nycdf = pd.DataFrame(nyc_df).fillna('N/a')


labelcuisine = pd.DataFrame(nyc_df)
labelcuisine['Critical Value'] = labelcuisine['Critical Flag'].map({
                                                                   'Y': 1, 'N': 0})
total_critical_by_cuisine = labelcuisine.groupby('Cuisine Description')['Critical Flag'].apply(
    lambda x: (x == 'Y').sum()).reset_index(name='# of Critical Violations/Cuisine')

labelborough = pd.DataFrame(nyc_df)
labelborough['Critical Value'] = labelborough['Critical Flag'].map({
                                                                   'Y': 1, 'N': 0})
total_critical_by_borough = labelborough.groupby('Borough')['Critical Flag'].apply(
    lambda x: (x == 'Y').sum()).reset_index(name='# of Critical Violations/Borough')


#combined_df = nycdf.merge(zipcode_df, left_on='zipcode', right_on='fields.zip')
data = nycdf[['Restaurant', 'Borough', 'Cuisine Description', 'Inspection Date',
              'Violation Description', 'Critical Flag', 'Inspection Type',
              'Grade', 'Grade Date', 'Latitude', 'Longitude'
              ]]
data['Latitude'] = pd.to_numeric(data['Latitude'], errors='coerce')
data['Longitude'] = pd.to_numeric(data['Longitude'], errors='coerce')
data['# of Inspection Visits/Franchise'] = data['Restaurant'].map(
    data['Restaurant'].value_counts())
data['Restaurant'] = data['Restaurant'].astype(str)


# Contrived df columns
data['Critical Value'] = data['Critical Flag'].map({'Y': 1, 'N': 0})
calc_df = data[['Restaurant', 'Critical Value']]

total_critical = calc_df.groupby('Restaurant')['Critical Value'].sum(
).reset_index(name='# of Critical Violations/Franchise')


"""
#I cant use this as a recommendation for clean restaurants
#until I get a metric that asseses the remarks on the violation description to
#determine if the inspection was positive or negative and the severity or weight of the remarks.
#(i.e. very good, good, okay)
"""


# Merged dataframe, look up 'reduce'
data_frames = [data, total_critical]
df_merged = reduce(lambda left, right: pd.merge(left, right, on='Restaurant',
                                                how='outer'), data_frames).fillna('')
df_merged['Latitude'] = pd.to_numeric(df_merged['Latitude'])
df_merged['Longitude'] = pd.to_numeric(df_merged['Longitude'])
df_merged['# of Critical Violations/Franchise'] = pd.to_numeric(
    df_merged['# of Critical Violations/Franchise']).fillna(0)
df_merged['# of Inspection Visits/Franchise'] = pd.to_numeric(
    df_merged['# of Inspection Visits/Franchise']).fillna(0)


# Insights
max_crit_cuisine = total_critical_by_cuisine['Cuisine Description'][total_critical_by_cuisine[
    '# of Critical Violations/Cuisine'] == total_critical_by_cuisine['# of Critical Violations/Cuisine'].max()]
max_crit_franchise = total_critical['Restaurant'][total_critical['# of Critical Violations/Franchise']
                                                  == total_critical['# of Critical Violations/Franchise'].max()]
max_crit_borough = total_critical_by_borough['Borough'][total_critical_by_borough['# of Critical Violations/Borough']
                                                        == total_critical_by_borough['# of Critical Violations/Borough'].max()]


# CustomHover Hidden Column
df_merged['HoverText'] = df_merged[['Restaurant', '# of Critical Violations/Franchise']
                                   ].apply(lambda x: ','.join(x.map(str)), axis=1)
decoy = df_merged['HoverText']
uniqdecoy = df_merged['HoverText'].unique().tolist()

# Just Date
df_merged['Inspection Date'] = pd.to_datetime(
    df_merged['Inspection Date'], errors='coerce')
df_merged['Inspection Date'] = df_merged['Inspection Date'].dt.date

color = df_merged['# of Critical Violations/Franchise'].to_numpy().astype(int)
size = df_merged['# of Inspection Visits/Franchise'].to_numpy().astype(int)


#max_crit_franchise.to_csv('nutest.csv', index=False, mode='w+')

# The columns i need for the datatable
table_df = df_merged[['Restaurant', 'Borough', 'Cuisine Description', 'Inspection Date',
                      'Violation Description', 'Critical Flag', 'Inspection Type',
                      '# of Critical Violations/Franchise', '# of Inspection Visits/Franchise']]


def plot_map():
    px.set_mapbox_access_token(
        'ENTER YOUR MAPBOX KEY HERE')
    fig = px.scatter_mapbox(df_merged, lat=df_merged['Latitude'], lon=df_merged['Longitude'],
                            color=color, size=size, color_continuous_scale=px.colors.sequential.Rainbow,
                            size_max=15, zoom=10, center={'lon': -73.939, 'lat': 40.684},
                            width=950, height=550, mapbox_style='OPTIONAL CUSTOM MAPBOX STYLE',
                            custom_data=[df_merged['HoverText']])
    layout = {'paper_bgcolor': 'rgb(87, 87, 87)', 'font_color': 'white'}
    fig['layout'].update(layout)
    fig.update_traces(
        hovertemplate='<b>Restaurant Name, # of Violations</b><br>' + '<b>%{customdata}</b><br>')

    return html.Div(children=[
        html.Div(children=[
            html.Div(className='infobox',
                     children=[
                         html.H4(children='NYC Restaurant Inspection Data', style={
                                 'font-size': '47px', 'text-align': 'center', 'margin-bottom': '0'}),
                         dcc.Dropdown(id='dropdown', options=[
                             {'label': i, 'value': i} for i in uniqdecoy
                         ], optionHeight=45, multi=True, placeholder='Select Restaurant Name', style={'font-size': '15px', 'font-family': 'calibri',
                                                                                                      'height': '35px', 'font-weight': '500',
                                                                                                      'width': '100%', 'background-color': 'black',
                                                                                                      'color': 'black', 'margin-bottom': '10px'
                                                                                                      }),
                         html.A(href='https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j',
                                target='_blank', children='NYC Open Data'),
                         html.P(
                             'This dataset highlights inspection comments and critical flags given to NYC restaurants from Aug. 2014 to-date. (Showing 1000 rows only)'),
                         html.A(href='https://github.com/lt47/nyc-restaurant-inspections',
                                target='_blank', children='View repository for demo. with full dataset'),
                         html.Table([
                             html.Tr([html.Td(id='insightlabel1')]),
                             html.Tr([html.Td(id='insight1')]),
                             html.Tr([html.Td(id='insightlabel2')]),
                             html.Tr([html.Td(id='insight2')]),
                             html.Tr([html.Td(id='insightlabel3')]),
                             html.Tr([html.Td(id='insight3')]),
                         ], style={'padding-top': '17px', 'margin-right': 'auto',
                                   'font-size': '17px', 'font-weight': '350',
                                   'font-family': 'mentone, sans-serif',
                                   'color': 'white'})
                     ]),
            html.Div(
                dcc.Graph(
                    id='graph',
                    config={"displaylogo": False},
                    figure=fig), className='graph-one')
        ], style={'display': 'flex', 'align-items': 'center',
                  'justify-content': 'center', 'margin': 'auto',
                  'background-color': 'rgb(87, 87, 87)',
                  'padding-top': '64px'}),
        dash_table.DataTable(id='table-container', columns=[{"name": i, "id": i} for i in table_df.columns],
                             data=df_merged.to_dict('rows'),
                             style_header={
            'backgroundColor': '#000000',
            'fontWeight': 'bold',
            'fontSize': '17px',
            'fontFamily': 'calibri',
            'textAlign': 'center',
                         'color': 'white'
        },
            style_cell={
            'backgroundColor': 'white',
            'color': 'black',
            'height': 'auto',
            'fontSize': '15px',
            'fontFamily': 'calibri',
            'whiteSpace': 'normal',
            'textAlign': 'center'
        },
            style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
        })
    ])


@app.callback(
    Output('table-container', 'data'),
    [Input('graph', 'clickData')])
def display_click_data(clickData):
    # This should translate to (not clickData) and (not dropdown_value) via De Morgan's Law
    if not clickData:
        return df_merged.to_dict('rows')
    else:
        restaurant = clickData['points'][0]['customdata']
        clickdf = df_merged[df_merged['HoverText'].str.contains(
            '|'.join(restaurant))]
        return clickdf.to_dict('rows')


@app.callback(
    [Output('insightlabel1', 'children'),
     Output('insight1', 'children'),
     Output('insightlabel2', 'children'),
     Output('insight2', 'children'),
     Output('insightlabel3', 'children'),
     Output('insight3', 'children')],
    [Input('dropdown', 'value')])
def restaurant_stats(dropdown):
    if not dropdown:
        return ('The cuisine type with the most critical flags:',
                max_crit_cuisine,
                'The franchise with the most critical flags:',
                max_crit_franchise,
                'The borough with the most critical flags:',
                max_crit_borough
                )
    else:
        dropdowndf = df_merged[df_merged['HoverText'].str.contains(
            '|'.join(dropdown))]
        return ('Number of critical violations:', dropdowndf['# of Critical Violations/Franchise'].iloc[0],
                'Total number of inspection visits:', dropdowndf[
                    '# of Inspection Visits/Franchise'].iloc[0],
                'Cuisine Type:', dropdowndf['Cuisine Description'].iloc[0])


app.layout = plot_map


if __name__ == '__main__':
    app.run_server(debug=True)
