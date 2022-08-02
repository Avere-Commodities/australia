import datetime
import pandas as pd

current_year = datetime.datetime.now().year

weather_items = ['daily-precipitation', 'max-temperature', 'min-temperature', 'average-temperature']
all_weather_items_pretty = ['Daily Precipitation', 'Max Temperature', 'Min Temperature', 'Average Temperature']

today = pd.to_datetime("today").strftime('%Y-%m-%d')