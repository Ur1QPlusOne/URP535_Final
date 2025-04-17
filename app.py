#   -------------------------------------   #
###    ---------   MODULES   ---------    ###
#   -------------------------------------   #

# Streamlit Modules
import streamlit as st
from streamlit_folium import st_folium

# Map Modules
import geopandas as gpd
import folium
from folium.plugins import Draw
from shapely.geometry import shape
import branca.colormap as cm

# Data Modules
import pandas as pd
import numpy as np

# Essential Modules
import json

# Setup imports
from setup import df as setup_df
from setup import wards_df as wards_df





#    -------------------------------------------   #
###    ---------   FUNCTION SETUP   ---------    ###
#    -------------------------------------------   #

def display_group(df, area):
    ret = df.groupby(area).agg({
        "chicago_energy_rating": "sum",
        "id": "count"
    }).reset_index()
    ret.columns = [area, "Total_Energy_Rating", "Total_Buildings"]
    ret['Mean_Rating'] = ret.apply(lambda x: round(x["Total_Energy_Rating"]/x["Total_Buildings"], 2), axis=1)
    return ret

def make_shape(geo):
    try:
        if pd.isna(geo):
            return None
        if isinstance(geo, dict):
            return shape(geo)
        if isinstance(geo, str):
            geo = geo.strip()
            if not geo or geo.lower() in ['nan', 'null']:
                return None
            geo = json.loads(geo)
            return shape(geo)
        return None
    except Exception as e:
        print(f"Skipping invalid geometry: {geo} — {e}")
        return None





#    -------------------------------------------   #
###    -------------   HEADER   -------------    ###
#    -------------------------------------------   #

st.set_page_config(
    layout="wide",
    page_title="Dylan's URP 535 Final",
    page_icon="🏙️",
    )
st.header("Chicago Energy Visualization")
st.subheader("regular text ah")
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Context", "Data","Findings"])

with tab1:
    st.write('hello world 1')

with tab2:
    st.write('hello world 2')

with tab3:
    col1, col2 = st.columns([1, 2])





    #    --------------------------------------------   #
    ###    -------------   SELECTS   -------------    ###
    #    --------------------------------------------   #

    # Year slider
    min_year = setup_df['data_year'].min()
    max_year = setup_df['data_year'].max()

    with col1:
        st.write("------------------------------------------------------------------------------")
        
        year = st.slider(
            "Select Year",
            min_value=min_year,
            max_value=max_year,
            step=1
        )

        # Permit data select
        permit = st.selectbox(
            "Select Data Visualized",
            ("All Permits", "Retrofit Permits", "Newbuild Permits"),
        )

        # Select dislayed metric
        display = st.selectbox(
            "Select Displayed Metric:",
            ("Total Registered Builds", "Average Energy Rating")
        )

        # Print what user is viewing
        st.write("You're viewing:", permit, " with a Chicago energy efficiency score since", str(year), '.')
        st.write("The gradient displayed is based on", display, " and is visualized by Chicago's ward .")
        st.write("------------------------------------------------------------------------------")




    #    --------------------------------------------   #
    ###    -----------   DATA FILTER   -----------    ###
    #    --------------------------------------------   #

    # Filter by year and permit type
    permit_dict = {"Retrofit Permits" : "PERMIT - RENOVATION/ALTERATION", "Newbuild Permits" : "PERMIT - NEW CONSTRUCTION"}
    if permit == "All Permits":
        df_map = setup_df[setup_df['data_year'] <= year]
    else:
        df_map = setup_df[
            (setup_df['data_year'] <= year) &
            (setup_df['permit_type'] == permit_dict[permit])
        ]

    grouped = display_group(df_map, 'ward')
    merged = wards_df.merge(grouped, on="ward")
    merged['geometry'] = merged['the_geom'].apply(make_shape)
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")





    #    --------------------------------------------   #
    ###    --------   MAP VISUALIZATION   --------    ###
    #    --------------------------------------------   #

    with col2:
        # Create map (centered around Chicago)
        m = folium.Map(location=[41.875, -87.63], zoom_start=9.5)
        
        # Select dislayed metric
        if display == "Total Registered Builds":
            color_by = "Total_Buildings"
        else:
            color_by = "Mean_Rating"
        colors = merged[color_by]
        
        min_val = colors.min()
        max_val = colors.max()

        # Create the colormap
        if display == "Total Registered Builds":
            colormap = cm.linear.Blues_09.scale(min_val, max_val)
            colormap.caption = "Total Projects by Ward"
        else:
            colormap = cm.linear.Greens_09.scale(min_val, max_val)
            colormap.caption = "Average Energy Rating by Ward"

        # Add geometry, color, and stroke.
        folium.GeoJson(
            merged,
            style_function=lambda feature: {
                "fillColor": colormap(feature["properties"][color_by]),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["ward", "Mean_Rating", "Total_Buildings"],
                aliases=["Ward", "Average Energy Rating", "Total Registered Builds"]
            )
        ).add_to(m)
        
        colormap.add_to(m)

        # Display map in Streamlit
        st_data = st_folium(m, width=800, height=500)

with tab4:
    st.write('hello world 3')