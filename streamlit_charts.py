import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
pd.options.mode.chained_assignment = None


class Weather_Report:
    def __init__(self, weather: pd.DataFrame, country_yields: pd.DataFrame, region_name: str):
        self.region_name = region_name
        self.country_yields = country_yields
        self.weather = weather

    def get_weather_analytics(self, weather_variable: str, start_date: str, end_date: str):
        start_date, end_date = pd.Timestamp(start_date), pd.Timestamp(end_date)
        start_date, end_date = pd.Timestamp(2020, start_date.month, start_date.day), pd.Timestamp(2020, end_date.month, end_date.day)
        
        y_df = self.country_yields
        y_df.set_index('year', inplace=True)

        x_df = self.weather[self.weather['year'].isin(y_df.index)]
        last_year = x_df['year'].max()
        max_last_date = x_df.query('year==@last_year')['unified_date'].max()
            
        boundary1, boundary2 = min(max_last_date, start_date), min(max_last_date, end_date)
        if boundary1 != boundary2:
            x_df = x_df.query('unified_date>=@boundary1 & unified_date<=@boundary2')
            x_df = x_df.groupby(['year'], as_index=False)['value'].mean()

            x_df = x_df.merge(y_df, left_on='year', right_index=True)
            x_df[['value', 'yield']] = x_df[['value', 'yield']].diff()
            x_df = x_df.dropna()
 
            fig = px.scatter(x_df.query('year<@last_year'), x='value', y='yield', text=x_df.query('year<@last_year')['year'],
                                trendline="ols")
            fig.update_traces(textposition='top center', marker=dict(color='#5D69B1', size=6),
                                textfont=dict(color='#E58606'))
            fig.add_trace(go.Scatter(x=[x_df.query('year==@last_year')['value'].values[0]], y=[0],
                                    showlegend=False, text=str(last_year), mode='markers', marker=dict(color='#FF0000', size=8)))

            model = px.get_trendline_results(fig)
            rsq = str(round(model.iloc[0]["px_fit_results"].rsquared, 3) * 100)[:4]
            title_text = f"<b>{self.region_name} Yield vs Avg {weather_variable.title().replace('-', ' ')}, YoY - From {boundary1.strftime('%b %d')} To {boundary2.strftime('%b %d')}</b>"
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
        start_date, end_date = pd.Timestamp(2020, start_date.month, start_date.day), pd.Timestamp(2020, end_date.month, end_date.day)
        
        def get_analogs(weather_variable: str, last_year: int, max_last_date):
            boundary = min(max_last_date, end_date)
            analogs_df = pd.concat([observed_data, ecm_data])

            analogs_df = analogs_df.query('unified_date == @boundary')
            
            analogs_df['value'] = abs(analogs_df['value'] -
                        analogs_df.query('year==@last_year')['value'].values[0])
            analogs_df['value'] = abs(analogs_df['value'] -
                                                analogs_df.query('year==@last_year')['value'].values[0])
            analogs_df = analogs_df[analogs_df['year'].isin(self.country_yields['year'])]
            first_analog, second_analog = analogs_df.sort_values(by='value')['year'][1:3].to_list()    
            return [last_year, last_year - 1] + list({first_analog, second_analog})

        observed_data = self.weather[self.weather['date'] < pd.Timestamp.today()]
        ecm_data = self.weather[self.weather['date'] >= pd.Timestamp.today()]
        observed_data = observed_data.query('unified_date>=@start_date & unified_date<=@end_date')
        ecm_data = ecm_data.query('unified_date>=@start_date & unified_date<=@end_date')
        
        last_year = self.weather['year'].max()
        max_last_date = self.weather.query('year==@last_year')['unified_date'].max()
        if weather_variable == 'daily-precipitation':
            observed_data = observed_data.groupby(['year', 'date', 'unified_date']).sum().groupby(
                level=0).cumsum().reset_index()
            if len(ecm_data)>0:
                ecm_data = ecm_data.groupby(['year', 'date', 'unified_date']).sum().groupby(
                    level=0).cumsum().reset_index()           
                if len(observed_data.query('year==@last_year')):
                    ecm_data[weather_variable] = ecm_data[weather_variable] + observed_data.query('year==@last_year')[weather_variable].max()

        excl_years = get_analogs(weather_variable, last_year, max_last_date)
        print(excl_years)
        max_data = observed_data.query('year<@last_year').groupby('unified_date', as_index=False)[
            ['unified_date', 'value']].max()
        min_data = observed_data.query('year<@last_year').groupby('unified_date', as_index=False)[
            ['unified_date', 'value']].min()
        mean_data = observed_data.query('year<@last_year').groupby('unified_date', as_index=False)[
            ['unified_date', 'value']].median()

        fig = px.line(observed_data[observed_data['year'].isin(excl_years)==False], x='unified_date', y='value',
                      color_discrete_sequence=px.colors.qualitative.G10, color='year', labels={'value':'', 'unified_date':'', 'year':''})
        fig.update_traces(visible="legendonly")
        fig.add_trace(go.Scatter(x=max_data['unified_date'], y=max_data['value'], name='',
                                 fill=None, mode='lines', line_color='#D3D3D3', line=dict(width=0)))
        fig.add_trace(go.Scatter(x=min_data['unified_date'], y=min_data['value'], name='Max-Min',
                                 fill='tonexty', mode='lines', line_color='#D3D3D3', line=dict(width=0)))
        
        fig.add_trace(
            go.Scatter(x=mean_data['unified_date'], y=mean_data['value'], name='Mean', line=dict(dash='dot', width=2),
                       fill=None, mode='lines', line_color='#0047AB'))

        for year_id, year in enumerate(excl_years[::-1]):
            col_list = ['#96616B', '#52BE80', '#000000', 'firebrick']
            fig.add_trace(go.Scatter(x=observed_data.query('year==@year')['unified_date'],
                                     y=observed_data.query('year==@year')['value'],
                                     fill=None, name=str(year),
                                     line=dict(width=max(2 + year_id - 2, 2), color=col_list[year_id])))
        if len(ecm_data)>0:
            fig.add_trace(
                go.Scatter(x=ecm_data.query('unified_date <@end_date')['unified_date'], y=ecm_data.query('unified_date <@end_date')['value'],
                           name='ECMWF', line=dict(width=3, dash='dot'), fill=None, mode='lines', line_color='firebrick'))
        yield_an1 = str(round(self.country_yields.query('year == @excl_years[2]')['yield'].values[0], 2))
        yield_an2 = str(round(self.country_yields.query('year == @excl_years[3]')['yield'].values[0], 2))

        title_text = f"<b>{self.region_name} - {weather_variable.title().replace('-', ' ')}</b><br><span style='font-size: 14px';>Pattern is similar to {excl_years[2]} and {excl_years[3]} when yield was {yield_an1} and {yield_an2}</span>"
        fig.update_layout(legend={'traceorder': 'reversed'}, title=title_text, hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),
                          xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d",
                                     linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                     tickfont=dict(size=12)),
                            yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                            plot_bgcolor='white')

        return fig
    
    
def yields_history(yields_df:pd.DataFrame, state: str):
    yields_df = yields_df.groupby(['year'], as_index=False)['yield'].mean()
    fig = px.line(yields_df, x="year", y="yield", labels={'yield':'', 'year':""})
    fig.update_layout(title=f'{state} - Historical Wheat Yields', hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),
                        xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d",
                                    linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                    tickfont=dict(size=12)),
                        yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                        plot_bgcolor='white')
    return fig

# if __name__ == '__main__':
#     all_historical_estimates()