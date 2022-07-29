import datetime
import pandas as pd
import streamlit as st
from support_files.resources import current_year, all_weather_items_pretty
from support_files.quickstart import credentials, download_dataframe
from streamlit_charts import Weather_Report

st.set_page_config(page_title="Weather per Region", layout='wide')
charts_container, models_container = st.container(), st.container()

min_start = datetime.date(current_year, 3, 1)
max_start = datetime.date(current_year, 12, 31)

creds = credentials()

def main():
    df = download_dataframe(creds=creds, filename='australia_weather.csv',  parse_dates=['date', 'unified_date'])
    yields = pd.read_csv('./support_files/australia_yields.csv')

    with st.sidebar:
        col11, col21 = st.columns(2)
        add_class = st.selectbox("Crop Type", ('Wheat', 'Barley', 'Canola'))
        add_region = st.selectbox("Choose a Region", ('New South Wales', 'Western Australia','Victoria', 'South Australia','Queensland'))
        start = col11.date_input("Start Date", min_start, min_value=min_start, max_value=max_start)
        end = col21.date_input("End Date", max_start, min_value=min_start, max_value=max_start)

        weather_options = st.multiselect('Parameter ', all_weather_items_pretty, ['Daily Precipitation'])


    
    with charts_container:
        st.markdown("#### **Weather Charts**")
        for weather in weather_options:
            weather = weather.replace(' ','-').lower()
            subdf = df.query('variable == @weather & state==@add_region')
            subyields = yields.query('crop=="Wheat" & region==@add_region')
            region_df = Weather_Report(subdf, subyields, add_region)

            st.plotly_chart(region_df.get_weather_chart(weather_options, start, end), use_container_width=True)
            
    with models_container:
        st.markdown("#### **Regression Charts**")
    for weather in weather_options:
        weather = weather.replace(' ','-').lower()
        
        
if __name__ == '__main__':
    main()