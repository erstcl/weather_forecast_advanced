import requests
import pandas as pd
from datetime import datetime
# import random


API_KEY = "SlQLdL8V9RaiYUQv8IADktwUWRaX1gAu"

def get_city_coordinates(city_name):
    url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city_name}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None
    location_data = response.json()
    if not location_data:
        print("Город не найден")
        return None
    latitude = location_data[0]["GeoPosition"]["Latitude"]
    longitude = location_data[0]["GeoPosition"]["Longitude"]
    return (latitude, longitude)

def get_weather_data(city, days):
    location_key = get_location_key(city, API_KEY)
    url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}?apikey={API_KEY}&metric=true&details=true"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None
    forecast_data = response.json()["DailyForecasts"]
    data = {
        "date": [datetime.strptime(day["Date"][:10], "%Y-%m-%d") for day in forecast_data[:days]],
        "temperature": [day["Temperature"]["Maximum"]["Value"] for day in forecast_data[:days]],
        "wind_speed": [day["Day"]["Wind"]["Speed"]["Value"] for day in forecast_data[:days]],
        "precipitation": [day["Day"].get("PrecipitationProbability", 0) for day in forecast_data[:days]]
    }
    return pd.DataFrame(data)

def get_forecast(location_str, api_key):
    location_key = get_location_key(location_str, api_key)
    url = f"http://dataservice.accuweather.com/currentconditions/v1/daily/5day/{location_key}"
    params = {"apikey": api_key, "details": "true", "metric": "true"}
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении прогноза погоды: {e}")
        return None

def get_location_key(location, api_key):
    url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={api_key}&q={location}"
    response = requests.get(url)
    print(response.json())
    if response.status_code == 503:
        print(f"Проблема на сервере (кончились запросы API): {response.status_code}")
        return None
    if response.status_code != 200:
        print(f"Ошибка поиска города: {response.status_code}")
        return None
    data = response.json()
    return data[0]["Key"] if data else None

def check_bad_weather(temperature, wind_speed, precipitation_prob, has_precipitation):
    if temperature < 0 or temperature > 35:
        return "Неблагоприятные условия - температура"
    if wind_speed > 50:
        return "Неблагоприятные условия - ветер"
    if precipitation_prob > 70 or has_precipitation:
        return "Неблагоприятные условия - осадки"
    return "Благоприятные условия"
