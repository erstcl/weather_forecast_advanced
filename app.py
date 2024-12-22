from flask import Flask, render_template, request, redirect, Blueprint
import dash
from dash import dcc, html
import dash_leaflet
import plotly.graph_objs as go
from weather_api import (
    get_city_coordinates,
    get_weather_data,
    # check_bad_weather,
    # get_forecast,
    # get_location_key
)

# Flask app initialization
app = Flask(__name__)
bp = Blueprint('weather', __name__, url_prefix='/weather')
app.register_blueprint(bp)

# Dash app integration
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')

cities = []  # List of cities for the route

@app.route('/', methods=['GET', 'POST'])
def index():
    global cities
    if request.method == 'POST':
        start_point = request.form['start_point']
        end_point = request.form['end_point']
        intermediate_cities = request.form.getlist('intermediate_city')
        cities = [start_point, end_point] + intermediate_cities
        return redirect('/dash/')
    return render_template('index.html')

dash_app.layout = html.Div([
    html.H1("Карта маршрута", style={'textAlign': 'center'}),
    dash_leaflet.Map(center=[50, 50], zoom=4, children=[
        dash_leaflet.TileLayer(),
        dash_leaflet.LayerGroup(id="markers-layer"),
        dash_leaflet.Polyline(id="route-line", positions=[])
    ], id="map", style={'width': '100%', 'height': '50vh'}),
    html.Div(id='weather-graph-container', style={'width': '100%', 'height': 'auto'}),
    html.Div([
        dcc.Dropdown(
            id='metric-dropdown',
            options=[
                {'label': 'Температура', 'value': 'temperature'},
                {'label': 'Скорость ветра', 'value': 'wind_speed'},
                {'label': 'Вероятность осадков', 'value': 'precipitation'}
            ],
            value='temperature',
            clearable=False,
            style={'width': '50%'}
        ),
        dcc.Dropdown(
            id='days-dropdown',
            options=[
                {'label': '3 дня', 'value': 3},
                {'label': '5 дней', 'value': 5}
            ],
            value=3,
            clearable=False,
            style={'width': '50%'}
        )
    ], style={'marginTop': '10px', 'display': 'flex', 'justifyContent': 'center'})
])

@dash_app.callback(
    [dash.Output("markers-layer", "children"), dash.Output("route-line", "positions")],
    dash.Input('map', 'id')
)
def add_route_and_markers(_):
    city_markers = []
    route_positions = []
    for city in cities:
        coordinates = get_city_coordinates(city)
        if coordinates:
            route_positions.append(coordinates)
            city_markers.append(dash_leaflet.Marker(
                position=coordinates,
                children=[
                    dash_leaflet.Tooltip(city),
                    dash_leaflet.Popup([html.H3(city), html.P("")])
                ]
            ))
    return city_markers, route_positions

@dash_app.callback(
    dash.Output("weather-graph-container", "children"),
    [dash.Input("metric-dropdown", "value"), dash.Input("days-dropdown", "value")]
)
def update_graph(selected_metric, days):
    if not cities:
        return html.Div("Выберите город для отображения графиков")
    graphs = []
    for city_name in cities:
        weather_data = get_weather_data(city_name, days)
        if weather_data is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weather_data['date'],
                y=weather_data[selected_metric],
                mode='lines+markers',
                name=f'{city_name}'
            ))
            fig.update_layout(
                title=f'{selected_metric.capitalize()} в {city_name} за {days} дней',
                xaxis_title='Дата',
                yaxis_title='Значение',
                template='plotly_white'
            )
            graphs.append(dcc.Graph(figure=fig))
    return graphs if graphs else [html.Div("Нет данных для отображения")]

if __name__ == "__main__":
    app.run(port=8000)
