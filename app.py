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





#    ------------------------------------------   #
###    ---------   WEBSITE SETUP   ---------    ###
#    ------------------------------------------   #

st.set_page_config(layout="wide", page_title="Dylan's URP 535 Final", page_icon="🏙️")
st.header("Understanding the State of Energy Efficiency in Chicago")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "Context", "Methods", "Data","Findings"])





#    ------------------------------------------   #
###    -----------   HOME PAGE   -----------    ###
#    ------------------------------------------   #
with tab1:
    col1, col2 = st.columns([3,5])
    with col1:
        st.header("Hello!   I'm Dylan Ingui.")
        st.write("I am a junior at the University of Michigan studying Urban Technology with a minor in \
            User Experience Design.")
        st.write("I come from a background in high performance building, and the purpose of my work is to \
            promote and practice energy efficiency in urban contexts.  This project was created as a way to understand and visualize \
            the landscape of energy efficiency in Chicago.")
    with col2:
        st.image('images/Thermal_Image.jpg', width=500)
    st.write("------------------------------------------------------------------------------")





#    --------------------------------------------   #
###    ---------   PROJECT CONTEXT   ---------    ###
#    --------------------------------------------   #
with tab2:
    col1, col2 = st.columns([3,5])
    with col1:
        st.image('images/Draft_Chicago_Energy_Rating_Placard.jpg', width=400)
    with col2:
        st.write("In America, there has been a large push towards energy efficiency in the built environment in a plethora of \
                the country's largest cities.  New York City gives large buildings an energy limit through [Local Law 97](https://www.nyc.gov/site/buildings/codes/ll97-greenhouse-gas-emissions-reductions.page#:~:text=Local%20Law%2097%20allows%20for,Questions%20and%20LL97%20RECs%20Policy.),\
                and the city taxes large building owners that refuse to comply.  Boston's [BERDO 2.0](https://www.iesve.com/discoveries/view/40249/berdo-2-0-decarbonizing-boston) \
                and DC's [BEPS](https://buildinginnovationhub.org/resource/regulation-basics/?gad_source=1&gclid=CjwKCAjw8IfABhBXEiwAxRHlsCHfp_HKfMvclnSkz7fMnW7demaNLFQ3MlWtc43EwZUbwqz2srFZYBoCfaMQAvD_BwE) programs were \
                introduced to place strict emissions thresholds on certain building types.  Finally, San Francisco's [Climate Action Plan](https://sfplanning.org/project/san-francisco-climate-action-plan#about) \
                focuses more on electrification and decarbonization rather than on emission caps.  \
                The City of Chicago, however, is still in the early stages of climate legislation.")
        
        st.write("Despite not having any strong action plans passed in legislation yet, Chicago has indirectly created an effort \
                to promote energy efficiency through their [Chicago Energy Rating](https://www.chicago.gov/city/en/progs/env/ChicagoEnergyRating.html).  \
                The program requires buildings over 50,000 square feet to report on their energy consumption once every three years to receive an energy \
                rating.  Luckily, Chicago's Open Data Portal publicly provides their dataset on buildings with a Chicago Energy Rating, which is the base data \
                utilized for this project.")
    st.write("------------------------------------------------------------------------------")





#    ---------------------------------------------   #
###    -----------   METHODS PAGE   -----------    ###
#    ---------------------------------------------   #
with tab3:
    st.write("these are methods")





#    -----------------------------------------------------   #
###    -----------   DATA VISUALIZATION PAGE   -----------    ###
#    -----------------------------------------------------   #
with tab4:
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
            ("Total Projects Built", "Average Energy Rating")
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
    if display == "Total Projects Built":
        color_by = "Total_Buildings"
        percents = [0, .04, .25, .5, .9]
    else:
        color_by = "Mean_Rating"
        percents = [0, .3, .5, .7, .9]

    # Get min and max
    min_val = merged[color_by].min()
    max_val = merged[color_by].quantile(0.95)

    # Create threshold manually
    thresholds = [min_val + (max_val - min_val) * p for p in percents]

    # Colors!
    if display == "Total Projects Built":
        colors = ['#e7efff', '#a4bbea', '#6c90d9', '#3b6bca', '#002f8c']
        caption = "Total Projects by Ward"
    else:
        colors = ['#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#31a354']
        caption = "Average Energy Rating by Ward"

    # Create a step colormap
    colormap = cm.StepColormap(
        colors=colors,
        index=thresholds,
        vmin=min_val,
        vmax=max_val,
        caption=caption
    )





    #    --------------------------------------------   #
    ###    --------   MAP VISUALIZATION   --------    ###
    #    --------------------------------------------   #

    with col2:
        # Create map (centered around Chicago)
        m = folium.Map(location=[41.875, -87.63], zoom_start=9.5)
        
        ticks = 5
        equal_ticks = np.linspace(min_val, max_val, ticks + 1)

        # Add GeoJson layer
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
                aliases=["Ward", "Average Energy Rating", "Total Projects Built"]
            )
        ).add_to(m)
        
        colormap.add_to(m)

        # Display map in Streamlit
        st_data = st_folium(m, width=800, height=500)





#    --------------------------------------------   #
###    ----------   FINDINGS PAGE   ----------    ###
#    --------------------------------------------   #
with tab5:
    st.write('hello world 3')