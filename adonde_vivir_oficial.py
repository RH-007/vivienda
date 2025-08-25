
## Proyecto a Donde Vivir
## ==========================

## Liberias
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from streamlit_folium import st_folium
import streamlit as st
import folium
from folium.plugins import MarkerCluster, MiniMap, Fullscreen, MeasureControl, LocateControl
from urllib.parse import quote


## Titulo
st.set_page_config(layout="wide")
st.title("Análisis Inmobiliario 🏡📊")

"""
Bienvenido a la plataforma interactiva de análisis inmobiliario de Lima.  

Aquí podrás explorar **departamentos, casas y terrenos** en venta y alquiler, con datos reales y actualizados. 

Las fuentes son: 
- 🏡 [Urbania](https://urbania.pe)
- 🏠 [Adondevivir](https://www.adondevivir.com)

La aplicación te permite:

- 📍 Visualizar la distribución geográfica de las propiedades en los distintos distritos.  
- 💰 Comparar precios en **soles** y **dólares**, con métricas como precio por m² y variación.  
- 📐 Filtrar fácilmente por área, dormitorios, baños, estacionamientos y mantenimiento.  
- 🔗 Acceder directamente al anuncio original de cada propiedad.  

En pocas palabras: una herramienta diseñada para ayudarte a entender **cómo se mueve el mercado inmobiliario en Lima**, detectar oportunidades y tomar mejores decisiones.  
"""

## ==================##
## Lecturas de data  ##
## ==================##

# Ruta
path = "./data/data_alquiler_venta.csv"

data = pd.read_csv(path, sep="|", encoding="utf-8")

## Variables
distritos = data["distrito_oficial"].unique()
inmueble = data["inmueble"].unique()
operacion = data["operacion"].unique()

## ==================##
##      Pestañas     ##
## ==================##
    
tab1, tab2, tab3 = st.tabs(["🔎 Análisis General", "📦 Alquiler", "📊 Venta"])

with tab1:

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
    
    st.subheader(f"Lista de {input_inmueble} en {input_operacion}")
    
    st.data_editor(
        data_agrupada_df_fmt.sort_values("n", ascending=False),
        use_container_width=True,
        column_config={
            "distrito_oficial": st.column_config.TextColumn("Distrito", disabled=True)
        },
        disabled=True, height=1000,
        key="data_agrupada_fmt"
    )
    
    
## =================================##
## PESTAÑA de ALquiler por Distrito ##
## =================================##

with tab2:
    
    st.subheader("Vista de Alquiler", divider="blue")
    
    c1, c2 = st.columns([2, 2], gap="small")

    with c1:
        st.markdown("**Distrito**")
        input_distrito = st.selectbox(
            "Distrito", distritos, key="alquiler_distrito" ,
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("**Inmueble**")
        input_inmueble = st.selectbox(
            "Inmueble", inmueble, key="alquiler_inmueble" ,
            label_visibility="collapsed"
        )
    
    ## Filtrado de Alquiler
    df_filtrado_aquiler = data[
        (data["inmueble"] == input_inmueble) &
        (data["distrito_oficial"] == input_distrito) &
        (data["operacion"] == "alquiler")
    ].copy()
    
    
    ## =============================##
    ## KPI de ALquiler por Distrito ##
    ## =============================##
    
    st.subheader(f"KPIs de precios Alquiler (S/.) en el distrito de {input_distrito}", divider="blue")
    # Asegura numérico
    df_filtrado_aquiler["precio_pen"] = pd.to_numeric(df_filtrado_aquiler["precio_pen"], errors="coerce")
    df_kpi = df_filtrado_aquiler.dropna(subset=["precio_pen"])
    # Formato helper
    fmt = lambda x: f"S/ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(f"Total {input_inmueble}", len(df_kpi), border=True)
    with c2: st.metric("Mínimo", fmt(df_kpi["precio_pen"].min()),border=True)
    with c3: st.metric("Máximo", fmt(df_kpi["precio_pen"].max()), border=True)
    c4, c5 = st.columns(2)
    with c4: st.metric("Promedio", fmt(df_kpi["precio_pen"].mean()), border=True)
    with c5: st.metric("Mediana", fmt(df_kpi["precio_pen"].median()), border=True)
    

    ## =======================================##
    ## TABLA Detalle de ALquiler por Distrito ##
    ## =======================================##
    
    st.subheader(f"Lista de {input_inmueble} en Alquiler en {input_distrito}", divider="blue")
        
    d1, d2 = st.columns([2, 2], gap="small")
    with d1:
        st.markdown("**Precio**")
        labels_alquiler_precio = ["Todos" ,"Hasta S/ 1000", "De S/ 1000 a S/ 2500", "De S/ 2500 a S/ 5000", "De S/ 5000 a S/ 10000", "De S/ 10000 a más"]
        input_rango_precio_aquiler = st.selectbox(
            "seleccione el precio:"
            , options=labels_alquiler_precio
            , index=0
        )
        
    with d2:
        st.markdown("**Área**")       
        labels_area = ["Todos", "Hasta 50m2", "De 50m2 a 100m2", "De 100m2 a 200m2", "De 200m2 a 300m2", "De 300m2 a más"]
        input_rango_area_alquiler = st.selectbox(
            "seleccione el area:"
            , options=labels_area
            , index=0 
            
        )
        
    ## Filtrado de Alquiler
    if input_rango_precio_aquiler == "Todos" and input_rango_area_alquiler == "Todos":
        df_filtrado_aquiler = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "alquiler")
        ].copy()
        
    else:
        df_filtrado_aquiler = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "alquiler") &
            (data["area_agp"] == input_rango_area_alquiler) &
            (data["precio_alquiler_agp"] == input_rango_precio_aquiler)
        ].copy()
    
    
    data_aquiler = df_filtrado_aquiler[["fuente", "direccion", "precio", "caracteristica", "enlace", "precio_pen", "precio_usd", "area", "baños", "distrito_oficial", "dormitorio", "estacionamientos", "mantenimiento"]].copy()
    
    st.data_editor(
        data_aquiler[["fuente", "direccion", "precio_pen", "area", "dormitorio","baños", "estacionamientos", "mantenimiento","caracteristica", "enlace"]].sort_values("precio_pen", ascending=True),
        hide_index=True,
        use_container_width=True,
        column_config={
            "fuente": st.column_config.TextColumn("Fuente", disabled=True),
            "direccion": st.column_config.TextColumn("Dirección", disabled=True),
            "precio_pen": st.column_config.NumberColumn("Precio (S/.)", format="S/. %d", disabled=True),
            "area": st.column_config.NumberColumn("Área (m²)", format="%d", width="small", disabled=True),
            "dormitorio": st.column_config.NumberColumn("Dormitorio", disabled=True),
            "baños": st.column_config.NumberColumn("Baños", disabled=True),
            "estacionamientos": st.column_config.NumberColumn("Estacionamientos", disabled=True),
            "mantenimiento": st.column_config.NumberColumn("Mantenimiento (S/.)", format="S/. %d", disabled=True),            
            "enlace": st.column_config.LinkColumn("Abrir", display_text="Abrir anuncio", validate=r"^https?://.*$"),
        },
        disabled=True,
        key="tabla_con_link_alquiler"
    )
    
    ## ==============================##
    ## Mapa de ALquiler por Distrito ##
    ## ==============================##
    
    st.subheader(f"Mapa de {input_inmueble} en Alquiler en {input_distrito}", divider="blue")
    
    df_filtrado_aquiler_map = df_filtrado_aquiler.copy()
    
    # Normaliza status y valida lat/lon
    status_validos = {'geo', 'ok', 'geocoded', 'found'}  # ajusta según tus valores reales
    df_filtrado_aquiler_map['status'] = df_filtrado_aquiler_map['status'].astype(str).str.lower()

    gdf = df_filtrado_aquiler_map.loc[
        df_filtrado_aquiler_map['status'].isin(status_validos) &
        df_filtrado_aquiler_map['lat'].notna() &
        df_filtrado_aquiler_map['lon'].notna()
    ].copy()
    
    if gdf.empty:
        st.info("No hay propiedades con geolocalización válida para graficar.")
    else:
        precio_pen_col = "precio_pen" if "precio_pen" in df_filtrado_aquiler_map.columns else ("precio_pe" if "precio_pe" in df_filtrado_aquiler_map.columns else None)
        precio_usd_col = "precio_usd" if "precio_usd" in df_filtrado_aquiler_map.columns else ("dolares" if "dolares" in df_filtrado_aquiler_map.columns else None)
        cols_extra = [c for c in ["fuente", "domitorio_min", precio_pen_col, precio_usd_col, "enlace", "caracteristica"] if c and c in df_filtrado_aquiler_map.columns]

        # Centro del mapa
        center_lat, center_lon = gdf['lat'].mean(), gdf['lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='OpenStreetMap')

        # Controles útiles
        # Fullscreen().add_to(m)
        # MiniMap(toggle_display=True).add_to(m)
        # MeasureControl(primary_length_unit='meters').add_to(m)
        LocateControl().add_to(m)

        # Cluster de marcadores
        cluster = MarkerCluster(name="Propiedades").add_to(m)

        # Función para color (ejemplo: por operación si existe la columna)
        def color_marker(row):
            if 'operacion' in row and isinstance(row['operacion'], str):
                op = row['operacion'].lower()
                if 'alquiler' in op: return 'blue'
                if 'venta' in op: return 'green'
            return 'red'

        # Construye popup/tooltip seguros
        def safe(x): 
            return "" if pd.isna(x) else str(x)
        
        def fmt_money(x, symbol):
            if pd.isna(x): return "-"
            s = f"{symbol} {x:,.0f}".replace(",", "X").replace(".", ",").replace("X",".")
            return s

        for _, r in gdf.iterrows():
            precio_pen = fmt_money(r.get(precio_pen_col), "S/.") if precio_pen_col else "-"
            precio_usd = fmt_money(r.get(precio_usd_col), "US$") if precio_usd_col else "-"
            gmaps_q = quote(f"{r['direccion']}, Lima, Perú")
            popup_html = f"""
            <b>Dirección:</b> {r['direccion']}<br>
            <b>Caracteristicas:</b> {r.get('caracteristica','-')}<br>
            <b>Precio PEN:</b> {safe(r.get('precio_pen'))}<br/>
            <b>Precio USD:</b> {safe(r.get('precio_usd'))}<br/>
            <b>Dirección:</b> {safe(r.get('direccion_fix') or r.get('direccion'))}<br/>
            <b>Enlace:</b> <a href="{r['enlace']}" target="_blank">Abrir en {r.get('fuente','-')}</a><br>
            <a href="https://www.google.com/maps/search/?api=1&query={gmaps_q}" target="_blank">Abrir en Google Maps</a>
            """

            folium.CircleMarker(
                location=[r['lat'], r['lon']],
                radius=5,
                color=color_marker(r),
                fill=True,
                fill_opacity=0.8,
                tooltip=safe(r.get('direccion_fix') or r.get('direccion')),
                popup=folium.Popup(popup_html, max_width=350),
            ).add_to(cluster)

        # Render en Streamlit
        st_folium(m, height=600, use_container_width=True)
    
    
## ===============================##
## PESTAÑA de Ventas por Distrito ##
## ===============================##

with tab3:
    
    st.subheader("Vista de Venta", divider="blue")
    
    c1, c2 = st.columns([2, 2], gap="small")
    with c1:
        st.markdown("**Distrito**")
        input_distrito = st.selectbox(
            "Distrito", distritos,key="venta_distrito" ,     # <- clave única
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("**Inmueble**")
        input_inmueble = st.selectbox(
            "Inmueble", inmueble, key="venta_inmueble"  ,     # <- clave única
            label_visibility="collapsed"
        )

    
    ## Filtrado de Alquiler
    df_filtrado_venta = data[
        (data["inmueble"] == input_inmueble) &
        (data["distrito_oficial"] == input_distrito) &
        (data["operacion"] == "venta")
    ].copy()
    
    ## ==========================##
    ## KPI de Venta por Distrito ##
    ## ==========================##
    
    st.subheader(f"KPIs de precios Venta ($) en el distrito de {input_distrito}")
    # Asegura numérico
    df_filtrado_venta["precio_usd"] = pd.to_numeric(df_filtrado_venta["precio_usd"], errors="coerce")
    df_kpi = df_filtrado_venta.dropna(subset=["precio_usd"])
    # Formato helper
    fmt = lambda x: f"$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total propiedades", len(df_kpi), border=True)
    with c2: st.metric("Mínimo", fmt(df_kpi["precio_usd"].min()), border=True)
    with c3: st.metric("Máximo", fmt(df_kpi["precio_usd"].max()), border=True)
    c4, c5 = st.columns(2)
    with c4: st.metric("Promedio", fmt(df_kpi["precio_usd"].mean()), border=True)
    with c5: st.metric("Mediana", fmt(df_kpi["precio_usd"].median()), border=True)
    
    ## ====================================##
    ## TABLA Detalle de Venta por Distrito ##
    ## ====================================##
    
    st.subheader(f"Lista de {input_inmueble} en Alquiler en {input_distrito}", divider="blue")
    
    e1, e2 = st.columns([2, 2], gap="small")
    with e1:
        st.markdown("**Precio**")
        labels_venta_precio = ["Todos", "Hasta $ 50k", "De $ 50k a $ 100k", "De $ 100k a $ 200k", "De $ 100k a $ 500k", "De $ 500k a más"]
        input_rango_precio_venta = st.selectbox(
            "seleccione el precio:"
            , options=labels_venta_precio
            , index=0
            , key="rango_area_venta"
        )
        
    with e2:
        st.markdown("**Área**")       
        labels_area_venta = ["Todos", "Hasta 50m2", "De 50m2 a 100m2", "De 100m2 a 200m2", "De 200m2 a 300m2", "De 300m2 a más"]
        input_rango_area_venta = st.selectbox(
            "seleccione el area:"
            , options=labels_area_venta
            , index=0 
            , key="rango_area_alquiler"
            
        )
        
    ## Filtrado de Venta
    if input_rango_precio_venta == "Todos" and input_rango_area_venta == "Todos":
        df_filtrado_venta = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "alquiler")
        ].copy()
        
    else:
        df_filtrado_venta = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "alquiler") &
            (data["area_agp"] == input_rango_area_venta) &
            (data["precio_venta_agp"] == input_rango_precio_venta)
        ].copy()
    
    data_venta = df_filtrado_venta[["fuente", "direccion", "precio", "caracteristica", "enlace", "precio_pen", "precio_usd", "area", "baños", "distrito_oficial", "dormitorio", "estacionamientos", "mantenimiento"]].copy()
    
    # st.dataframe(data_aquiler)
    st.data_editor(
        data_venta[["fuente", "direccion", "precio_usd", "area", "dormitorio","baños", "estacionamientos","caracteristica", "enlace"]].sort_values("precio_usd", ascending=True),
        hide_index=True,
        use_container_width=True,
        column_config={
            "fuente": st.column_config.TextColumn("Fuente", disabled=True),
            "direccion": st.column_config.TextColumn("Dirección", disabled=True),
            "precio_usd": st.column_config.NumberColumn("Precio $.", format="$ %d", disabled=True),
            "caracteristicas": st.column_config.NumberColumn("Caracteristicas", disabled=True),
            "enlace": st.column_config.LinkColumn("Abrir", display_text="Abrir anuncio", validate=r"^https?://.*$"),
        },
        disabled=True,
        key="tabla_con_link_venta"
    )
    
    ## ===========================##
    ## Mapa de Venta por Distrito ##
    ## ===========================##
    
    st.subheader(f"Mapa de {input_inmueble} en Venta en {input_distrito}", divider="blue")
    
    df_filtrado_venta_map = df_filtrado_venta.copy()
    
    # Normaliza status y valida lat/lon
    status_validos = {'geo', 'ok', 'geocoded', 'found'}  # ajusta según tus valores reales
    df_filtrado_venta_map['status'] = df_filtrado_venta_map['status'].astype(str).str.lower()

    gdf = df_filtrado_venta_map.loc[
        df_filtrado_venta_map['status'].isin(status_validos) &
        df_filtrado_venta_map['lat'].notna() &
        df_filtrado_venta_map['lon'].notna()
    ].copy()
    
    if gdf.empty:
        st.info("No hay propiedades con geolocalización válida para graficar.")
    else:
        precio_pen_col = "precio_pen" if "precio_pen" in df_filtrado_venta_map.columns else ("precio_pe" if "precio_pe" in df_filtrado_venta_map.columns else None)
        precio_usd_col = "precio_usd" if "precio_usd" in df_filtrado_venta_map.columns else ("dolares" if "dolares" in df_filtrado_venta_map.columns else None)
        cols_extra = [c for c in ["fuente", "domitorio_min", precio_pen_col, precio_usd_col, "enlace", "caracteristica"] if c and c in df_filtrado_venta_map.columns]

        # Centro del mapa
        center_lat, center_lon = gdf['lat'].mean(), gdf['lon'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='OpenStreetMap')

        # Controles útiles
        # Fullscreen().add_to(m)
        # MiniMap(toggle_display=True).add_to(m)
        # MeasureControl(primary_length_unit='meters').add_to(m)
        LocateControl().add_to(m)

        # Cluster de marcadores
        cluster = MarkerCluster(name="Propiedades").add_to(m)

        # Función para color (ejemplo: por operación si existe la columna)
        def color_marker(row):
            if 'operacion' in row and isinstance(row['operacion'], str):
                op = row['operacion'].lower()
                if 'alquiler' in op: return 'blue'
                if 'venta' in op: return 'green'
            return 'red'

        # Construye popup/tooltip seguros
        def safe(x): 
            return "" if pd.isna(x) else str(x)
        
        def fmt_money(x, symbol):
            if pd.isna(x): return "-"
            s = f"{symbol} {x:,.0f}".replace(",", "X").replace(".", ",").replace("X",".")
            return s

        for _, r in gdf.iterrows():
            precio_pen = fmt_money(r.get(precio_pen_col), "S/.") if precio_pen_col else "-"
            precio_usd = fmt_money(r.get(precio_usd_col), "US$") if precio_usd_col else "-"
            gmaps_q = quote(f"{r['direccion']}, Lima, Perú")
            popup_html = f"""
            <b>Dirección:</b> {r['direccion']}<br>
            <b>Caracteristicas:</b> {r.get('caracteristica','-')}<br>
            <b>Precio PEN:</b> {safe(r.get('precio_pen'))}<br/>
            <b>Precio USD:</b> {safe(r.get('precio_usd'))}<br/>
            <b>Dirección:</b> {safe(r.get('direccion_fix') or r.get('direccion'))}<br/>
            <b>Enlace:</b> <a href="{r['enlace']}" target="_blank">Abrir en {r.get('fuente','-')}</a><br>
            <a href="https://www.google.com/maps/search/?api=1&query={gmaps_q}" target="_blank">Abrir en Google Maps</a>
            """

            folium.CircleMarker(
                location=[r['lat'], r['lon']],
                radius=5,
                color=color_marker(r),
                fill=True,
                fill_opacity=0.8,
                tooltip=safe(r.get('direccion_fix') or r.get('direccion')),
                popup=folium.Popup(popup_html, max_width=350),
            ).add_to(cluster)

        # Render en Streamlit
        st_folium(m, height=600, use_container_width=True)
