import pandas as pd
import numpy as np

def main():
    table_old = pd.read_csv('wheat_old_yields.csv')
    table_old['crop'] = 'Wheat'
    table_old.columns = ['year', 'region', 'yield', 'crop']

    table_new = pd.read_excel('https://daff.ent.sirsidynix.net.au/client/en_AU/search/asset/1033561/3', sheet_name=None)

    vlookup = 'Crops'
    sheet_list =[]
    for key in table_new.keys():
        if key != 'Index':
            table_sheet = table_new[key]
            table_sheet = table_sheet.dropna(how='all', axis=1)
            table_sheet = table_sheet.iloc[np.where(table_sheet==vlookup)[0][0]:]
            table_sheet.columns = table_sheet.iloc[0,:]
            table_sheet = table_sheet.iloc[1:,:]
            table_sheet['crop'] = np.where(table_sheet.iloc[:,1].isna(), table_sheet[vlookup], np.nan)
            table_sheet['item'] = np.where(table_sheet.iloc[:,1].isna(), np.nan, table_sheet[vlookup])
            table_sheet['crop'] = table_sheet['crop'].ffill()
            table_sheet = table_sheet.dropna(subset=['item'])
            table_sheet = table_sheet.drop(['Crops'], axis=1)
            table_sheet = table_sheet.melt(id_vars=['crop', 'item'], var_name='year')
            table_sheet = table_sheet.dropna()
            table_sheet = table_sheet.pivot(index=['crop', 'year'], columns='item', values='value')
            table_sheet = table_sheet[table_sheet['Area']>0]
            table_sheet['yield'] = table_sheet['Production'] / table_sheet['Area']
            table_sheet = table_sheet.reset_index()
            table_sheet = table_sheet.drop(['Area', 'Production'], axis=1)
            table_sheet['region'] = key
            table_sheet['year'] = table_sheet['year'].str.replace(' s', '')
            table_sheet['year'] = table_sheet['year'].str.replace(' f', '')
            sheet_list.append(table_sheet)
    table = pd.concat(sheet_list)
    table = pd.concat([table, table_old])
    table['year'] = table['year'].str[:4].astype(int)
    table.to_csv('australia_yields.csv', index=None)
    

if __name__ == '__main__':
    main()