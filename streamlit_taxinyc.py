import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk

@st.cache
def load_data(path):
    return pd.read_csv(path, delimiter=',')

@st.cache
def get_dom(dt):
    return dt.day

@st.cache
def get_weekday(dt):
    return dt.weekday()

@st.cache
def get_hour(dt):
    return dt.hour

# Load data
path = "https://raw.githubusercontent.com/uber-web/kepler.gl-data/master/nyctrips/data.csv"
df = load_data(path)

# Data exploration and analysis
st.write(df)
st.write(df.describe())

total_fares = df["fare_amount"].sum()
st.write("Total fares :", total_fares)
tip_fares = df["tip_amount"].sum()
st.write("Total tips :", tip_fares)
total_distance = df["trip_distance"].sum()
st.write("Total distance :", total_distance)
farePerMile = total_fares / total_distance
st.write("Each mile run generated :", farePerMile, "$")

st.write(df.head())

# Modification des timestamps (strings) en format datetime et parsing
df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
df["hour"] = df["tpep_pickup_datetime"].dt.hour
df["minute"] = df["tpep_pickup_datetime"].dt.minute
df["minute_oftheday"] = df["hour"] * 60 + df["minute"]
df["day_week"] = df["tpep_pickup_datetime"].dt.dayofweek
df["month"] = df["tpep_pickup_datetime"].dt.month
df['Duration'] = (df['tpep_dropoff_datetime'].map(pd.to_datetime) - df['tpep_pickup_datetime'].map(pd.to_datetime)).dt.seconds

st.write(df)
st.write(df.describe())

df4 = df.groupby("passenger_count").sum()
st.write(df4)

"""Number of passengers per company"""
fig, ax = plt.subplots(1, 2)
sns.countplot(x="passenger_count", data=df[df["VendorID"] == 1], ax=ax[0])
sns.countplot(x="passenger_count", data=df[df["VendorID"] == 2], ax=ax[1])
st.pyplot(fig)

# Duration without the outliers
fig, ax = plt.subplots(figsize=(10,10))
ax.scatter(range(len(df["Duration"])), np.sort(df["Duration"]))
ax.set_xlabel('index')
ax.set_ylabel('trip duration in seconds')
st.pyplot(fig)

df['log_duration'] = np.log1p(df['Duration'].values)

fig, ax = plt.subplots()
ax.hist(df['log_duration'], bins=50)
ax.set_xlabel('log(trip duration)')
st.pyplot(fig)

sns.set_style('darkgrid')

fig, ax = plt.subplots()
ax.hist(df['trip_distance'], bins=20, color='blue')
ax.set_title('Distribution de la distance de voyage')
ax.set_xlabel('Distance de voyage (miles)')
ax.set_ylabel('Fréquence')
st.pyplot(fig)

sns.set_style('white')

fig, ax = plt.subplots()
ax.scatter(df['pickup_longitude'], df['pickup_latitude'], s=0.5, alpha=0.1)
ax.set_title('Carte des prises en charge')
ax.set_xlabel('Longitude')
ax.set_ylabel

def generate_pickup_layer(df, vendor_id, color):
    pickup_counts = df[df['VendorID'] == vendor_id].groupby(['pickup_longitude', 'pickup_latitude']).size().reset_index(name='counts')
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=pickup_counts,
        get_position='[pickup_longitude, pickup_latitude]',
        get_radius='counts/50',
        radius_scale=0.5,
        radius_min_pixels=3,
        get_color=color,
        pickable=True
    )
    return layer

def generate_dropoff_layer(df, vendor_id, color):
    dropoff_counts = df[df['VendorID'] == vendor_id].groupby(['dropoff_longitude', 'dropoff_latitude']).size().reset_index(name='counts')
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=dropoff_counts,
        get_position='[dropoff_longitude, dropoff_latitude]',
        get_radius='counts/50',
        radius_scale=0.5,
        radius_min_pixels=3,
        get_color=color,
        pickable=True,
        opacity=0.6
    )
    return layer

# Define the initial view state
view_state = pdk.ViewState(
    latitude=df['pickup_latitude'].median(),
    longitude=df['pickup_longitude'].median(),
    zoom=10
)

# Define the layers
pickup_layer_1 = generate_pickup_layer(df, 1, [155, 165, 0])
dropoff_layer_1 = generate_dropoff_layer(df, 1, [0, 155, 0])
pickup_layer_2 = generate_pickup_layer(df, 2, [255, 165, 0])
dropoff_layer_2 = generate_dropoff_layer(df, 2, [0, 255, 0])

# Define the DeckGL map
map_layer = pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=view_state,
    layers=[pickup_layer_1, dropoff_layer_1, pickup_layer_2, dropoff_layer_2]
)

# Render the map
st.pydeck_chart(map_layer)
