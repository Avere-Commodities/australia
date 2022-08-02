
import cdsapi
import urllib3
import pandas as pd
from support_files.resources import today
import datetime
from os import listdir
from os.path import isfile, join

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


"""
Documentation: https://apps.ecmwf.int/codes/grib/param-db
Documentation: https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=form
"""


client = cdsapi.Client()

def retrieve_data(date, variable):
    TIMES = [f'{hour:02}:00' for hour in range(0, 24)]

    params = {
            'product_type': 'reanalysis',
            'variable': variable,
            'date':date,
            'time': TIMES,
            'area': [-10, 110, -47, 155]
            }

    client.retrieve("reanalysis-era5-single-levels",
                    params, f"./data/{date}.grib")


def retrieve_era5():
    mypath = './data_era5/'
    all_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    start_date = (datetime.datetime.strptime(all_files[-1].split('_')[0], '%Y-%m-%d')+ datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    for date in pd.date_range(start_date, today):
        try:
            retrieve_data(date.strftime("%Y-%m-%d"), ['2m_temperature', 'total_precipitation'])
        except:
            print(date.strftime("%Y-%m-%d"))
            pass
        


if __name__ == '__main__':
    retrieve_era5()
