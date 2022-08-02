import datetime
from os import listdir
from os.path import isfile, join
import pandas as pd

current_year = datetime.datetime.now().year

weather_items = ['daily-precipitation', 'max-temperature', 'min-temperature', 'average-temperature']
all_weather_items_pretty = ['Daily Precipitation', 'Max Temperature', 'Min Temperature', 'Average Temperature']


mypath = './data_era5/'
all_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
start_date = (datetime.datetime.strptime(all_files[-1].split('_')[0], '%Y-%m-%d')+ datetime.timedelta(days=1)).strftime('%Y-%m-%d')
today = pd.to_datetime("today").strftime('%Y-%m-%d')