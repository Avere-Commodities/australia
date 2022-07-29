import requests
import datetime
import pandas as pd
from os import listdir
from os.path import isfile, join


aus_dict = {
    1015184: 'New South Wales',
    1015186: 'Queensland',
    1015187: 'South Australia',
    1015188: 'Tasmania',
    1015189: 'Victoria',
    1015190: 'Western Australia',
}

headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = 'grant_type=password&\
username=AQ_AVERE_mln&\
password=AQ_AVERE_mln&\
client_id=agriquest_web&\
client_secret=agriquest_web.secret&\
scope=openid offline_access geo6:ndvigraph'
response = requests.post('https://identity.geosys-na.com/v2.1/connect/token', headers=headers, data=data)
bearer_token = 'Bearer ' + response.json()['access_token']


def run_general_request(region_ids: list, item: str, bearer_token: str,
                        start_date: str, end_date: str):
    headers = {'Authorization': bearer_token}
    indicatorTypeIds = [2]
    json_data = {
        'fillYearGaps': False,
        'amuIds': region_ids,
        'idBlock': 129,
        'idPixelType': 1,
        'indicatorTypeIds': indicatorTypeIds,
        'startDate': start_date,
        'endDate': end_date,
        'isMonthlyPrecipGraph': False,
    }
    response = requests.post(
        f'https://api.geosys-na.net/Agriquest/Geosys.Agriquest.CropMonitoring.WebApi/v0/api/{item}', headers=headers,
        json=json_data)
    js = response.json()
    df = pd.json_normalize(js['observedMeasures'])
    df['variable'] = item
    return df


def create_agriquest(start_date: str, end_date: str):
    states_list = []
    for key in aus_dict.keys():
        df_cy = pd.concat([run_general_request([key], var, bearer_token, start_date, end_date) for var in ['daily-precipitation', 'max-temperature', 'min-temperature', 'average-temperature']])
        df_cy['region'] = aus_dict[key]
        states_list.append(df_cy)
    table = pd.concat(states_list)
    table = table.drop(['dayId'], axis=1)
    table = table[['indicatorTypeId', 'time', 'region', 'variable', 'value']]
    table.columns = ['indicator', 'date', 'state', 'variable', 'value']
    table['date'] = pd.to_datetime(table['date'])
    return table


def create_era5():
    mypath = './data_era5/'
    all_files = pd.concat([pd.read_csv(join(mypath, f), parse_dates=['date']) for f in listdir(mypath) if isfile(join(mypath, f))])
    all_files['indicator'] = 2
    all_files['variable'] = all_files['variable'].replace({'2m_temperature_max': 'max-temperature', '2m_temperature_mean': 'average-temperature',
                                   '2m_temperature_min': 'min-temperature', 'total_precipitation' : 'daily-precipitation'})
    all_files = all_files[['indicator', 'date', 'state', 'variable', 'value']]
    return all_files
    
   
def main():
    current_year = datetime.datetime.now().year
    df_era5 = create_era5()
    last_date = df_era5['date'].max()+pd.DateOffset(days=1)
    df_cy = create_agriquest(last_date.strftime("%Y-%m-%d"), f'{current_year+1}-12-31')
    df_observed = pd.concat([df_era5, df_cy])
    df_observed = df_observed.sort_values(by=['indicator', 'date', 'state', 'variable'])
    df_observed.to_csv(r'G:\My Drive\australia\australia_weather.csv', index=None)
 
 
if __name__ == '__main__':
    main()