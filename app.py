from shiny import App, render, ui, reactive
import pandas as pd
from io import StringIO
import pyodide.http
import matplotlib
import plotly.express as px
from shinywidgets import render_widget  
from shinywidgets import output_widget, render_widget  


def highlight_min_max(value):
    is_max = value == value.max()
    is_min = value == value.min()
    return [
        "background-color: yellow;" if max_ else
        "background-color: lightgray;" if min_ else ""
        for min_, max_ in zip(is_min, is_max)
    ]

app_ui = ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.panel_title("Worldwide time series of healthcare utilisation", "Browser Tab Title"),
                ui.output_ui("Countries_from_data"),
                ui.output_ui("datasets_from_data"),
                ui.output_ui("variables_filtered_dataset"),
                ui.output_ui("slider_years_values_from_data"),
                ui.markdown(
        """
        **Data source:**
        OECD (Organisation for Economic Co-operation and Development) in the OECD Data Explorer[https://data-explorer.oecd.org/].
        """),
            ),
                ui.markdown(
                """
                **(1) Temporal trends.**
                """),
            output_widget("plot_timeseries"),
            ui.markdown(
                """
                **(2) Summary table, grouped by country, over time.**
                """),
            ui.input_checkbox("highlight", "Highlight min/max values."),
            ui.output_table("table_all_data_with_year_from_slider"),
            ui.panel_conditional(
                "input.highlight",
                ui.panel_absolute(
                    "Yellow is maximum, grey is minimum.",
                    bottom="6px",
                    right="6px",
                    class_="p-1 bg-light border",
                ),
            ),
            class_="p-3",
        )
)

#################
# Server

def server(input, output, session):
    global deaths_df
    
    deaths_df = reactive.value(pd.DataFrame({}))

    #read datasets: compiled from healthcare utilisation
    async def parsed_data_from_url():
        global deaths_df
        file_url = "https://raw.githubusercontent.com/drpawelo/data/main/health/OCED_simplified.csv"
        response = await pyodide.http.pyfetch(file_url) 
        data = await response.string() 
        loaded_df = pd.read_csv(StringIO(data)) 
        return loaded_df

    #load data    
    @reactive.Effect 
    async def refreshData():
        global deaths_df
        
        data_so_far = deaths_df.get()
        if data_so_far.empty == True:
            print("started loading online data")
            deaths_df.set(await parsed_data_from_url())
            print("finished loading online data")
        else:
            print("online data was already loaded")

    #countries selection
    @output
    @render.ui
    def Countries_from_data():
        global deaths_df
        loaded_df = deaths_df.get()

        # get unique countries
        unique_countries = sorted(list(set(loaded_df['country'])))
        country_dict = dict(zip(unique_countries, unique_countries))
    
        return ui.input_selectize(
            "selected_countries", 
            "Select country(ies):", 
            country_dict, 
            multiple=True
        )
    
    #datasets selection. This helps to narrow down the type of variables
    @output
    @render.ui
    def datasets_from_data():
        list_datasets = [
            'Immunisation',
            'Consultations',
            'Diagnostic exams',
            'Healthcare utilisation',
            'Hospital aggregates',
            'Screening',
            'Average length of stay',
            'Hospital discharges',
            'Waiting times'
        ]
        return ui.input_selectize(
            "datasets_included", 
            "Select dataset:", 
            list_datasets, 
            multiple=True
        )

    #variable selection
    @output
    @render.ui
    async def variables_filtered_dataset():
        global var_dataset_dict
        #creates a dictionary with name_of_the_dataset:variables
        var_dataset_dict = {
             'Immunisation': ['Immunisation: Hepatitis B_% of children immunised','Immunisation: Influenza_% of population aged 65 years and over','Immunisation: Diphtheria, Tetanus, Pertussis_% of children immunised','Immunisation: Measles_% of children immunised'],
             'Diagnostic exams' : ['Computed Tomography exams, total_Number','Computed Tomography exams, total_Per 1 000 population','Computed Tomography exams, total_Per scanner','Magnetic Resonance Imaging exams, total_Number','Magnetic Resonance Imaging exams, total_Per 1 000 population','Magnetic Resonance Imaging exams, total_Per scanner','Computed Tomography exams, in hospitals_Number','Computed Tomography exams, in hospitals_Per 1 000 population','Computed Tomography exams, in hospitals_Per scanner','Computed Tomography exams, in ambulatory care_Number','Computed Tomography exams, in ambulatory care_Per 1 000 population','Computed Tomography exams, in ambulatory care_Per scanner','Magnetic Resonance Imaging exams, in hospitals_Number','Magnetic Resonance Imaging exams, in hospitals_Per 1 000 population','Magnetic Resonance Imaging exams, in hospitals_Per scanner','Magnetic Resonance Imaging exams, in ambulatory care_Number','Magnetic Resonance Imaging exams, in ambulatory care_Per 1 000 population','Magnetic Resonance Imaging exams, in ambulatory care_Per scanner'],
             'Hospital aggregates' : ['Curative care bed-days_Number per capita','Curative care occupancy rate_% of available beds'],
             'Screening' : ['Cervical cancer screening, programme data_% of females aged 20-69 screened','Cervical cancer screening, survey data_% of females aged 20-69 screened','Breast cancer screening, programme data_% of females aged 50-69 screened','Breast cancer screening, survey data_% of females aged 50-69 screened','Colorectal cancer screening, programme data_% of population aged 50-74 screened','Colorectal cancer screening, survey data_% of population aged 50-74 screened','Colorectal cancer screening, programme data_% of females aged 50-74 screened','Colorectal cancer screening, survey data_% of males aged 50-74 screened','Colorectal cancer screening, survey data_% of females aged 50-74 screened','Colorectal cancer screening, programme data_% of males aged 50-74 screened'],
             'Average length of stay' : ['Infectious and parasitic diseases_Number','Infectious and parasitic diseases_Per 100 000 population','Intestinal infectious diseases except diarrhoea_Number','Intestinal infectious diseases except diarrhoea_Per 100 000 population','Diarrhoea and gastroenteritis of presumed infectious origin_Number','Diarrhoea and gastroenteritis of presumed infectious origin_Per 100 000 population','Tuberculosis_Number','Tuberculosis_Per 100 000 population','Septicaemia_Number','Septicaemia_Per 100 000 population','Human immunodeficiency virus (HIV) disease_Number','Human immunodeficiency virus (HIV) disease_Per 100 000 population','Other infectious and parasitic diseases_Number','Other infectious and parasitic diseases_Per 100 000 population'],
             'Waiting times' : ['Knee replacement_Waiting times from specialist assessment to treatment: Median (days)','Prostatectomy_Waiting times from specialist assessment to treatment: Mean (days)','Cataract surgery_Waiting times of patients on the list: % of all patients waiting more than 3 months','Knee replacement_Waiting times of patients on the list: Mean (days)','Cataract surgery_Waiting times from specialist assessment to treatment: Median (days)','Knee replacement_Waiting times of patients on the list: % of all patients waiting more than 3 months','Prostatectomy_Waiting times of patients on the list: Mean (days)','Prostatectomy_Waiting times from specialist assessment to treatment: Median (days)','Knee replacement_Waiting times from specialist assessment to treatment: Mean (days)','Hip replacement (total and partial_ including the revision of hip replacement)_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Coronary bypass_Waiting times of patients on the list: Median (days)','Cataract surgery_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Percutaneous transluminal coronary angioplasty (PTCA)_Waiting times of patients on the list: % of all patients waiting more than 3 months','Knee replacement_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Hip replacement (total and partial_ including the revision of hip replacement)_Waiting times of patients on the list: Median (days)','Coronary bypass_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Cataract surgery_Waiting times from specialist assessment to treatment: Mean (days)','Coronary bypass_Waiting times from specialist assessment to treatment: Median (days)','Hysterectomy_Waiting times of patients on the list: % of all patients waiting more than 3 months','Hysterectomy_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Hip replacement (total and partial, including the revision of hip replacement)_Waiting times from specialist assessment to treatment: Median (days)','Hip replacement (total and partial, including the revision of hip replacement)_Waiting times of patients on the list: Mean (days)','Percutaneous transluminal coronary angioplasty (PTCA),Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Cataract surgery_Waiting times of patients on the list: Mean (days)','Hip replacement (total and partial_ including the revision of hip replacement)_Waiting times from specialist assessment to treatment: Mean (days)','Hysterectomy_Waiting times from specialist assessment to treatment: Mean (days)','Percutaneous transluminal coronary angioplasty (PTCA)_Waiting times of patients on the list: Mean (days)','Hysterectomy_Waiting times from specialist assessment to treatment: Median (days)','Cataract surgery_Waiting times of patients on the list: Median (days)','Percutaneous transluminal coronary angioplasty (PTCA)_Waiting times from specialist assessment to treatment: Mean (days)','Prostatectomy_Waiting times from specialist assessment to treatment: % of all patients waiting more than 3 months','Knee replacement_Waiting times of patients on the list: Median (days)','Coronary bypass_Waiting times of patients on the list: % of all patients waiting more than 3 months','Hip replacement (total and partial_ including the revision of hip replacement)_Waiting times of patients on the list: % of all patients waiting more than 3 months','Coronary bypass_Waiting times from specialist assessment to treatment: Mean (days)','Coronary bypass_Waiting times of patients on the list: Mean (days)','Percutaneous transluminal coronary angioplasty (PTCA)_Waiting times from specialist assessment to treatment: Median (days)','Percutaneous transluminal coronary angioplasty (PTCA)_Waiting times of patients on the list: Median (days)','Hysterectomy_Waiting times of patients on the list: Mean (days)','Prostatectomy_Waiting times of patients on the list: Median (days)','Hysterectomy_Waiting times of patients on the list: Median (days)','Prostatectomy_Waiting times of patients on the list: % of all patients waiting more than 3 months'],
             'Healthcare utilisation' : ['All causes_Days','Infectious and parasitic diseases_Days','Intestinal infectious diseases except diarrhoea_Days','Diarrhoea and gastroenteritis of presumed infectious origin_Days','Tuberculosis_Days','Septicaemia_Days','Human immunodeficiency virus (HIV) disease_Days','Other infectious and parasitic diseases_Days','Neoplasms_Days','Malignant neoplasm of colon_ rectum and anus_Days','Malignant neoplasm of trachea_ bronchus and lung_Days','Malignant neoplasm of skin_Days','Malignant neoplasm of breast_Days','Malignant neoplasm of uterus_Days','Malignant neoplasm of ovary_Days','Malignant neoplasm of prostate_Days','Malignant neoplasm of bladder_Days','Other Malignant neoplasms_Days','Carcinoma in situ_Days','Benign neoplasm of colon_ rectum and anus_Days','Leiomyoma of uterus_Days','Other Benign neoplasms and neoplasms of uncertain or unknown behaviour_Days','Diseases of the blood and bloodforming organs_Days','Anaemias_Days','Other diseases of the blood and bloodforming organs_Days','Endocrine_ nutritional and metabolic diseases_Days','Diabetes mellitus_Days','Other endocrine_ nutritional and metabolic diseases_Days','Mental and behavioural disorders_Days','Dementia_Days','Mental and behavioural disorders due to alcohol_Days','Mental and behavioural disorders due to use of Other psychoactive substance_Days','Schizophrenia_ schizotypal and delusional disorders_Days','Mood (affective) disorders_Days','Other Mental and behavioural disorders_Days','Diseases of the nervous system_Days',"Alzheimer's disease_Days",'Multiple sclerosis_Days','Epilepsy_Days','Transient cerebral ischaemic attacks and related syndromes_Days','Other diseases of the nervous system_Days','Diseases of the eye and adnexa_Days','Cataract_Days','Other diseases of the eye and adnexa_Days','Diseases of the ear and mastoid process_Days','Diseases of the circulatory system_Days','Hypertensive diseases_Days','Angina pectoris_Days','Acute myocardial infarction_Days','Other ischaemic heart disease_Days','Pulmonary heart disease and diseases of Pulmonary circulation_Days','Conduction disorders and cardiac arrhythmias_Days','Heart failure_Days','Cerebrovascular diseases_Days','Atherosclerosis_Days','Varicose veins of lower extremities_Days','Other diseases of the circulatory system_Days','Diseases of the respiratory system_Days','Acute upper respiratory infections and influenza_Days','Pneumonia_Days','Other acute lower respiratory infections_Days','Chronic diseases of tonsils and adenoids_Days','Other diseases of upper respiratory tract_Days','Chronic obstructive Pulmonary disease and bronchiectasis_Days','Asthma_Days','Other diseases of the respiratory system_Days','Diseases of the digestive system_Days','Disorders of teeth and supporting structures_Days','Other diseases of oral cavity_ salivary glands and jaws_Days','Diseases of oesophagus_Days','Peptic ulcer_Days','Dyspepsia and Other diseases of stomach and duodenum_Days','Diseases of appendix_Days','Inguinal hernia_Days','Other abdominal hernia_Days',"Crohn's disease and ulcerative colitis_Days",'Other noninfective gastroenteritis and colitis_Days','Paralytic ileus and Intestinal obstruction without hernia_Days','Diverticular disease of intestine_Days','Diseases of anus and rectum_Days','Other diseases of intestine_Days','Alcoholic liver disease_Days','Other diseases of liver_Days','Cholelithiasis_Days','Other diseases of gall bladder and biliary tract_Days','Diseases of pancreas_Days','Other diseases of the digestive system_Days','Diseases of the skin and subcutaneous tissue_Days','Infections of the skin and subcutaneous tissue_Days','Dermatitis_ eczema and papulosquamous disorders_Days','Other diseases of the skin and subcutaneous tissue_Days','Diseases of musculoskeletal system and connective tissue_Days','Coxarthrosis (arthrosis of hip)_Days','Gonarthrosis (arthrosis of knee)_Days','Internal derangement of knee_Days','Other arthropathies_Days','Systemic connective tissue disorders_Days','Deforming dorsopathies and spondylopathies_Days','Intervertebral disc disorders_Days','Dorsalgia_Days','Soft tissue disorders_Days','Other disorders of the musculoskeletal system and connective tissue_Days','Diseases of the genitourinary system_Days','Glomerular and renal tubulo-interstitial diseases_Days','Renal failure_Days','Urolithiasis_Days','Other diseases of the urinary system_Days','Hyperplasia of prostate_Days','Other diseases of Male genital organs_Days','Disorders of breast_Days','Inflammatory diseases of Female pelvic organs_Days','Menstrual_ menopausal and Other Female genital conditions_Days','Other disorders of the genitourinary system_Days','Pregnancy_ childbirth and the puerperium_Days','Medical abortion_Days','Other pregnancy with abortive outcome_Days','Complications of pregnancy in the antenatal period_Days','Complications of pregnancy predominantly during labour and delivery_Days','Single spontaneous delivery_Days','Other delivery_Days','Complications predominantly related to the puerperium_Days','Other obstetric conditions_Days','Certain conditions originating in the perinatal period_Days','Disorders related to short gestation and low birthweight_Days','Other conditions originating in the perinatal period_Days','Congenital malformations_ deformations and chromosomal abnormalities_Days','Symptoms_ signs and abnormal clinical and laboratory findings_ n.e.c._Days','Pain in throat and chest_Days','Abdominal and pelvic Pain_Days','Unknown and unspecified causes of morbidity_Days','Other symptoms_ signs and abnormal clinical and laboratory findings_Days','Injury_ poisoning and other consequences of external causes_Days','Intracranial injury_Days','Other injuries to the head_Days','Fracture of forearm_Days','Fracture of femur_Days','Fracture of lower leg_ including ankle_Days','Other injuries_Days','Burns and corrosions_Days','Poisonings by drugs_ medicaments_ and biological substances and toxic effects_Days','Complications of Surgical and medical care_ n.e.c._Days','Sequelae of injuries_ of poisoning and of Other external causes_Days','Other and unspecified effects of external causes_Days','Factors influencing health status and contact with health services_Days','Medical observation and evaluation for suspected diseases and conditions_Days','Contraceptive management_Days','Liveborn infants according to place of birth_Days','Other medical care (including radiotherapy and chemotherapy sessions)_Days','Other factors influencing Health status and contact with Health services_Days'],
             'Consultations' : ['Dentists consultations (in all settings)_Number per capita','Doctors consultations (in all settings)_Number per capita'],
             'Hospital discharges': ["Neoplasms_Number","Neoplasms_Per 100 000 population","Malignant neoplasm of colon, rectum and anus_Number","Malignant neoplasm of colon, rectum and anus_Per 100 000 population","Malignant neoplasm of trachea, bronchus and lung_Number","Malignant neoplasm of trachea, bronchus and lung_Per 100 000 population","Malignant neoplasm of skin_Number","Malignant neoplasm of skin_Per 100 000 population","Malignant neoplasm of breast_Number","Malignant neoplasm of breast_Per 100 000 females","Malignant neoplasm of uterus_Number","Malignant neoplasm of uterus_Per 100 000 females","Malignant neoplasm of ovary_Number","Malignant neoplasm of ovary_Per 100 000 females","Malignant neoplasm of prostate_Number","Malignant neoplasm of prostate_Per 100 000 males","Malignant neoplasm of bladder_Number","Malignant neoplasm of bladder_Per 100 000 population","Other Malignant neoplasms_Number","Other Malignant neoplasms_Per 100 000 population","Carcinoma in situ_Number","Carcinoma in situ_Per 100 000 population","Benign neoplasm of colon, rectum and anus_Number","Benign neoplasm of colon, rectum and anus_Per 100 000 population","Leiomyoma of uterus_Number","Leiomyoma of uterus_Per 100 000 females","Other Benign neoplasms and neoplasms of uncertain or unknown behaviour_Number","Other Benign neoplasms and neoplasms of uncertain or unknown behaviour_Per 100 000 population","Diseases of the blood and bloodforming organs_Number","Diseases of the blood and bloodforming organs_Per 100 000 population","Anaemias_Number","Anaemias_Per 100 000 population","Other diseases of the blood and bloodforming organs_Number","Other diseases of the blood and bloodforming organs_Per 100 000 population","Endocrine, nutritional and metabolic diseases_Number","Endocrine, nutritional and metabolic diseases_Per 100 000 population","Diabetes mellitus_Number","Diabetes mellitus_Per 100 000 population","Other endocrine_ nutritional and metabolic diseases_Number","Other endocrine_ nutritional and metabolic diseases_Per 100 000 population","Mental and behavioural disorders_Number","Mental and behavioural disorders_Per 100 000 population","Dementia_Number","Dementia_Per 100 000 population","Mental and behavioural disorders due to alcohol_Number","Mental and behavioural disorders due to alcohol_Per 100 000 population","Mental and behavioural disorders due to use of Other psychoactive substance_Number","Mental and behavioural disorders due to use of Other psychoactive substance_Per 100 000 population","Schizophrenia, schizotypal and delusional disorders_Number","Schizophrenia, schizotypal and delusional disorders_Per 100 000 population","Mood (affective) disorders_Number","Mood (affective) disorders_Per 100 000 population","Other Mental and behavioural disorders_Number","Other Mental and behavioural disorders_Per 100 000 population","Diseases of the nervous system_Number","Diseases of the nervous system_Per 100 000 population","Alzheimer's disease_Number","Alzheimer's disease_Per 100 000 population","Multiple sclerosis_Number","Multiple sclerosis_Per 100 000 population","Epilepsy_Number","Epilepsy_Per 100 000 population","Transient cerebral ischaemic attacks and related syndromes_Number","Transient cerebral ischaemic attacks and related syndromes_Per 100 000 population","Other diseases of the nervous system_Number","Other diseases of the nervous system_Per 100 000 population","Diseases of the eye and adnexa_Number","Diseases of the eye and adnexa_Per 100 000 population","Cataract_Number","Cataract_Per 100 000 population","Other diseases of the eye and adnexa_Number","Other diseases of the eye and adnexa_Per 100 000 population","Diseases of the ear and mastoid process_Number","Diseases of the ear and mastoid process_Per 100 000 population","Diseases of the circulatory system_Number","Diseases of the circulatory system_Per 100 000 population","Hypertensive diseases_Number","Hypertensive diseases_Per 100 000 population","Angina pectoris_Number","Angina pectoris_Per 100 000 population","Acute myocardial infarction_Number","Acute myocardial infarction_Per 100 000 population","Other ischaemic heart disease_Number","Other ischaemic heart disease_Per 100 000 population","Pulmonary heart disease and diseases of Pulmonary circulation_Number","Pulmonary heart disease and diseases of Pulmonary circulation_Per 100 000 population","Conduction disorders and cardiac arrhythmias_Number","Conduction disorders and cardiac arrhythmias_Per 100 000 population","Heart failure_Number","Heart failure_Per 100 000 population","Cerebrovascular diseases_Number","Cerebrovascular diseases_Per 100 000 population","Atherosclerosis_Number","Atherosclerosis_Per 100 000 population","Varicose veins of lower extremities_Number","Varicose veins of lower extremities_Per 100 000 population","Other diseases of the circulatory system_Number","Other diseases of the circulatory system_Per 100 000 population","Diseases of the respiratory system_Number","Diseases of the respiratory system_Per 100 000 population","Acute upper respiratory infections and influenza_Number","Acute upper respiratory infections and influenza_Per 100 000 population","Pneumonia_Number","Pneumonia_Per 100 000 population","Other acute lower respiratory infections_Number","Other acute lower respiratory infections_Per 100 000 population","Chronic diseases of tonsils and adenoids_Number","Chronic diseases of tonsils and adenoids_Per 100 000 population","Other diseases of upper respiratory tract_Number","Other diseases of upper respiratory tract_Per 100 000 population","Chronic obstructive Pulmonary disease and bronchiectasis_Number","Chronic obstructive Pulmonary disease and bronchiectasis_Per 100 000 population","Asthma_Number","Asthma_Per 100 000 population","Other diseases of the respiratory system_Number","Other diseases of the respiratory system_Per 100 000 population","Diseases of the digestive system_Number","Diseases of the digestive system_Per 100 000 population","Disorders of teeth and supporting structures_Number","Disorders of teeth and supporting structures_Per 100 000 population","Other diseases of oral cavity_ salivary glands and jaws_Number","Other diseases of oral cavity_ salivary glands and jaws_Per 100 000 population","Diseases of oesophagus_Number","Diseases of oesophagus_Per 100 000 population","Peptic ulcer_Number","Peptic ulcer_Per 100 000 population","Dyspepsia and Other diseases of stomach and duodenum_Number","Dyspepsia and Other diseases of stomach and duodenum_Per 100 000 population","Diseases of appendix_Number","Diseases of appendix_Per 100 000 population","Inguinal hernia_Number","Inguinal hernia_Per 100 000 population","Other abdominal hernia_Number","Other abdominal hernia_Per 100 000 population","Crohn's disease and ulcerative colitis_Number","Crohn's disease and ulcerative colitis_Per 100 000 population","Other noninfective gastroenteritis and colitis_Number","Other noninfective gastroenteritis and colitis_Per 100 000 population","Paralytic ileus and Intestinal obstruction without hernia_Number","Paralytic ileus and Intestinal obstruction without hernia_Per 100 000 population","Diverticular disease of intestine_Number","Diverticular disease of intestine_Per 100 000 population","Diseases of anus and rectum_Number","Diseases of anus and rectum_Per 100 000 population","Other diseases of intestine_Number","Other diseases of intestine_Per 100 000 population","Alcoholic liver disease_Number","Alcoholic liver disease_Per 100 000 population","Other diseases of liver_Number","Other diseases of liver_Per 100 000 population","Cholelithiasis_Number","Cholelithiasis_Per 100 000 population","Other diseases of gall bladder and biliary tract_Number","Other diseases of gall bladder and biliary tract_Per 100 000 population","Diseases of pancreas_Number","Diseases of pancreas_Per 100 000 population","Other diseases of the digestive system_Number","Other diseases of the digestive system_Per 100 000 population","Diseases of the skin and subcutaneous tissue_Number","Diseases of the skin and subcutaneous tissue_Per 100 000 population","Infections of the skin and subcutaneous tissue_Number","Infections of the skin and subcutaneous tissue_Per 100 000 population","Dermatitis_ eczema and papulosquamous disorders_Number","Dermatitis_ eczema and papulosquamous disorders_Per 100 000 population","Other diseases of the skin and subcutaneous tissue_Number","Other diseases of the skin and subcutaneous tissue_Per 100 000 population","Diseases of musculoskeletal system and connective tissue_Number","Diseases of musculoskeletal system and connective tissue_Per 100 000 population","Coxarthrosis (arthrosis of hip)_Number","Coxarthrosis (arthrosis of hip)_Per 100 000 population","Gonarthrosis (arthrosis of knee)_Number","Gonarthrosis (arthrosis of knee)_Per 100 000 population","Internal derangement of knee_Number","Internal derangement of knee_Per 100 000 population","Other arthropathies_Number","Other arthropathies_Per 100 000 population","Systemic connective tissue disorders_Number","Systemic connective tissue disorders_Per 100 000 population","Deforming dorsopathies and spondylopathies_Number","Deforming dorsopathies and spondylopathies_Per 100 000 population","Intervertebral disc disorders_Number","Intervertebral disc disorders_Per 100 000 population","Dorsalgia_Number","Dorsalgia_Per 100 000 population","Soft tissue disorders_Number","Soft tissue disorders_Per 100 000 population","Other disorders of the musculoskeletal system and connective tissue_Number","Other disorders of the musculoskeletal system and connective tissue_Per 100 000 population","Diseases of the genitourinary system_Number","Diseases of the genitourinary system_Per 100 000 population","Glomerular and renal tubulo-interstitial diseases_Number","Glomerular and renal tubulo-interstitial diseases_Per 100 000 population","Renal failure_Number","Renal failure_Per 100 000 population","Urolithiasis_Number","Urolithiasis_Per 100 000 population","Other diseases of the urinary system_Number","Other diseases of the urinary system_Per 100 000 population","Hyperplasia of prostate_Number","Hyperplasia of prostate_Per 100 000 males","Other diseases of Male genital organs_Number","Other diseases of Male genital organs_Per 100 000 males","Disorders of breast_Number","Disorders of breast_Per 100 000 females","Inflammatory diseases of Female pelvic organs_Number","Inflammatory diseases of Female pelvic organs_Per 100 000 females","Menstrual_ menopausal and Other Female genital conditions_Number","Menstrual_ menopausal and Other Female genital conditions_Per 100 000 females","Other disorders of the genitourinary system_Number","Other disorders of the genitourinary system_Per 100 000 females","Pregnancy_ childbirth and the puerperium_Number","Pregnancy_ childbirth and the puerperium_Per 100 000 females","Medical abortion_Number","Medical abortion_Per 100 000 females","Other pregnancy with abortive outcome_Number","Other pregnancy with abortive outcome_Per 100 000 females","Complications of pregnancy in the antenatal period_Number","Complications of pregnancy in the antenatal period_Per 100 000 females","Complications of pregnancy predominantly during labour and delivery_Number","Complications of pregnancy predominantly during labour and delivery_Per 100 000 females","Single spontaneous delivery_Number","Single spontaneous delivery_Per 100 000 females","Other delivery_Number","Other delivery_Per 100 000 females","Complications predominantly related to the puerperium_Number","Complications predominantly related to the puerperium_Per 100 000 females","Other obstetric conditions_Number","Other obstetric conditions_Per 100 000 females","Certain conditions originating in the perinatal period_Number","Certain conditions originating in the perinatal period_Per 100 000 population","Disorders related to short gestation and low birthweight_Number","Disorders related to short gestation and low birthweight_Per 100 000 population","Other conditions originating in the perinatal period_Number","Other conditions originating in the perinatal period_Per 100 000 population","Congenital malformations_ deformations and chromosomal abnormalities_Number","Congenital malformations_ deformations and chromosomal abnormalities_Per 100 000 population","Symptoms, signs and abnormal clinical and laboratory findings, n.e.c._Number","Symptoms, signs and abnormal clinical and laboratory findings, n.e.c._Per 100 000 population","Pain in throat and chest_Number","Pain in throat and chest_Per 100 000 population","Abdominal and pelvic Pain_Number","Abdominal and pelvic Pain_Per 100 000 population","Unknown and unspecified causes of morbidity_Number","Unknown and unspecified causes of morbidity_Per 100 000 population","Other symptoms_ signs and abnormal clinical and laboratory findings_Number","Other symptoms_ signs and abnormal clinical and laboratory findings_Per 100 000 population","Injury_ poisoning and other consequences of external causes_Number","Injury_ poisoning and other consequences of external causes_Per 100 000 population","Intracranial injury_Number","Intracranial injury_Per 100 000 population","Other injuries to the head_Number","Other injuries to the head_Per 100 000 population","Fracture of forearm_Number","Fracture of forearm_Per 100 000 population","Fracture of femur_Number","Fracture of femur_Per 100 000 population","Fracture of lower leg_ including ankle_Number","Fracture of lower leg_ including ankle_Per 100 000 population","Other injuries_Number","Other injuries_Per 100 000 population","Burns and corrosions_Number","Burns and corrosions_Per 100 000 population","Poisonings by drugs_ medicaments_ and biological substances and toxic effects_Number","Poisonings by drugs_ medicaments_ and biological substances and toxic effects_Per 100 000 population","Complications of Surgical and medical care_ n.e.c._Number","Complications of Surgical and medical care_ n.e.c._Per 100 000 population","Sequelae of injuries_ of poisoning and of Other external causes_Number","Sequelae of injuries_ of poisoning and of Other external causes_Per 100 000 population","Other and unspecified effects of external causes_Number","Other and unspecified effects of external causes_Per 100 000 population","Factors influencing health status and contact with health services_Number","Factors influencing health status and contact with health services_Per 100 000 population","Medical observation and evaluation for suspected diseases and conditions_Number","Medical observation and evaluation for suspected diseases and conditions_Per 100 000 population","Contraceptive management_Number","Contraceptive management_Per 100 000 population","Liveborn infants according to place of birth_Number","Liveborn infants according to place of birth_Per 100 000 population","Other medical care (including radiotherapy and chemotherapy sessions)_Number","Other medical care (including radiotherapy and chemotherapy sessions)_Per 100 000 population","Other factors influencing Health status and contact with Health services_Number","Other factors influencing Health status and contact with Health services_Per 100 000 population","All causes_Number","All causes_Per 100 000 population","Cataract surgery_Number of day cases","Cataract surgery_Total number of procedures","Cataract surgery_Number of inpatient cases","Cataract surgery_Total procedures per 100 000 population","Cataract surgery_% performed as day cases","Cataract surgery_% performed as inpatient cases","Cataract surgery_Inpatient cases per 100 000 population","Cataract surgery_Day cases per 100 000 population","Tonsillectomy_Number of day cases","Tonsillectomy_Total number of procedures","Tonsillectomy_Number of inpatient cases","Tonsillectomy_Total procedures per 100 000 population","Tonsillectomy_% performed as day cases","Tonsillectomy_% performed as inpatient cases","Tonsillectomy_Inpatient cases per 100 000 population","Tonsillectomy_Day cases per 100 000 population","Transluminal coronary angioplasty_Number of inpatient cases","Transluminal coronary angioplasty_Inpatient cases per 100 000 population","Coronary artery bypass graft_Number of inpatient cases","Coronary artery bypass graft_Inpatient cases per 100 000 population","Appendectomy_Number of inpatient cases","Appendectomy_Inpatient cases per 100 000 population","Cholecystectomy_Number of day cases","Cholecystectomy_Total number of procedures","Cholecystectomy_Number of inpatient cases","Cholecystectomy_Total procedures per 100 000 population","Cholecystectomy_% performed as day cases","Cholecystectomy_% performed as inpatient cases","Cholecystectomy_Inpatient cases per 100 000 population","Cholecystectomy_Day cases per 100 000 population","Laparoscopic cholecystectomy_Number of day cases","Laparoscopic cholecystectomy_Total number of procedures","Laparoscopic cholecystectomy_Number of inpatient cases","Laparoscopic cholecystectomy_Total procedures per 100 000 population","Laparoscopic cholecystectomy_% performed as day cases","Laparoscopic cholecystectomy_% performed as inpatient cases","Laparoscopic cholecystectomy_Inpatient cases per 100 000 population","Laparoscopic cholecystectomy_Day cases per 100 000 population","Repair of inguinal hernia_Number of day cases","Repair of inguinal hernia_Total number of procedures","Repair of inguinal hernia_Number of inpatient cases","Repair of inguinal hernia_Total procedures per 100 000 population","Repair of inguinal hernia_% performed as day cases","Repair of inguinal hernia_% performed as inpatient cases","Repair of inguinal hernia_Inpatient cases per 100 000 population","Repair of inguinal hernia_Day cases per 100 000 population","Transurethral prostatectomy_Number of inpatient cases","Transurethral prostatectomy_Inpatient cases per 100 000 males","Open prostatectomy_Number of inpatient cases","Open prostatectomy_Inpatient cases per 100 000 males","Hysterectomy_Number of inpatient cases","Hysterectomy_Inpatient cases per 100 000 females","Caesarean section_Number of inpatient cases","Caesarean section_Inpatient cases per 100 000 females","Caesarean section_Total procedures per 1 000 live births","Hip replacement_Number of inpatient cases","Hip replacement_Inpatient cases per 100 000 population","Total knee replacement_Number of inpatient cases","Total knee replacement_Inpatient cases per 100 000 population","Partial excision of mammary gland_Number of inpatient cases","Partial excision of mammary gland_Inpatient cases per 100 000 females","Total mastectomy_Number of inpatient cases","Total mastectomy_Inpatient cases per 100 000 females","Partial excision of mammary gland_% performed as day cases","Curative care discharges_Per 100 000 population","Open prostatectomy_% performed as day cases","Inpatient care discharges (all hospitals)_Number","Open prostatectomy_% performed as inpatient cases","Partial excision of mammary gland_% performed as inpatient cases","Positron Emission Tomography (PET) exams_ total_Per scanner","Hip replacement_% performed as day cases","Hysterectomy_% performed as day cases","Curative care discharges_Number","Total knee replacement_Inpatient procedures per 1 000 population aged 65 years old and over","Stem cell transplantation_% performed as inpatient cases","Laparoscopic hysterectomy_% performed as day cases","Transluminal coronary angioplasty_% performed as day cases","Transurethral prostatectomy_% performed as day cases","Curative care bed-days_Number","Total knee replacement_% performed as inpatient cases","Stem cell transplantation_% performed as day cases","Inpatient care average length of stay (all hospitals)_Days","Positron Emission Tomography (PET) exams_ in ambulatory care_Per scanner","Coronary artery bypass graft_% performed as day cases","Hip replacement_% performed as inpatient cases","Inpatient care discharges (all hospitals)_Per 100 000 population","Appendectomy_% performed as inpatient cases","Hysterectomy_% performed as inpatient cases","Caesarean section_% performed as day cases","Coronary artery bypass graft_% performed as inpatient cases","Caesarean section_Inpatient procedures per 1 000 live births","Appendectomy_% performed as day cases","Laparoscopic appendectomy_% performed as day cases","Cataract surgery_% performed as outpatient cases","Caesarean section_% performed as inpatient cases","Total mastectomy_% performed as day cases","Total knee replacement_% performed as day cases","Transurethral prostatectomy_% performed as inpatient cases","Transluminal coronary angioplasty_% performed as inpatient cases","Total mastectomy_% performed as inpatient cases","Tonsillectomy_% performed as outpatient cases","Curative care average length of stay_Days","Hip replacement_Inpatient procedures per 1 000 population aged 65 years old and over","Laparoscopic repair of Inguinal hernia_% performed as day cases","Laparoscopic repair of Inguinal hernia_% performed as inpatient cases","Laparoscopic hysterectomy_% performed as inpatient cases","Laparoscopic appendectomy_% performed as inpatient cases","Positron Emission Tomography (PET) exams_ in hospitals_Per scanner","Coronary artery bypass graft_Day cases per 100 000 population","Laparoscopic appendectomy_Number of inpatient cases","Hysterectomy_Total procedures per 100 000 females","Transurethral prostatectomy_Number of day cases","Total knee replacement_Total procedures per 1000 population aged 65 years old and over","Appendectomy_Number of day cases","Laparoscopic hysterectomy_Total number of procedures","Hip replacement_Total procedures per 100 000 population","Transurethral prostatectomy_Total procedures per 100 000 males","Total mastectomy_Number of day cases","Stem cell transplantation_Number of inpatient cases","Appendectomy_Total procedures per 100 000 population","Caesarean section_Total number of procedures","Laparoscopic appendectomy_Total procedures per 100 000 population","Total mastectomy_Day cases per 100 000 females","Total knee replacement_Number of day cases","Laparoscopic appendectomy_Total number of procedures","Hip replacement_Day cases per 100 000 population","Laparoscopic hysterectomy_Number of inpatient cases","Positron Emission Tomography (PET) exams_ in hospitals_Number","Total knee replacement_Total procedures per 100 000 population","Transluminal coronary angioplasty_Day cases per 100 000 population","Open prostatectomy_Total procedures per 100 000 males","Cataract surgery_Outpatient cases per 100 000 population","Stem cell transplantation_Total procedures per 100 000 population","Positron Emission Tomography (PET) exams_ total_Per 1 000 population","Positron Emission Tomography (PET) exams_ in hospitals_Per 1 000 population","Laparoscopic repair of Inguinal hernia_Total number of procedures","Transluminal coronary angioplasty_Number of day cases","Caesarean section_Number of day cases","Laparoscopic appendectomy_Inpatient cases per 100 000 population","Laparoscopic hysterectomy_Day cases per 100 000 females","Coronary artery bypass graft_Total number of procedures","Cataract surgery_Number of outpatient cases","Caesarean section_Day cases per 100 000 females","Tonsillectomy_Number of outpatient cases","Caesarean section_Total procedures per 100 000 females","Hip replacement_Number of day cases","Transurethral prostatectomy_Day cases per 100 000 males","Caesarean section_Day cases procedures per 1 000 live births","Laparoscopic appendectomy_Day cases per 100 000 population","Positron Emission Tomography (PET) exams_ total_Number","Positron Emission Tomography (PET) exams_ in ambulatory care_Number","Total knee replacement_Day cases procedures per 1 000 population aged 65 years old and over","Laparoscopic repair of Inguinal hernia_Number of day cases","Transluminal coronary angioplasty_Total procedures per 100 000 population","Open prostatectomy_Total number of procedures","Partial excision of mammary gland_Total number of procedures","Transurethral prostatectomy_Total number of procedures","Total knee replacement_Day cases per 100 000 population","Stem cell transplantation_Number of day cases","Open prostatectomy_Day cases per 100 000 males","Hysterectomy_Number of day cases","Appendectomy_Day cases per 100 000 population","Hip replacement_Day cases procedures per 1 000 population aged 65 years old and over","Partial excision of mammary gland_Number of day cases","Total mastectomy_Total number of procedures","Laparoscopic repair of Inguinal hernia_Inpatient cases per 100 000 population","Partial excision of mammary gland_Total procedures per 100 000 females","Hip replacement_Total number of procedures","Total knee replacement_Total number of procedures","Hip replacement_Total procedures per 1 000 population aged 65 years old and over","Hysterectomy_Total number of procedures","Total mastectomy_Total procedures per 100 000 females","Stem cell transplantation_Day cases per 100 000 population","Appendectomy_Total number of procedures","Transluminal coronary angioplasty_Total number of procedures","Positron Emission Tomography (PET) exams_ in ambulatory care_Per 1 000 population","Partial excision of mammary gland_Day cases per 100 000 females","Open prostatectomy_Number of day cases","Coronary artery bypass graft_Total procedures per 100 000 population","Tonsillectomy_Outpatient cases per 100 000 population","Coronary artery bypass graft_Number of day cases","Laparoscopic appendectomy_Number of day cases","Laparoscopic repair of Inguinal hernia_Number of inpatient cases","Stem cell transplantation_Inpatient cases per 100 000 population","Laparoscopic repair of Inguinal hernia_Day cases per 100 000 population","Laparoscopic hysterectomy_Total procedures per 100 000 females","Stem cell transplantation_Total number of procedures","Laparoscopic hysterectomy_Inpatient cases per 100 000 females","Hysterectomy_Day cases per 100 000 females","Laparoscopic repair of Inguinal hernia_Total procedures per 100 000 population"]
         }

        #parse variables to a list. 
        list_variables = []
        to_keep = input.datasets_included()
        
        for key in to_keep:
            value = var_dataset_dict.get(key)
            if isinstance(value, list):
                list_variables.extend(value)
            elif value is not None:
                list_variables.append(value)
                
        list_variables_dict = dict(zip(list_variables,list_variables))
        
        return ui.input_select(
            "variable_to_plot", 
            "Select variable:", 
            list_variables_dict)
        
    #select max year. range of years comes from data
    @output
    @render.ui
    def slider_years_values_from_data():
        global deaths_df
        loaded_df = deaths_df.get()
        minimum_year = min(loaded_df.year.unique())
        maximum_year = max(loaded_df.year.unique())
        return ui.input_slider(
            "slider_years_2", 
            "Year", 
            minimum_year, 
            maximum_year,
            maximum_year
        )

    #main plot. lines and points. Filtered by user selection on side panel. 
    @output
    @render_widget 
    async def plot_timeseries():
        global deaths_df
        loaded_df = deaths_df.get()
        selected_year = input.slider_years_2()
        selected_countries = input.selected_countries()
        var_plot = input.variable_to_plot()
        if var_plot == None or selected_countries == None:
            return print("Please enter a value to display the table.")
        else:
            filtered_df = loaded_df[(loaded_df['country'].isin(selected_countries)) & (loaded_df['year'] <=
     selected_year)]
            filtered_df = filtered_df.sort_values("year") 
    
            fig = px.line(filtered_df, 
                            x = "year", 
                            y = var_plot, 
                            color = 'country',
                            markers = True).update_traces(
                textposition="bottom right").update_layout(
                plot_bgcolor='white',
                xaxis=dict(
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    gridcolor='lightgray'
                )
            )
            return fig

    
    #table output. averaged along the time window grouping by country
    @output
    @render.table
    def table_all_data_with_year_from_slider():
        global deaths_df
        loaded_df = deaths_df.get()
        selected_year = input.slider_years_2()
        if input.variable_to_plot() == None:
            return print("Please enter a value to display the table.")
        else:
            selected_countries = input.selected_countries()
            var_plot = input.variable_to_plot()
            filtered_df = loaded_df[(loaded_df['country'].isin(selected_countries)) & (loaded_df['year'] <= selected_year)]
            summarised_df = filtered_df[[var_plot, 'country']].groupby(['country'],as_index=False).mean(numeric_only=True)
            if not input.highlight():
                    return (
                        summarised_df
                        .style
                        .format(
                            {
                                var_plot:"{0:0.3f}",
                            }
                        )
                        .set_table_styles([
                        {'selector': 'td', 'props': [('text-align', 'right')]},
                        {'selector': 'th', 'props': [('text-align', 'right')]}  # Optional: header alignment
                    ])
                        .hide(axis="index")
        
                    )
            else:
                    return (
                    summarised_df
                        .style
                        .apply(highlight_min_max, subset=[var_plot])
                        .set_table_attributes(
                            'class="dataframe shiny-table table w-auto"'
                        )
                        .format(
                            {
                                var_plot:"{0:0.3f}",
                            }
                        )
                        .set_table_styles([
                        {'selector': 'td', 'props': [('text-align', 'right')]}, # table body
                        {'selector': 'th', 'props': [('text-align', 'right')]}  # table header
                    ])
                        .hide(axis="index")
                )

        
app = App(app_ui, server)
