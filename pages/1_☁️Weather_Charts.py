import datetime
import pandas as pd
import streamlit as st
from support_files.resources import current_year


st.set_page_config(page_title="Weather per Region", layout='wide')
charts_container, models_container = st.container(), st.container()

min_start = datetime.date(current_year, 3, 1)
max_start = datetime.date(current_year, 12, 31)



def main():   
    # regions_list = pd.read_csv(mapping_path).query('region_1=="Russia"')['region_2'].to_list()
    # regions_list.sort()
    
    with st.sidebar:
        add_class = st.radio("Crop Type", ('Winter Wheat', 'Spring Wheat'))
        col11, col21 = st.columns(2)
        add_region = st.selectbox("Choose a Region", tuple(wwht_regions))
        start = col11.date_input("Start Date", min_start, min_value=min_start, max_value=max_start_wwht)
        end = col21.date_input("End Date", max_start_wwht, min_value=min_start_wwht, max_value=max_start_wwht)

        weather_options = st.multiselect('Parameter ', all_weather_items_pretty, ['Daily Precipitation'])

    
    # region_df = Weather_Report(add_region, add_class)
    
    # with charts_container:
    #     st.markdown("#### **Weather Charts**")
    #     for weather in weather_options:
    #         weather = weather.replace(' ','-').lower()
    #         st.plotly_chart(region_df.get_weather_chart(weather, start, end), use_container_width=True)

    # with models_container:
    #     st.markdown("#### **Regression Charts**")
    #     for weather in weather_options:
    #         weather = weather.replace(' ','-').lower()
    #         if weather != 'soil-moisture':
    #             st.plotly_chart(region_df.get_weather_analytics(weather, start, end), use_container_width=True)    


if __name__ == '__main__':
    main()