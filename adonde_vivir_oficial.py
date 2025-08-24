

## Liberias
import streamlit as st
import pandas as pd
from pathlib import Path
# from geopy.geocoders import Nominatim
# from geopy.extra.rate_limiter import RateLimiter
# import matplotlib.pyplot as plt
# import plotly.express as px
# import plotly.graph_objects as go
# import numpy as np
# import folium
# from folium.plugins import MarkerCluster
# from streamlit_folium import st_folium
# from urllib.parse import quote


st.title("Análisis Inmoviliario")

## Lecturas de data
# path = Path(rf"C:\Users\PC\Desktop\Proyectos\Proyectos_Py\6.Analisis_Alquiler_Venta\vivienda\data\data_alquiler_venta.csv")
path = "./data/data_alquiler_venta.csv"

data = pd.read_csv(path, sep="|", encoding="utf-8")

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
    
    st.subheader(f"Lista de Propiedad en {input_inmueble} en {input_operacion}")
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
    
## Pestaña de Alquiler
with tab2:
    
    st.subheader("Vista de Alquiler", divider="blue")
    
    c1, c2 = st.columns([2, 2], gap="small")
    with c1:
        st.markdown("**Inmueble**")
        input_inmueble = st.selectbox(
            "Inmueble", inmueble, key="f_inm",
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("**Distrito**")
        input_distrito = st.selectbox(
            "Distrito", distritos, key="f_inm",
            label_visibility="collapsed"
        )
    
    ## Filtrado de Alquiler
    df_filtrado_aquiler = data[
        (data["inmueble"] == input_inmueble) &
        (data["distrito_oficial"] == input_distrito) &
        (data["operacion"] == "alquiler")
    ].copy()
    
    
    st.subheader("KPIs de precios Alquiler (S/.)")
    # Asegura numérico
    df_filtrado_aquiler["precio_pen"] = pd.to_numeric(df_filtrado_aquiler["precio_pen"], errors="coerce")
    df_kpi = df_filtrado_aquiler.dropna(subset=["precio_pen"])
    # Formato helper
    fmt = lambda x: f"S/. {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total propiedades", len(df_kpi))
    with c2: st.metric("Mínimo", fmt(df_kpi["precio_pen"].min()))
    with c3: st.metric("Máximo", fmt(df_kpi["precio_pen"].max()))
    c4, c5 = st.columns(2)
    with c4: st.metric("Promedio", fmt(df_kpi["precio_pen"].mean()))
    with c5: st.metric("Mediana", fmt(df_kpi["precio_pen"].median()))
    
    
    st.subheader(f"Lista de Propiedad en Alquiler en {input_distrito}")
    
    

## Pestaña de Venta
with tab3:
    
    st.subheader("Vista de Venta", divider="blue")
    
    c1, c2 = st.columns([2, 2], gap="small")
    with c1:
        st.markdown("**Inmueble**")
        input_inmueble = st.selectbox(
            "Inmueble", inmueble, key="f_inm",
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("**Distrito**")
        input_distrito = st.selectbox(
            "Distrito", distritos, key="f_inm",
            label_visibility="collapsed"
        )
    
    ## Filtrado de Alquiler
    df_filtrado_venta = data[
        (data["inmueble"] == input_inmueble) &
        (data["distrito_oficial"] == input_distrito) &
        (data["operacion"] == "venta")
    ].copy()
    
    
    st.subheader("KPIs de precios Alquiler (S/.)")
    # Asegura numérico
    df_filtrado_venta["precio_usd"] = pd.to_numeric(df_filtrado_venta["precio_usd"], errors="coerce")
    df_kpi = df_filtrado_venta.dropna(subset=["precio_usd"])
    # Formato helper
    fmt = lambda x: f"$. {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total propiedades", len(df_kpi))
    with c2: st.metric("Mínimo", fmt(df_kpi["precio_usd"].min()))
    with c3: st.metric("Máximo", fmt(df_kpi["precio_usd"].max()))
    c4, c5 = st.columns(2)
    with c4: st.metric("Promedio", fmt(df_kpi["precio_usd"].mean()))
    with c5: st.metric("Mediana", fmt(df_kpi["precio_usd"].median()))
    
    
    st.subheader(f"Lista de Propiedad en Venta en {input_distrito}")
