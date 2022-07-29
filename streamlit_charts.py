import joblib
from datetime import timedelta
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from combine_weather import weighted_weather
from support_files.quickstart import credentials, download_dataframe
# from support_files.resources import  get_translation, get_yields, wwht_start, swht_start
pd.options.mode.chained_assignment = None

creds = credentials()


def add_new_date(df: pd.DataFrame, grains_class: str):
    if grains_class == 'Winter Wheat':        
        df['new_time'] = wwht_start+pd.to_timedelta(df['day_of_year'], unit='d')
    else:
        df['new_time'] = swht_start+pd.to_timedelta(df['day_of_year'], unit='d')
    return df


def get_borders(state: str):
    new_names={
        'daily-precipitation':[],
        'max-temperature':[],
        'min-temperature':[],
        'average-temperature':[],
    }
    start_date = swht_start if 'Spring Wheat' in state else wwht_start
    model_path = [os.path.join("models", "final", file_name) for file_name in os.listdir(os.path.join("models", "final"))
                if ((state in file_name))]
    if len(model_path) > 0:
        model_path = [os.path.join("models", "final", file_name) for file_name in os.listdir(os.path.join("models", "final"))
                if ((state in file_name))][0]
        state_model = joblib.load(model_path)
        for xname in state_model.params.index:
            if xname.count('_') > 1:
                dates_range = list(map(lambda x: (start_date+timedelta(days=int(x))), xname.split('_')[:2]))
                new_xname = ' '.join(xname.split('_')[2:]).replace(' ','')
                if new_xname in new_names:
                    if state_model.params[xname] > 0:
                        dates_range.append('green')
                    else:
                        dates_range.append('red')
                    new_names[new_xname].append(dates_range)
    return new_names

class Weather_Report:
    def __init__(self, region_name: str, grains_class: str):
        self.region_name = region_name
        self.grains_class = grains_class
        self.country_yields = get_yields(region_name, grains_class, False)
        region_translated = str(get_translation(region_name, reverse=True))
        self.weather = add_new_date(weighted_weather(region_translated, grains_class, False), grains_class)
        self.borders = get_borders(f"{grains_class}_{get_translation(region_name, reverse=True)}")

    def get_weather_analytics(self, weather_variable: str, start_date: str, end_date: str):
        start_date, end_date = pd.Timestamp(start_date), pd.Timestamp(end_date)
        year_start = 2021 if start_date.month<9 else 2020
        if self.grains_class == 'Spring Wheat':
            year_start = 2020
        start_date, end_date = pd.Timestamp(year_start, start_date.month, start_date.day), pd.Timestamp(end_date.year-start_date.year+year_start, end_date.month, end_date.day)
        
        y_df = self.country_yields
        y_df.loc[y_df.index.max()+1]=y_df.loc[y_df.index.max()]

        x_df = self.weather[self.weather['year'].isin(y_df.index)]
        if weather_variable == 'vegetation-vigor-index':
            x_df = x_df.dropna(subset=weather_variable)
        last_year = x_df['year'].max()
        max_last_date = x_df.query('year==@last_year')['new_time'].max()
            
        boundary1, boundary2 = min(max_last_date, start_date), min(max_last_date, end_date)
        if boundary1 != boundary2:
            x_df = x_df.query('new_time>=@boundary1 & new_time<=@boundary2')
            if not weather_variable in ['vegetation-vigor-index', 'soil-moisture']:
                x_df = x_df.groupby(['year'], as_index=False)[weather_variable].mean()
            else:
                x_df = x_df.query('new_time==@boundary2')[['year', weather_variable]]
            x_df = x_df.merge(y_df, left_on='year', right_index=True)
            x_df[[weather_variable, 'Value']] = x_df[[weather_variable, 'Value']].diff()
            x_df = x_df.dropna()
 
            fig = px.scatter(x_df.query('year<@last_year'), x=weather_variable, y='Value', text=x_df.query('year<@last_year')['year'],
                                trendline="ols")
            fig.update_traces(textposition='top center', marker=dict(color='#5D69B1', size=6),
                                textfont=dict(color='#E58606'))
            fig.add_trace(go.Scatter(x=[x_df.query('year==@last_year')[weather_variable].values[0]], y=[0],
                                    showlegend=False, text=str(last_year), mode='markers', marker=dict(color='#FF0000', size=8)))

            model = px.get_trendline_results(fig)
            rsq = str(round(model.iloc[0]["px_fit_results"].rsquared, 3) * 100)[:4]
            if not weather_variable in ['vegetation-vigor-index', 'soil-moisture']:
                title_text = f"<b>{self.region_name} Yield vs Avg {weather_variable.title().replace('-', ' ')}, YoY - From {boundary1.strftime('%b %d')} To {boundary2.strftime('%b %d')}</b>"
            else:
                title_text = f"<b>{self.region_name} Yield vs {weather_variable.title().replace('-', ' ')}, YoY - As of {boundary2.strftime('%b %d')}</b>"
            fig.update_layout(
                title=title_text, 
                font=dict(color='rgb(82, 82, 82)', family='Arial'),
                xaxis=dict(gridcolor='#FFFFFF', title = f"{weather_variable.title().replace('-', ' ')}, YoY",
                                                linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                                tickfont=dict(size=12)),
                                        yaxis=dict(gridcolor='#FFFFFF', title="Wheat Yield, YoY"),
                                        plot_bgcolor='white')
            return fig


    def get_weather_chart(self, weather_variable: str, start_date: str, end_date: str):

        start_date, end_date = pd.Timestamp(start_date), pd.Timestamp(end_date)
        year_start = 2021 if start_date.month<9 else 2020
        if self.grains_class == 'Spring Wheat':
            year_start = 2020
        start_date, end_date = pd.Timestamp(year_start, start_date.month, start_date.day), pd.Timestamp(end_date.year-start_date.year+year_start, end_date.month, end_date.day)
        
        def get_analogs(weather_variable: str, last_year: int, max_last_date):
            if not weather_variable in ['vegetation-vigor-index', 'soil-moisture']:
                boundary = min(max_last_date, end_date)
                analogs_df = pd.concat([observed_data, ecm_data])
                analogs_df = analogs_df.query('new_time == @boundary')
                analogs_df[weather_variable] = abs(analogs_df[weather_variable] -
                            analogs_df.query('year==@last_year')[weather_variable].values[0])
            else:
                analogs_df = observed_data.dropna(subset=weather_variable)
                last_date = analogs_df.query('year==@last_year')['new_time'].max()
                analogs_df = analogs_df.query('new_time==@last_date')
            
            analogs_df[weather_variable] = abs(analogs_df[weather_variable] -
                                                analogs_df.query('year==@last_year')[weather_variable].values[0])
            analogs_df = analogs_df[analogs_df['year'].isin(self.country_yields.index)]
            first_analog, second_analog = analogs_df.sort_values(by=weather_variable)['year'][:2].to_list()    
            return [last_year, last_year - 1] + list({first_analog, second_analog})

        observed_data = self.weather[self.weather['time'] < pd.Timestamp.today()]
        ecm_data = self.weather[self.weather['time'] >= pd.Timestamp.today()]
        
        observed_data = observed_data.query('new_time>=@start_date & new_time<=@end_date')
        ecm_data = ecm_data.query('new_time>=@start_date & new_time<=@end_date')
        
        last_year = self.weather['year'].max()
        max_last_date = self.weather.query('year==@last_year')['new_time'].max()
        if weather_variable == 'daily-precipitation':
            observed_data = observed_data.groupby(['year', 'time', 'new_time']).sum().groupby(
                level=0).cumsum().reset_index()
            ecm_data = ecm_data.groupby(['year', 'time', 'new_time']).sum().groupby(
                level=0).cumsum().reset_index()           
            if len(observed_data.query('year==@last_year')):
                ecm_data[weather_variable] = ecm_data[weather_variable] + observed_data.query('year==@last_year')[weather_variable].max()


        excl_years = get_analogs(weather_variable, last_year, max_last_date)

        max_data = observed_data.query('year<@last_year').groupby('new_time', as_index=False)[
            ['new_time', weather_variable]].max()
        min_data = observed_data.query('year<@last_year').groupby('new_time', as_index=False)[
            ['new_time', weather_variable]].min()
        mean_data = observed_data.query('year<@last_year').groupby('new_time', as_index=False)[
            ['new_time', weather_variable]].mean()

        fig = px.line(observed_data[observed_data['year'].isin(excl_years)==False], x='new_time', y=weather_variable,
                      color_discrete_sequence=px.colors.qualitative.G10, color='year', labels={weather_variable:'', 'new_time':'', 'year':''})
        fig.update_traces(visible="legendonly")
        fig.add_trace(go.Scatter(x=max_data['new_time'], y=max_data[weather_variable], name='',
                                 fill=None, mode='lines', line_color='#D3D3D3', line=dict(width=0)))
        fig.add_trace(go.Scatter(x=min_data['new_time'], y=min_data[weather_variable], name='Max-Min',
                                 fill='tonexty', mode='lines', line_color='#D3D3D3', line=dict(width=0)))
        
        fig.add_trace(
            go.Scatter(x=mean_data['new_time'], y=mean_data[weather_variable], name='Mean', line=dict(dash='dot', width=2),
                       fill=None, mode='lines', line_color='#0047AB'))

        for year_id, year in enumerate(excl_years[::-1]):
            col_list = ['#96616B', '#52BE80', '#000000', 'firebrick']
            fig.add_trace(go.Scatter(x=observed_data.query('year==@year')['new_time'],
                                     y=observed_data.query('year==@year')[weather_variable],
                                     fill=None, name=str(year),
                                     line=dict(width=max(2 + year_id - 2, 2), color=col_list[year_id])))
        if ecm_data is not None:
            fig.add_trace(
                go.Scatter(x=ecm_data.query('new_time <@end_date')['new_time'], y=ecm_data.query('new_time <@end_date')[weather_variable],
                           name='ECMWF', line=dict(width=3, dash='dot'), fill=None, mode='lines', line_color='firebrick'))
        yield_an1 = str(round(self.country_yields.loc[excl_years[2]].values[0], 2))
        yield_an2 = str(round(self.country_yields.loc[excl_years[3]].values[0], 2))
        if (not weather_variable in ['soil-moisture', 'vegetation-vigor-index']) and (len(self.borders[weather_variable])>0):
            for bb in self.borders[weather_variable]:
                vrect_start = max(bb[0], observed_data.query('year==@year')['new_time'].min())
                vrect_end = min(bb[1], observed_data.query('year==@year')['new_time'].max())
                if vrect_start < vrect_end:
                    annotation_text = 'Negative impact on yield' if bb[2] == 'red' else 'Positive impact on yield'
                    fig.add_vrect(x0=vrect_start, x1=vrect_end, 
                                  annotation_text=annotation_text, annotation_position="top left", annotation_textangle=90,
                                  fillcolor=bb[2], opacity=0.1, line_width=0)
        title_text = f"<b>{self.region_name} - {weather_variable.title().replace('-', ' ')}</b><br><span style='font-size: 14px';>Pattern is similar to {excl_years[2]} and {excl_years[3]} when yield was {yield_an1} and {yield_an2}</span>"
        fig.update_layout(legend={'traceorder': 'reversed'}, title=title_text, hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),
                          xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d",
                                     linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                     tickfont=dict(size=12)),
                            yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                            plot_bgcolor='white')

        return fig
    
    
def all_historical_estimates():
    def get_historical_estimates(region: str, grains_class: str):
        df = get_yields(region, grains_class)
        for file in os.listdir("models/final/"):
            if file.__contains__(f"{grains_class}_{region}"):
                file_path = file
        forecasts_list = []
        for year_id, year in enumerate(df.index):
            forecasts_list.append(get_forecast(file_path, get_evolution=False, year=year, grains_class=grains_class))
        df['Estimate'] = forecasts_list
        region = get_translation(region)
        df.to_csv(os.path.join("support_files", "yield_evolution", f"{grains_class}_{region}.csv"))
    data_hist_path = os.path.join('models', "final")
    allfiles = [filename.split('_')[:2] for filename in listdir(data_hist_path) if (isfile(join(data_hist_path, filename)))]
    for file in allfiles:
        get_historical_estimates(file[1], file[0])

    
def get_regression_chart(region: str, grains_class: str):   
    region_translated = get_translation(region, reverse=True)
    for file in os.listdir("models/final/"):
        if file.__contains__(f"{grains_class}_{region_translated}"):
            file_path = file
    
    df = pd.read_csv(os.path.join("support_files", "yield_evolution", f"{grains_class}_{region}.csv"), index_col='Year')
    df.loc[max(df.index)+1] = [np.nan, get_forecast(file_path, get_evolution=False, year=max(df.index)+1, grains_class=grains_class)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Value'], name='Final Yield', line=dict(color='#702963', width=3)))
    fig.add_trace(go.Scatter(x=df.index, y=df['Estimate'], name='Model Yield', line=dict(color='#000000', width=3, dash='dash')))
    fig.update_layout(
            xaxis=dict(
                showline=True,
                showgrid=False,
                showticklabels=True,
                linecolor='rgb(204, 204, 204)',
                linewidth=2,
                ticks='outside',
                tickformat="%b %d",
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
            ),
            yaxis=dict(
                showgrid=True,
                zeroline=True,
                showline=True,
                showticklabels=True,
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
            ), font=dict(color='rgb(82, 82, 82)', family='Arial'),
            autosize=False,
            width=1300,
            title=f'{region} Historical {grains_class} Yields',
            height=500,
            showlegend=True,
            plot_bgcolor='white',
            hovermode='x unified',
        )
    return fig


def get_chart_region(region: str, grains_class = 'Winter Wheat'):
    hex_code = '#02386E' if grains_class == 'Winter Wheat' else '#2E8B57'	
    df1 = download_dataframe(creds=creds, filename=f"{grains_class}_yields_evolution.csv", parse_dates=['day_of_year'], index_col='day_of_year')
    df1_melted = df1.reset_index()
    df1_melted = df1_melted.melt(id_vars='day_of_year')
    fig = go.Figure()
    annotations=[]
    fig.add_trace(go.Scatter(x=df1.index, y=df1[region], name='Yield', line=dict(color=hex_code, width=4)))
    fig.add_trace(go.Scatter(
        x=[df1.index[0], df1.index[-1]],
        y=[df1[region][0], df1[region][-1]],
        mode='markers',
        marker=dict(color='#702963', size=4)
    ))
    fig.update_layout(font=dict(color='rgb(82, 82, 82)', family='Arial'),
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickformat="%b %d",
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True,
            showline=True,
            showticklabels=True,
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        autosize=False,
        width=1300,
        height=500,
        showlegend=False,
        plot_bgcolor='white',
        hovermode='x unified',
    )
    annotations.append(dict(xref='paper', x=0.05, y=df1[region][0],
                                    xanchor='right', yanchor='middle',
                                    text=f"{round(df1[region][0], 2)}Mt/Ha",
                                    font=dict(family='Arial',
                                            size=12),
                                    showarrow=False))
    annotations.append(dict(xref='paper', x=0.95, y=df1[region][-1],
                                    xanchor='left', yanchor='middle',
                                    text=f"{round(df1[region][-1], 2)}Mt/Ha",
                                    font=dict(family='Arial',
                                            size=12),
                                    showarrow=False))
    annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                                xanchor='left', yanchor='bottom',
                                text=f'{grains_class} {region} Yields Evolution',
                                font=dict(family='Arial',
                                            size=18,
                                            color='rgb(37,37,37)'),
                                showarrow=False))
    fig.update_layout(annotations=annotations)
    return fig


def get_regional_chart(production_df: pd.DataFrame, region: str, hex_code='#702963'):
        sub_df = production_df.query('macro == @region')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_df['day_of_year'], y=sub_df['yield'], name='Final Yield', line=dict(color=hex_code, width=3)))
        
        fig.add_trace(go.Scatter(
            x=[sub_df['day_of_year'].iloc[0], sub_df['day_of_year'].iloc[-1]],
            y=[sub_df['yield'].iloc[0], sub_df['yield'].iloc[-1]],
            mode='markers',
            marker=dict(color='#702963', size=4)
        ))
        annotations=[]
        annotations.append(dict(xref='paper', x=0.05, y=sub_df['yield'].iloc[0],
                                        xanchor='right', yanchor='middle',
                                        text=f"{round(sub_df['yield'].iloc[0], 2)}Mt/Ha",
                                        font=dict(family='Arial',
                                                size=12),
                                        showarrow=False))
        annotations.append(dict(xref='paper', x=0.95, y=sub_df['yield'].iloc[-1],
                                        xanchor='left', yanchor='middle',
                                        text=f"{round(sub_df['yield'].iloc[-1], 2)}Mt/Ha",
                                        font=dict(family='Arial',
                                                size=12),
                                        showarrow=False))
        annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.05,
                                    xanchor='left', yanchor='bottom',
                                    text=f'{region} Yields Evolution - Current Year',
                                    font=dict(family='Arial',
                                                size=18,
                                                color='rgb(37,37,37)'),
                                    showarrow=False))
        fig.update_layout(
                xaxis=dict(
                    showline=True,
                    showgrid=False,
                    showticklabels=True,
                    linecolor='rgb(204, 204, 204)',
                    linewidth=2,
                    ticks='outside',
                    tickformat="%b %d",
                    tickfont=dict(
                        family='Arial',
                        size=12,
                        color='rgb(82, 82, 82)',
                    ),
                ),
                yaxis=dict(
                    showgrid=True,
                    zeroline=True,
                    showline=True,
                    showticklabels=True,
                    tickfont=dict(
                        family='Arial',
                        size=12,
                        color='rgb(82, 82, 82)',
                    ),
                ),
                autosize=False,
                width=1300,
                height=500,
                showlegend=False,
                plot_bgcolor='white',
                hovermode='x unified',
                annotations=annotations
            )

        return fig
    
    
def deviation_charts():
    def get_deviation_chart(variable, period):
        sub_weather_deviation = weather_deviation.query('variable == @variable & period == @period')
        sub_weather_deviation = sub_weather_deviation.sort_values(by='ratio')

        fig = px.bar(sub_weather_deviation, x='region_4', y='ratio', color='region_3',
                    color_discrete_sequence=px.colors.qualitative.Dark2,
                    category_orders={"region_3": ["South", "Central", "Volga", "Ural","Siberia", "North-Western"]}, labels={'ratio':'', 'region_3':'Region','region_4':''})

        fig.update_layout(title=f'{variable.replace("-", " ").title()} - Last {period} vs Historical Average', hovermode="x unified",
                          font=dict(color='rgb(82, 82, 82)', family='Arial'),
                          width=1300,height=400,
                                xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d",
                                            linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                            tickfont=dict(size=12)),
                                    yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12), tickformat=".1%"),
                                    plot_bgcolor='white')
        return fig
    weather_deviation = download_dataframe(creds=creds, filename="russia_weather_vs_normal.csv")
    return get_deviation_chart('daily-precipitation', 7), get_deviation_chart('daily-precipitation', 30),get_deviation_chart('vegetation-vigor-index', 7), get_deviation_chart('vegetation-vigor-index', 30)


def get_progress_chart(df_all: pd.DataFrame, region:str, commodity:str, variable:str):
    last_year = df_all['year'].max()
    temp = df_all.query('region==@region & commodity==@commodity & variable==@variable').sort_values(by=['year', 'date_unified'])
    if variable == 'yield':
        temp['value'] = temp['value'] /10
    fig = px.line(temp.query('year<@last_year-1'), x="date_unified", y="value",
                    color='year', title = f"{commodity.capitalize()} {variable.capitalize()} Progress, {region}",
                    color_discrete_sequence=px.colors.qualitative.Bold, 
                    labels={"value": "", 'date_unified': '', 'year':'Year'}
                    )

    fig.update_traces(line=dict(width=1))
    fig.add_trace(
        go.Scatter(x=temp.query('year==@last_year-1')['date_unified'], y=temp.query('year==@last_year-1')['value'],
                    fill=None, mode='lines', name=str(last_year-1),
                    text=str(last_year-1), line=dict(color='black', width=2)))
    fig.add_trace(
        go.Scatter(x=temp.query('year==@last_year')['date_unified'], y=temp.query('year==@last_year')['value'],
                    fill=None, mode='lines+markers', name=str(last_year),
                    text=str(last_year), line=dict(color='firebrick', width=4)))
    
    fig.update_layout(hovermode="x unified", plot_bgcolor='white', font=dict(color='rgb(82, 82, 82)', family='Arial'), width=1300,height=500,
                    xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d", linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside', tickfont=dict(size=12)),
                    yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),)
    return fig



if __name__ == '__main__':
    all_historical_estimates()