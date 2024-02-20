#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 13:33:15 2023

@author: mariofestersen
"""
import pandas as pd
import dash
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
import plotly.express as px
import random
import plotly.graph_objs as go

def getSongCount(slist):
    """ Add song count to dataframe """

    song_count_list = []
    for song_list in slist:
        song_count_list.append(len(song_list))

    return song_count_list

def splitSongs(df):
    df = df.fillna('')
    return_list = []
    for songlist_str in df:
        if songlist_str != "":
            try:
                songlist = songlist_str.split(',')
                for song in songlist:
                    return_list.append(song)
            except:
                print(f"Exception in splitSongs function: songlist_str = {songlist_str}")
    return return_list

# A function that takes in a dict and number(x amount of words) as input. Outputs a list of words and sizes(with respect to the frequencies)
def getTags(dictionary,number):
    words = []
    sizes = []

    counter = 0
    for w in sorted(dictionary, key=dictionary.get, reverse=True):
        words.append(w)
        sizes.append(dictionary[w])
       
        counter += 1
        if counter == number:
            break
    maxvalue = sizes[0]
    for i in range(len(sizes)):
        sizes[i] = sizes[i]/maxvalue*100 + 10
    return [words, sizes]

#Function to make a dict out of a df[col] with a count of frequencies)
def toDict(df_col, df):
    df[df_col] = df[df_col].map(lambda x: x)
    d_dict = {}
    for tags in df[df_col]:
        if tags != [""]:
            for tag in tags:
                tag = tag.strip()
                if tag not in d_dict:
                    d_dict[tag] = 1
                else:
                    d_dict[tag] += 1
    return d_dict

""" INITIATE """
app = dash.Dash(__name__)
data = pd.read_csv('setlist_csv_data.csv', encoding='utf-8', delimiter=";")

""" FILL EMPTIES """
data['tour'] = data['tour'].fillna("No Tour")
data['songs'] = data['songs'].fillna("")
types = data['tour'].unique()
data['songs'] = data['songs'].str.split(", ")

""" UNIQUE TOURS """
type_options = [{'label': i, 'value': i} for i in types]
type_options.append({'label': 'All Tours', 'value': 'all'})
# Convert date column to datetimes. Then convert them to year strings.s

""" CONVERT DATE TO YEARS """
data['date'] = pd.to_datetime(data['date'])
data['date'] = data['date'].dt.strftime('%Y') # Now they have the format "YYYY"
data['date'] = data['date'].astype(int)
mintime = data['date'].min()
maxtime = data['date'].max()


data['song_count'] = getSongCount(data['songs'])
""" A COUNT FOR EACH EVENING """


b_style = {
    'position': 'fixed', 
    'top': '25px', 
    'right': '50px', 
    'z-index':'100',
    'padding': '10px 30px',
    'border': '1px solid black',
    'border-radius': '5px',
    'box-shadow': 'rgba(0, 0, 0, 0.35) 0px 5px 15px',
    'background-color': 'lightblue',
    }



app.layout = html.Div([
    
                 html.Button('Reset map', id='reset', n_clicks=0, style=b_style),
                 html.H1(children="Red Hot Chilly Peppers - Tours",
                         style = {'textAlign':'center', 'font-family' : 'Roboto'}),
                 
                 html.Div(dcc.Dropdown(
                        id='tours',
                        options=type_options,
                        value='all'
                 )),
                 html.Div([
                     dcc.RangeSlider(
                       id='tour-dates',
                       min=mintime,
                       max=maxtime,
                       step=1,
                       value=[mintime,maxtime],
                       marks={i: str(i) for i in range(mintime, maxtime, 1)})
                 ]),
                 html.Div([
                     html.Div(
                         dcc.Graph(id='rhcp-map'),
                         style={'width':'100%','display':'inline-block','vertical-align':'top','margin':'8px 0px', 'padding':'0px'}),
                 ]),
                 
                 html.Div(
                     [dcc.Graph(id = "bar_chart")],
                     style={'width':'100%','display':'inline-block','vertical-align':'top','margin':'12px 8px 12px 0px', 'border': '1px solid grey'}),
                 
                 html.Div([
                     html.Div([
                         html.H3(id="word_count"),
                         html.Div(dcc.Input(
                             id="number",
                             type='range',
                             value=15,
                             step=5,
                             min=5,
                             max=100,
                             ),
                             )],
                             style={'display': 'block', 'margin': '8px 64px 0px 64px'}
                             ),
                     dcc.Graph(id="word_works")],
                     style={ 'width': '99%', 'display': 'block', 'background-color': 'lightblue', 'padding': '12px', 'border': '1px solid grey' }),
])

""" MAP """
@app.callback(
    [Output(component_id='rhcp-map', component_property='figure'),
     Output(component_id='word_works', component_property='clickData'),
     Output(component_id='reset', component_property='n_clicks')],
    [
        
        Input(component_id='tours', component_property='value'),
        Input(component_id='tour-dates', component_property='value'),
        Input(component_id='word_works', component_property='clickData'),
        Input(component_id='reset', component_property='n_clicks'),
    ]
)
def update_output(tour, tour_dates, clickData, n_clicks):

    mydata = data

    if tour != 'all' and n_clicks == 0:
        mydata = mydata[mydata['tour'] == tour]

    if tour_dates != [mintime,maxtime] and n_clicks == 0:
        mydata = mydata[mydata['date'] >= tour_dates[0]]
        mydata = mydata[mydata['date'] <= tour_dates[1]]

    if clickData != None and n_clicks == 0:
        clicked_song = clickData['points'][0]['text']
        
        # Here i need a subset where the song is contained in the songs column.
        mydata = mydata[mydata['songs'].apply(lambda x: clicked_song in x)]

        # Now I need a new data frame, where I store each unique venue and its geocodes.
        mydata = mydata.groupby('venue').agg({'venue': 'count', 'geocodeLat': 'mean', 'geocodeLon': 'mean'})
        print(mydata)

        # name the columns
        mydata.columns = ['count', 'geocodeLat', 'geocodeLon']

        # Reset the index to make 'venue' a regular column
        mydata.reset_index(inplace=True)
        
        
        fig = px.scatter_mapbox(
                            data_frame=mydata,
                            title="hello",
                            lat="geocodeLat",
                            lon="geocodeLon",
                            hover_name="venue",
                            hover_data=["venue"],
                            size="count",
                            color="count", # Fucking idiot package. Doesnt update correctly unless you add colors...
                            size_max=15,
                            zoom=0,
                            height=900,
                            mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":20,"b":0})
    
    else:
        fig = px.scatter_mapbox(
                            data_frame=mydata,
                            title="hello",
                            lat="geocodeLat",
                            lon="geocodeLon",
                            hover_name="tour",
                            hover_data=["id", "date", "venue"],
                            size="song_count",
                            color="tour",
                            size_max=15,
                            zoom=0,
                            height=900,
                            mapbox_style="open-street-map")
        fig.update_layout(margin={"r":0,"t":0,"l":20,"b":0})
    #clickData = None;
    n_clicks = 0
    return fig, clickData, n_clicks

""" BAR CHART """
@app.callback(
    [
    Output(component_id='bar_chart', component_property='figure'),
    Output(component_id='reset', component_property='n_clicks', allow_duplicate=True),
    ],
    [
        Input(component_id='word_works', component_property='clickData'),
        Input(component_id='reset', component_property='n_clicks')
    ], prevent_initial_call=True
)
def update_output(clickData, n_clicks):

    if clickData != None and n_clicks == 0:
        clicked_song = clickData['points'][0]["text"]
    else:
        clicked_song = "Intro Jam"
    mydata = data
    mydata = mydata[mydata['songs'].apply(lambda x: clicked_song in x)]
    
    # Create a dict with the indexes, and their counts.
    index_count = {index: 0 for index in range(1, 29)}
    for song_list in mydata['songs']:
        position = song_list.index(clicked_song) + 1
        index_count[position] = index_count[position] + 1
    
    
    i = []
    c = []
    # convert to dataframe
    for index, count in index_count.items():
        i.append(index)
        c.append(count)
    df2 = pd.DataFrame(data={'index': i, 'count': c})

    fig_bar = px.bar(df2,
                  x="index",
                  y="count",
                  title=f"Barchart of the index count of when {clicked_song} is played")
    n_clicks = 0
    return fig_bar, n_clicks

""" WORD WORKS """
#Wordcloud that works for interactions 
@app.callback(
    [
         Output(component_id='word_works', component_property='figure'),
         Output(component_id='word_count', component_property='children')
    ],
    [
        Input(component_id='tours', component_property='value'),
        Input(component_id='number', component_property='value')
    ]
)
def update_output(tour, number):
    mydata1 = data
    number = float(number)
    number = int(number)
    if tour != 'all':
        mydata1 = data[data['tour'] == tour]
    t_dict = toDict("songs", mydata1)
    size_dict = getTags(t_dict, int(number)) #Set number to the amount of tags you want to be visualized (utilising the two functions from above.)
    
    # I prefer slightly smaller teksts.
    for i in range(len(size_dict[1])):
        size_dict[1][i] /= 2
    
    x1 = random.choices(range(0, 6000), k=number)
    y1 = random.choices(range(100, 3500), k=number)
    
    ata = go.Scatter(  x=x1,
                       y=y1,
                       mode='text',
                       text=size_dict[0],
                       marker={'opacity': 0.8},
                       textfont={'size': size_dict[1]})
    layout = go.Layout({'xaxis': {'showgrid': True, 'showticklabels': True, 'zeroline': True},
                        'yaxis': {'showgrid': True, 'showticklabels': True, 'zeroline': True},
                        'height': 800})
    fig4 = go.Figure(data=[ata], layout=layout)
    
    return fig4, f"{number} words in the wordcloud"



if __name__ == '__main__':
    app.run_server(debug=True, port=8893)
    "asd"

