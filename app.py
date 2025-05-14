from shiny import App, render, ui, reactive
import pandas as pd
from io import StringIO
import pyodide.http
import matplotlib
import plotly.express as px
from shinywidgets import render_widget  
from shinywidgets import output_widget, render_widget  

app_ui = ui.page_fluid(
    ui.output_ui("Countries_from_data"),
    ui.output_ui("datasets_from_data"),
    ui.output_ui("variables_filtered_dataset"),
    ui.output_ui("slider_years_values_from_data"),
    #ui.output_plot("plot_timeseries"),
    output_widget("plot_timeseries"),
    ui.output_table("table_all_data_with_year_from_slider")
)

def server(input, output, session):
    # done for you - reactive data variables
    global deaths_df
    global columns_dataset_df
    
    deaths_df = reactive.value(pd.DataFrame({}))
    columns_dataset_df = reactive.value(pd.DataFrame({}))

    async def parsed_data_from_url():
        # done for you - get online data
        global deaths_df
        file_url = "https://raw.githubusercontent.com/drpawelo/data/main/health/OCED_simplified.csv"
        response = await pyodide.http.pyfetch(file_url) # load file
        data = await response.string() # make it a string
        loaded_df = pd.read_csv(StringIO(data)) # read string as csv
        return loaded_df
    
    #read csv with map variable names to datset type
    async def parsed_data_from_url_2():
        # done for you - get online data
        global columns_dataset_df
        file_url = "https://raw.githubusercontent.com/simonpcastillo/dshsc_term3_python/refs/heads/main/data/columns_dataset.csv"
        response = await pyodide.http.pyfetch(file_url) # load file
        data = await response.string() # make it a string
        columns_dataset_df = pd.read_csv(StringIO(data)) # read string as csv
        return columns_dataset_df
        
    # here reactive.Effect means that the function is ran once, at the beginning.
    @reactive.Effect 
    async def refreshData():
        global deaths_df
        global columns_dataset_df
        columns_dataset_df
        data_so_far = deaths_df.get()
        if data_so_far.empty == True:
            print("started loading online data")
            deaths_df.set(await parsed_data_from_url())
            columns_dataset_df.set(await parsed_data_from_url_2())
            print("finished loading online data")
        else:
            print("online data was already loaded")

    @output
    @render.ui
    def Countries_from_data():
        global deaths_df
        loaded_df = deaths_df.get()

        # get unique countries
        unique_countries = sorted(list(set(loaded_df['country'])))
        country_dict = dict(zip(unique_countries, unique_countries))
    
        return ui.input_selectize("selected_countries", "Select country(ies):", country_dict, multiple=True)
    
    @output
    @render.ui
    def datasets_from_data():
        global columns_dataset_df
        columns_dataset_df = columns_dataset_df
        list_columns = list(columns_dataset_df['health_dataset'])
        list_columns_dict = dict(zip(list_columns,list_columns))
        return ui.input_selectize("datasets_included", "Select dataset:", list_columns_dict )

    @output
    @render.ui
    async def variables_filtered_dataset():
        global columns_dataset_df
        columns_dataset_df = columns_dataset_df
        list_variables = list(columns_dataset_df[columns_dataset_df['health_dataset'].isin([input.datasets_included()])]['column'])
        list_variables_dict = dict(zip(list_variables,list_variables))
        return ui.input_select("variable_to_plot", "Select variable:", list_variables_dict)
        
    
    @output
    @render.ui
    def slider_years_values_from_data():
        global deaths_df
        loaded_df = deaths_df.get()
        minimum_year = min(loaded_df.year.unique())
        maximum_year = max(loaded_df.year.unique())
        return ui.input_slider("slider_years_2", "Year", minimum_year, maximum_year, maximum_year)

    @output
    @render_widget 
    async def plot_timeseries():
        global deaths_df
        loaded_df = deaths_df.get()
        selected_year = input.slider_years_2()
        selected_countries = input.selected_countries()
        var_plot = input.variable_to_plot()
        filtered_df = loaded_df[(loaded_df['country'].isin(selected_countries)) & (loaded_df['year'] <=
 selected_year)]

        fig = px.line(filtered_df, 
                      x = "year", 
                      y = var_plot, 
                      color = 'country',
                     markers = True).update_traces(textposition="bottom right")
        return fig

    
    
    @output
    @render.table
    def table_all_data_with_year_from_slider():
        global deaths_df
        loaded_df = deaths_df.get()
        selected_year = input.slider_years_2()
        selected_countries = input.selected_countries()
        var_plot = input.variable_to_plot()
        filtered_df = loaded_df[(loaded_df['country'].isin(selected_countries)) & (loaded_df['year'] <= selected_year)]
        summarised_df = filtered_df[['country', var_plot]].groupby("country").mean()
        return summarised_df
        
app = App(app_ui, server)
