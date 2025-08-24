

## Liberias
import streamlit as st
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from urllib.parse import quote


st.title("Análisis Inmoviliario")

## Lecturas de data
path = Path(rf"C:\Users\PC\Desktop\Proyectos\Proyectos_Py\6.Analisis_Alquiler_Venta\vivienda\data\data_alquiler_venta.csv")
data = pd.read_csv(path, sep="|")

## Variables
distritos = data["distrito_oficial"].unique()
inmueble = data["inmueble"].unique()
operacion = data["operacion"].unique()



# --------- PESTAÑAS ----------
# tab1, tab2, tab3 = st.tabs(["🔎 Análisis", "📦 Alquiler", "📊 Venta"])
# st.sidebar.header('Filtros Analisis')
# # input_distrito = st.sidebar.selectbox('Seleccione un distrito', distritos)
# input_inmueble = st.sidebar.selectbox('Seleccione un tipo de inmueble', inmueble)
# input_operacion = st.sidebar.selectbox('Seleccione una operación', operacion)

    
tab1, tab2, tab3 = st.tabs(["🔎 Análisis", "📦 Alquiler", "📊 Venta"])

with tab1:

    # ---- Sidebar falso sólo en esta pestaña ----
    # ---- Filtros en una sola línea ----
    c1, c2 = st.columns([2, 2], gap="small")
    with c1:
        st.markdown("**Inmueble**")
        input_inmueble = st.selectbox(
            "Inmueble", inmueble, key="f_inm",
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("**Operación**")
        input_operacion = st.selectbox(
            "Operación", operacion, key="f_ope",
            label_visibility="collapsed"
        )

    col_precio = "precio_usd" if input_operacion == "venta" else "precio_pen"
    simbolo   = "US$" if input_operacion == "venta" else "S/"

    df_filtrado = data[
        (data["inmueble"] == input_inmueble) &
        (data["operacion"] == input_operacion)
    ].copy()

    data_agrupada = df_filtrado.groupby("distrito_oficial")
    data_agrupada_df = data_agrupada[col_precio].agg(
        n="count",
        min="min", max="max",
        p05=lambda s: s.quantile(0.05),
        q1=lambda s: s.quantile(0.25),
        median="median",
        q3=lambda s: s.quantile(0.75).round(2),
        p95=lambda s: s.quantile(0.95).round(2)
    )

    cols_precios = [c for c in data_agrupada_df.columns if c != "n"]
    data_agrupada_df_fmt = data_agrupada_df.copy()
    data_agrupada_df_fmt[cols_precios] = data_agrupada_df_fmt[cols_precios]\
        .applymap(lambda x: f"{simbolo} {x:,.0f}")

    # st.table(data_agrupada_df_fmt.sort_values("n", ascending=False))
    # st.dataframe(
    # data_agrupada_df_fmt.sort_values("n", ascending=False),
    # use_container_width=True, 
    # height=None, 
    # )   
    
    styled_df = data_agrupada_df_fmt.sort_values("n", ascending=False).style.set_table_styles(
        [
            {"selector": "th", "props": [("font-size", "12px"), ("text-align", "center")]},
            {"selector": "td", "props": [("font-size", "12px"), ("text-align", "center")]}
        ]
    ).set_properties(**{
        'width': 'auto',     # ancho automático de columnas
        'max-width': '100px' # evita columnas enormes
    })
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    

with tab2:
    st.subheader("Vista de alquiler (sin sidebar)")
    # tu lógica de alquiler

with tab3:
    st.subheader("Vista de venta (sin sidebar)")
    # tu lógica de venta