import urllib3
import numpy as np
import pandas as pd
import xarray as xr
import geopandas
from tqdm import tqdm
from itertools import chain
from concurrent.futures import ProcessPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def regional_production():
    df_prod = pd.read_excel('./support_files/AGCDCASGS202021.xlsx', sheet_name='Table 1')
    df_prod.columns = df_prod.iloc[5,:]
    df_prod = df_prod.iloc[6:,:]
    df_prod[' Estimate '] = pd.to_numeric(df_prod[' Estimate '], errors='coerce')
    df_prod = df_prod.dropna(subset=['Commodity description', ' Estimate '])
    df_prod = df_prod[df_prod['Commodity description'].str.contains('Wheat for grain - Production')]
    df_prod = df_prod[['Region code', ' Estimate ']]
    df_prod.rename({' Estimate ':'Estimate', 'Region code':'SA2_CODE21'}, axis=1, inplace=True)
    df_prod['SA2_CODE21'] = df_prod['SA2_CODE21'].astype(str)

    gpd = geopandas.read_file('./support_files/SA2_2021_AUST_SHP_GDA2020.zip')
    gpd = gpd.merge(df_prod, on='SA2_CODE21',how='left')
    gpd['Estimate'] = gpd['Estimate'].fillna(0)
    gpd = gpd[gpd['Estimate']>15000]
    return gpd


def merge_datasets(date: str, variables):
    
    params_dict = {
        '2m_temperature': '2t',
        'total_precipitation': 'tp',
        'snowfall':'sf',
        'leaf_area_index_low_vegetation': 'lai_lv'}
    
    ds_list = []
    for var in variables:
        short_name = params_dict[var]
        ds_list.append(xr.open_dataset(f'./data/{date}.grib', engine='cfgrib', filter_by_keys={'shortName': short_name}))  
    ds = xr.merge(ds_list)
    
    new_lon = np.linspace(ds.longitude[0], ds.longitude[-1], ds.dims['longitude'] * 4)
    new_lat = np.linspace(ds.latitude[0], ds.latitude[-1], ds.dims['latitude'] * 4)
    ds = ds.interp(latitude=new_lat, longitude=new_lon)
    
    ds.rio.write_crs("EPSG:4326", inplace=True)
    return ds


def process_moisture_vars(regional_production, date: str, moisture_vars=['total_precipitation', 'snowfall']):
    moisture_dict = {
        'total_precipitation': 'tp',
        'snowfall':'sf'}   
    ds = merge_datasets(date, moisture_vars)
    data_list = []
    for row_id in tqdm(range(len(regional_production))):
        w_xarr = ds.rio.clip([regional_production.iloc[row_id]['geometry']])
        values = w_xarr.groupby('valid_time').mean(dim=['latitude', 'longitude']).sum()
        
        data_list.append([regional_production.iloc[row_id,-7], regional_production.iloc[row_id,-1]] + [np.asarray(values[moisture_dict[key]]) for key in moisture_vars])

    table = pd.DataFrame(data_list, columns=['state', 'production']+moisture_vars)

    table = table.melt(id_vars=['state', 'production'])
    table['value'] = table['value'].astype(float)
    table['wvalue'] = table['value'] * table['production']
    table = table.groupby(['state', 'variable'], as_index=False).sum()
    table['value'] = table['wvalue'] / table['production']*1000
    table = table.drop(['wvalue', 'production'], axis=1)
    table['date'] = date
    return table


def process_hourly_vars(regional_production, date: str, hourly_vars=['2m_temperature', 'leaf_area_index_low_vegetation']):
        hourly_dict = {
                '2m_temperature': 't2m',
                'leaf_area_index_low_vegetation': 'lai_lv'}

        ds = merge_datasets(date, hourly_vars)
        data_list = []
        for row_id in tqdm(range(len(regional_production))):
                w_xarr = ds.rio.clip([regional_production.iloc[row_id]['geometry']]).resample({'time':'1D'})
                value_mean = w_xarr.mean().mean()
                value_max = w_xarr.max().mean()
                value_min = w_xarr.min().mean()
                data_list.append([regional_production.iloc[row_id,-7], regional_production.iloc[row_id,-1]] + [np.asarray(value_mean[hourly_dict[key]]) for key in hourly_vars] + [np.asarray(value_min[hourly_dict[key]]) for key in hourly_vars] + [np.asarray(value_max[hourly_dict[key]]) for key in hourly_vars])

        table = pd.DataFrame(data_list, columns=['state', 'production']+list(chain.from_iterable([[f"{variable}_{sub}" for variable in hourly_vars] for sub in ['mean', 'min', 'max']])))

        table = table.melt(id_vars=['state', 'production'])
        table['value'] = table['value'].astype(float)
        table['wvalue'] = table['value'] * table['production']
        table = table.groupby(['state', 'variable'], as_index=False).sum()
        table['value'] = table['wvalue'] / table['production']
        table = table.drop(['wvalue', 'production'], axis=1)
        table['date'] = date
        table['value'] = np.where(table['variable'].str.contains('2m_temperature'), table['value']-273.15, table['value'])
        return table
    

def process_all(date: str, suffix='australia'):
    try:
        print(date)
        reg_prod = regional_production()
        table = pd.concat([process_hourly_vars(reg_prod, date, ['2m_temperature']), process_moisture_vars(reg_prod, date, ['total_precipitation'])])
        table.to_csv(f'./data_era5/{date}_{suffix}.csv', index=None)
    except:
        pass


def main():
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_all, date.strftime("%Y-%m-%d")) for date in pd.date_range('1980-01-01', '2012-09-10')[::-1]]
        # [future.result() for future in futures]
    # for date in pd.date_range('1980-01-01', '2022-07-22')[::-1]:
    #         process_all(date.strftime("%Y-%m-%d"))


if __name__ == '__main__':
    main()