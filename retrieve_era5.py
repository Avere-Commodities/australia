
import cdsapi
import urllib3
import pandas as pd


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


def main():
    for date in pd.date_range('1980-01-01', '2019-10-21')[::-1]:
        try:
            retrieve_data(date.strftime("%Y-%m-%d"), ['2m_temperature', 'total_precipitation', 'snowfall', 'leaf_area_index_low_vegetation'])
        except:
            print(date.strftime("%Y-%m-%d"))
            pass
        


if __name__ == '__main__':
    main()
