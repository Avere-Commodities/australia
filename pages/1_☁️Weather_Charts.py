import datetime
import pandas as pd
import streamlit as st
from support_files.resources import current_year, all_weather_items_pretty


st.set_page_config(page_title="Weather per Region", layout='wide')
charts_container, models_container = st.container(), st.container()

min_start = datetime.date(current_year, 3, 1)
max_start = datetime.date(current_year, 12, 31)



def main():
    st.write('qwe')
    # regions_list = pd.read_csv(mapping_path).query('region_1=="Russia"')['region_2'].to_list()
    # regions_list.sort()
    
    with st.sidebar:
        add_class = st.selectbox("Crop Type", ('Wheat', 'Barley', 'Canola'))
        col11, col21 = st.columns(2)
        add_region = st.selectbox("Choose a Region", ('New South Wales', 'Western Australia','Victoria', 'South Australia','Queensland'))
        start = col11.date_input("Start Date", min_start, min_value=min_start, max_value=max_start)
        end = col21.date_input("End Date", max_start, min_value=min_start, max_value=max_start)

        weather_options = st.multiselect('Parameter ', all_weather_items_pretty, ['Daily Precipitation'])


if __name__ == '__main__':
    main()