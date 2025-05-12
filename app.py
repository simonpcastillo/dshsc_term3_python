from shiny import App, render, ui, reactive
import pandas as pd
from io import StringIO
import pyodide.http
import matplotlib

app_ui = ui.page_fluid(
    ui.output_ui("Countries_from_data"),
    ui.output_ui("slider_years_values_from_data"),
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
    
        return ui.input_select("Select", "Select from:", country_dict, multiple=True)
    
        
    
    @output
    @render.ui
    def slider_years_values_from_data():
        # these first two lines you'll need to put everywhere you are using the data. Then use the variable loaded_df
        global deaths_df
        loaded_df = deaths_df.get()
        
        # get values you need to make the inputs (slider boundaries, drop-down options, etc)
        minimum_year = min(loaded_df.year.unique())
        maximum_year = max(loaded_df.year.unique())
        # use those values:
        return ui.input_slider("slider_years_2", "Year - this one controlls the table below", minimum_year, maximum_year, maximum_year)
    
    # example table:
    @output
    @render.table
    def table_all_data_with_year_from_slider():
        # these first two lines you'll need to put everywhere you are using the data. Then use the variable loaded_df
        global deaths_df
        loaded_df = deaths_df.get()
        
        selected_year = input.slider_years_2()
        demo_countries = ['Ireland', 'India']
        demo_columns = ['country','Immunisation: Hepatitis B_% of children immunised']
        
        filtered_data = loaded_df[ (loaded_df['year'] == selected_year) & (loaded_df['country'].isin(demo_countries))].reindex()
        return filtered_data[demo_columns]
        
app = App(app_ui, server)
