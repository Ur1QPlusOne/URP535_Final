"""  MODULES  """
import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
import requests
import streamlit as st
import numpy as np



"""  FUNCTION SETUP  """
def read_api(url):
    # Pull api
    response = requests.get(url)
    # If the pull works
    if response.status_code == 200:
        # Read it as a json and return it
        data = response.json()
        return gpd.GeoDataFrame(data)



"""  READ IN APIs FOR BUILDING DATA  """
# Read in permit data of completed new-build projects
newbuild_df = read_api("https://data.cityofchicago.org/resource/ydr8-5enu.json?permit_status=COMPLETE&permit_type=PERMIT%20-%20NEW%20CONSTRUCTION&$limit=50000")
# Read in permit data of completed retrofit projects
retrofit_df = read_api("https://data.cityofchicago.org/resource/ydr8-5enu.json?permit_status=COMPLETE&permit_type=PERMIT%20-%20RENOVATION/ALTERATION&$limit=50000")
# Read in energy benchmark data of all buildings
energy_df = read_api("https://data.cityofchicago.org/resource/xq83-jr8c.json?$limit=50000")



"""  DATA CLEANING  """
# PERMITS!!!
# There were a bunch of columns with contact email address etc. that were all empty and deleting them makes this go from 115ish columns to 30ish
necessary_columns = [x for x in retrofit_df.columns if x.startswith('contact') == False]
# Filter out useless columns
retrofit_df = retrofit_df[necessary_columns]
newbuild_df = newbuild_df[necessary_columns]
allhomes_df = result_vertical = pd.concat([retrofit_df, newbuild_df])
allhomes_df = allhomes_df[['id','permit_type', 'community_area','ward','latitude','longitude','location']]
# Filter out null rows
allhomes_df['longitude'] = pd.to_numeric(allhomes_df['longitude'], errors='coerce')
allhomes_df['latitude'] = pd.to_numeric(allhomes_df['latitude'], errors='coerce')

# ENERGY RATINGS!!!
# Drop rows with null values
energy_df_clean = energy_df.dropna(subset=['data_year', 'longitude', 'latitude', 'chicago_energy_rating'])
# Make columns numbers
energy_df_clean['data_year'] = pd.to_numeric(energy_df_clean['data_year'], errors='coerce')
energy_df_clean['longitude'] = pd.to_numeric(energy_df_clean['longitude'], errors='coerce')
energy_df_clean['latitude'] = pd.to_numeric(energy_df_clean['latitude'], errors='coerce')
energy_df_clean['chicago_energy_rating'] = pd.to_numeric(energy_df_clean['chicago_energy_rating'], errors='coerce')
# Filter out non-chicago locations
energy_df_clean = energy_df_clean[(energy_df_clean['latitude'].between(41.60, 42.10)) & (energy_df_clean['longitude'].between(-88.00, -87.50))]



"""  MERGING DFs  """
# Round to 4 or 5 decimal places (approx ~11m or ~1m accuracy)
energy_df_clean['latitude_rounded'] = energy_df_clean['latitude'].round(5)
energy_df_clean['longitude_rounded'] = energy_df_clean['longitude'].round(5)

allhomes_df['latitude_rounded'] = allhomes_df['latitude'].round(5)
allhomes_df['longitude_rounded'] = allhomes_df['longitude'].round(5)

merged_df = energy_df_clean.merge(allhomes_df, on=['latitude_rounded', 'longitude_rounded'])
df = merged_df[['data_year', 'id_x',  'zip_code',  'chicago_energy_rating', 'latitude_x', 'longitude_x', 'location_x', 'property_name', 'year_built', 'community_area_y', 'permit_type', 'ward']]
df.columns = ['data_year', 'id',  'zip_code',  'chicago_energy_rating', 'latitude', 'longitude', 'location', 'property_name', 'year_built', 'community_area', 'permit_type', 'ward']



""" WARD BOUNDARY IMPORTS """
wards_df = read_api("https://data.cityofchicago.org/resource/p293-wvbd.json")
wards_df.head()