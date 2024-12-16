import pandas as pd
import requests
import json
from datetime import datetime
import streamlit as st
from sqlalchemy import create_engine
import base64
import os

# Function to encode the background image in Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Add background image
background_image_path = "CT-Logo.jpg"  # Replace with your image file name
base64_image = get_base64_image(background_image_path)
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{base64_image}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Function to get EID
def get_eid():
    p = r'accounts.json'
    fp = open(p)
    res = json.load(fp)
    access_token = res['track3']['access_token']
    base_url = res['track3']['base_url']
    url = 'https://hst-api.wialon.com/wialon/ajax.html?svc=token/login&params={"token":"' + access_token + '"}'
    r = requests.post(url)
    data = json.loads(r.text)
    eid = data['eid']
    # Set the localization
    url2 = 'https://hst-api.wialon.com/wialon/ajax.html?svc=render/set_locale&params={"tzOffset":134228528,"language":"en","formatDate":"%E.%m.%Y %H:%M:%S"}&sid=' + eid
    r2 = requests.post(url2)
    return eid

# Function to fetch Eco Driving Report
def get_eco_driving_report(ID, FROM, TO, eco_template, eid):
    xl_url = r'https://hst-api.wialon.com/wialon/ajax.html?svc=report/export_result&params={"format":8,"compress":0}&sid=' + eid
    params = {
        "reportResourceId": 26749909,  # Replace with your resource ID
        "reportTemplateId": 8,
        "reportObjectId": int(ID),
        "reportObjectSecId": 0,
        "reportTemplate": eco_template,
        "interval": {
            "from": int(FROM.timestamp()),
            "to": int(TO.timestamp()),
            "flags": 0
        }
    }
    params = json.dumps(params, separators=(',', ':'))
    get_report_url = f'https://hst-api.wialon.com/wialon/ajax.html?svc=report/exec_report&params={params}&sid={eid}'
    requests.post(get_report_url)  # Trigger report execution

    r2 = requests.post(xl_url)  # Download report
    return r2.content

# Function to fetch Trip Report
def get_trip_report(ID, FROM, TO, template, eid):
    xl_url = r'https://hst-api.wialon.com/wialon/ajax.html?svc=report/export_result&params={"format":8,"compress":0}&sid=' + eid
    params = {
        "reportResourceId": 17082202,  # Replace with your resource ID
        "reportTemplateId": 0,
        "reportObjectId": int(ID),
        "reportObjectSecId": 0,
        "reportTemplate": template,
        "interval": {
            "from": int(FROM.timestamp()),
            "to": int(TO.timestamp()),
            "flags": 0
        }
    }
    params = json.dumps(params, separators=(',', ':'))
    get_report_url = f'https://hst-api.wialon.com/wialon/ajax.html?svc=report/exec_report&params={params}&sid={eid}'
    requests.post(get_report_url)  # Trigger report execution

    r2 = requests.post(xl_url)  # Download report
    return r2.content

# Streamlit UI components
st.title("Trips and Eco Driving Report Table")

# Get start and end datetime from the user
start_date = st.date_input("Start Date", datetime(2024, 12, 1))
end_date = st.date_input("End Date", datetime(2024, 12, 30))
start_datetime = datetime.combine(start_date, datetime.min.time())
end_datetime = datetime.combine(end_date, datetime.max.time())

if start_datetime >= end_datetime:
    st.error("Start date must be earlier than the end date. Please adjust the dates.")
    st.stop()

st.write(f"Fetching reports for the period: {start_datetime} to {end_datetime}")

# Define constants
group_name = 'Agility'
group_id = 28475360

# Eco Driving Template
eco_template = [{'id': 8,'n': '20cube - Eco Driving Per Fleet','ct': 'avl_unit_group','p': '{"descr":"","bind":{"avl_unit_group":[]}}','tbl': [{'n': 'unit_group_stats','l': 'Statistics','c': '','cl': '','cp': '','s': '["address_format","time_format","us_units","deviation"]','sl': '["Address","Time Format","Measure","Deviation"]','filter_order': [],'p': '{"address_format":"1178599424_10_5","time_format":"%E.%m.%Y_%H:%M:%S","us_units":0,"deviation":"30"}','sch': {'f1': 0,'f2': 0,'t1': 0,'t2': 0,'m': 0,'y': 0,'w': 0,'fl': 0},'f': 0},{'n': 'unit_group_ecodriving','l': 'Eco driving','c': '["violation_name","time_begin","time_end","location","location_end","mileage","violations_count","violation_value","avg_speed","max_speed","violation_mark","driver","violation_duration","violation_mileage"]','cl': '["Violation","Beginning","End","Initial location","Final location","Mileage","Count","Value","Avg speed","Max speed","Penalties","Driver","Violation duration","Violation mileage"]','cp': '[{},{},{},{},{},{},{},{},{},{},{},{},{},{}]','s': '','sl': '','filter_order': ['violation_group_name','violation_duration','show_all_trips','mileage','colors','custom_sensors_col','geozones_ex'],'p': '{"grouping":"{\\"type\\":\\"unit\\",\\"nested\\":{\\"type\\":\\"criterion\\"}}","violation_group_name":"*"}','sch': {'f1': 0,'f2': 0,'t1': 0,'t2': 0,'m': 0,'y': 0,'w': 0,'fl': 0},'f': 4198672}],'bsfl': {'ct': 1683207805, 'mt': 1721114533}}]


# Trip Template
group_trips_stops_parkings_report_template = {"id":0,"n":"Group Trips Stops and Parkings Report","ct":"avl_unit_group","p":"{\"descr\":\"\",\"bind\":{\"avl_unit_group\":[]}}","tbl":[{"n":"unit_group_stats","l":"Statistics","c":"","cl":"","cp":"","s":"[\"address_format\",\"time_format\",\"us_units\"]","sl":"[\"Address\",\"Time Format\",\"Measure\"]","filter_order":[],"p":"{\"address_format\":\"1178599424_10_5\",\"time_format\":\"%E.%m.%Y_%H:%M:%S\",\"us_units\":0}","sch":{"f1":0,"f2":0,"t1":0,"t2":0,"m":0,"y":0,"w":0,"fl":0},"f":0},{"n":"unit_group_trips","l":"Trips","c":"[\"time_begin\",\"time_end\",\"location_begin\",\"location_end\",\"coord_begin\",\"coord_end\",\"duration\",\"duration_ival\",\"eh_duration\",\"mileage\",\"correct_mileage\",\"absolute_mileage_begin\",\"absolute_mileage_end\",\"avg_speed\",\"max_speed\",\"driver\",\"trips_count\",\"fuel_consumption_all\",\"fuel_consumption_fls\",\"fuel_level_begin\",\"fuel_level_end\",\"fuel_level_max\",\"fuel_level_min\"]","cl":"[\"Beginning\",\"End\",\"Initial location\",\"Final location\",\"Initial coordinates\",\"Final coordinates\",\"Duration\",\"Total time\",\"Engine hours\",\"Mileage\",\"Mileage (adjusted)\",\"Initial mileage\",\"Final mileage\",\"Avg speed\",\"Max speed\",\"Driver\",\"Count\",\"Consumed\",\"Consumed by FLS\",\"Initial fuel level\",\"Final fuel level\",\"Max fuel level\",\"Min fuel level\"]","cp":"[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]","s":"","sl":"","filter_order":["duration","mileage","base_eh_sensor","engine_hours","speed","stops","sensors","sensor_name","custom_sensors_col","driver","trailer","geozones_ex"],"p":"","sch":{"f1":0,"f2":0,"t1":0,"t2":0,"m":0,"y":0,"w":0,"fl":0},"f":256},{"n":"unit_group_stops","l":"Stops","c":"[\"time_begin\",\"time_end\",\"duration\",\"driver\",\"location\",\"coord\",\"stops_count\"]","cl":"[\"Beginning\",\"End\",\"Duration\",\"Driver\",\"Location\",\"Coordinates\",\"Count\"]","cp":"[{},{},{},{},{},{},{}]","s":"","sl":"","filter_order":["duration","sensors","sensor_name","driver","trailer","fillings","thefts","geozones_ex"],"p":"","sch":{"f1":0,"f2":0,"t1":0,"t2":0,"m":0,"y":0,"w":0,"fl":0},"f":256},{"n":"unit_group_stays","l":"Parkings","c":"[\"time_begin\",\"time_end\",\"duration\",\"location\",\"coord\",\"driver\",\"stays_count\"]","cl":"[\"Beginning\",\"End\",\"Duration\",\"Location\",\"Coordinates\",\"Driver\",\"Count\"]","cp":"[{},{},{},{},{},{},{}]","s":"","sl":"","filter_order":["duration","sensors","sensor_name","fillings","thefts","driver","trailer","geozones_ex"],"p":"","sch":{"f1":0,"f2":0,"t1":0,"t2":0,"m":0,"y":0,"w":0,"fl":0},"f":256}],"bsfl":{"ct":1675063376,"mt":1675063897}}

# Fetch EID
eid = get_eid()

# Display both reports in tabs
tabs = st.tabs(["Eco Driving Report", "Trip Report"])

# Eco Driving Report tab
with tabs[0]:
    st.write("Fetching Eco Driving Report...")
    eco_driving_data = get_eco_driving_report(group_id, start_datetime, end_datetime, eco_template, eid)
    eco_driving_file_name = f'{group_name}_Eco_Driving_Report.xlsx'
    with open(eco_driving_file_name, 'wb') as fp:
        fp.write(eco_driving_data)
    eco_driving_df = pd.read_excel(eco_driving_file_name, sheet_name='Eco driving')
    #eco_driving_df2 = eco_driving_df[eco_driving_df['Count'] == 1].copy()
    columns = ['Grouping','Mileage','Violation','Count','Violation duration','Violation mileage']
    scoring_df = eco_driving_df[columns]

    scoring_df['Count'] = 1
    df2 = scoring_df[scoring_df['Violation'] != '-----']
    df3 = df2[df2['Grouping'] != '-----']
    os.remove(eco_driving_file_name)
    st.write("Eco Driving Report", df3)
    
    # Push to PostgreSQL
    db_url = "postgresql://postgres:Mawaskii254@localhost:5432/postgres"
    engine = create_engine(db_url)
    df3.to_sql('eco_driving', engine, if_exists='replace', index=False)

# Trip Report tab
with tabs[1]:
    st.write("Fetching Trip Report...")
    trip_data = get_trip_report(group_id, start_datetime, end_datetime, group_trips_stops_parkings_report_template, eid)
    trip_file_name = f'{group_name}_Trip_Report.xlsx'
    with open(trip_file_name, 'wb') as fp:
        fp.write(trip_data)
    trip_df = pd.read_excel(trip_file_name, sheet_name='Trips')
    # # Select relevant columns and filter data
    selected_columns = ['Grouping', 'Beginning', 'End', 'Initial location', 'Final location', 'Max speed', 'Mileage', 'Count']
    trips_df = trip_df[selected_columns]
    # # Filter for trips where 'Count' is 1
    trips_df2 = trips_df[trips_df['Count'] == 1].copy()

 # Reset index for cleaner output
    trips_df2.reset_index(drop=True, inplace=True)
    os.remove(trip_file_name)
    st.write("Trip Report", trips_df2)
    
    # Push to PostgreSQL
    db_url = "postgresql://postgres:Mawaskii254@localhost:5432/postgres"
    engine = create_engine(db_url)
    trips_df2.to_sql('trips_data2', engine, if_exists='replace', index=False)
