#!/usr/bin/env python
# coding: utf-8

# In[2]:

import calendar  # Core Python Module
from datetime import datetime  # Core Python Module
import streamlit as st  # pip install streamlit
from streamlit_option_menu import option_menu  # pip install streamlit-option-menu
from deta import Deta
import pandas as pd
import altair as alt

from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

import folium
from streamlit_folium import st_folium



# In[ ]:


DETA_KEY  = "a0acyqpb_JSJasjvVhoGmGLrSXmdyMVamB196dpNK"

deta = Deta(DETA_KEY)

db = deta.Base("check_list")

# -------------- FUNCTIONS --------------

def insert_period(date, species, n_specimens, comment, lat, lon):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db.put({"date": date, "species": species, "n_specimens": n_specimens, "comment": comment, "lat": lat, "lon": lon})


# -------------- SETTINGS --------------
species = ["Anax imperator", "Anax parthenope", "Libellula fulva"]
page_title = "Income and Expense Tracker"
page_icon = ":fish: - :whale2: - :whale2: - :whale2:"  # emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
layout = "centered"

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
st.title(page_icon)


# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- NAVIGATION MENU ---
selected = option_menu(
    menu_title=None,
    options=["Data Entry", "Data Visualization"],
    icons=["pencil-fill", "bar-chart-fill"],  # https://icons.getbootstrap.com/
    orientation="horizontal",
)

# --- INPUT & SAVE PERIODS ---
if selected == "Data Entry":
    with st.form("entry_form", clear_on_submit=True):

        date = st.date_input("Date")
        with st.expander("Species:"):
                sp = st.selectbox("", species, key="species")
                n = st.number_input("n_specimens:", min_value=0, key="n_specimens")
        with st.expander("Comment"):
            comment = st.text_area("", placeholder="Enter a comment here ...")
        
        loc_button = Button(label="Get Location")
        loc_button.js_on_event("button_click", CustomJS(code="""
            navigator.geolocation.getCurrentPosition(
                (loc) => {
                    document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))
                }
            )
            """))

        result = streamlit_bokeh_events(
            loc_button,
            events="GET_LOCATION",
            key="get_location",
            refresh_on_update=False,
            override_height=75,
            debounce_time=0)

        if result:
            if "GET_LOCATION" in result:
                lat = result.get("GET_LOCATION")["lat"]
                lon = result.get("GET_LOCATION")["lon"]

        "---"
        submitted = st.form_submit_button("Save Data")
        if submitted:
            period = str(date)
            insert_period(period, sp, n, comment, lat, lon)
            st.success("Data saved!")
            
# --- PLOT PERIODS ---
if selected == "Data Visualization":
    # ---CREATE THE FILTERS---
    sp_plot = st.selectbox("Species", species, key="species")
    
    # ---FILTER THE DATASET---
    db_content = db.fetch().items
    df = pd.DataFrame(db_content).drop("key",axis=1)
    df_2 = df[df.species==sp_plot]
    
    with st.form("saved_periods"):
        submitted = st.form_submit_button("Plot Period")
        if submitted:
            # ---show dataframe---
            st.dataframe(df,use_container_width=True)
            
            # ---CREATE THE PLOT---
            source = df.groupby("species", as_index=False)['n_specimens'].sum()
            st.dataframe(source)
            c = alt.Chart(source).mark_bar().encode(y='species', x='n_specimens', color='species')
            st.altair_chart(c, use_container_width=True)
            
            # ---CREATE THE MAP---
            m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=12,control_scale=False,tiles=None )
            tile_layer = folium.TileLayer(
                tiles='OpenStreetMap',
                control=False,
                opacity=1
            )
            for i, row in df.iterrows():
                popup = folium.Popup(f"""
                  <a Date: {row["date"]}</a><br>
                  <br>
                  <a Species: {row["species"]}</a><br>
                  """,
                  max_width = 250)

                folium.Marker([row['lat'], row['lon']],
                              popup=popup).add_to(m)

            tile_layer.add_to(m)
            st_folium(m,  width=500, height=500)
            
    # ---CREATE A DOWNLOAD BOTTON ---
    csv = df_2.to_csv().encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='df.csv',
        mime='text/csv',
    )
            
            

            
                                                
            
        











