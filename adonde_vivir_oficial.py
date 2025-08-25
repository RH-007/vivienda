
## Proyecto a Donde Vivir
## ==========================

## Liberias
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from streamlit_folium import st_folium
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

@st.cache_data # Decorador mágico de Streamlit
def load_data(path):
    """
    Carga los datos desde un archivo CSV.
    Gracias a @st.cache_data, esta función solo se ejecutará una vez
    y el resultado (el DataFrame) se guardará en memoria caché.
    Las siguientes veces que se necesiten los datos, se leerán directamente
    de la caché, haciendo la app mucho más rápida.
    """
    df = pd.read_csv(path, sep="|", encoding="utf-8")
    
    # OPTIMIZACIÓN OPCIONAL: Convertir columnas a tipos más eficientes
    # Esto reduce el uso de memoria y acelera los cálculos.
    # df['distrito_oficial'] = df['distrito_oficial'].astype('category')
    # df['inmueble'] = df['inmueble'].astype('category')
    # df['operacion'] = df['operacion'].astype('category')
    # df['area'] = pd.to_numeric(df['area'], errors='coerce', downcast='integer')
    
    return df

# Cargamos los datos usando nuestra función cacheada
data = load_data("./data/data_alquiler_venta.csv")

## Variables
distritos = data["distrito_oficial"].unique()
inmueble = data["inmueble"].unique()
operacion = data["operacion"].unique()

## ==================##
##    Funciones      ##
## ==================##

def create_map(df: pd.DataFrame):
    """Genera y muestra un mapa de Folium con las propiedades de un DataFrame."""
    
    # Filtra propiedades con geolocalización válida.
    status_validos = {'geo', 'ok', 'geocoded', 'found'}
    
    # .loc con una máscara booleana devuelve una copia. Se añade .copy() para ser explícitos.
    gdf = df.loc[
        df['status'].astype(str).str.lower().isin(status_validos) &
        df['lat'].notna() &
        df['lon'].notna()
    ].copy()
    
    if gdf.empty:
        st.info("No hay propiedades con geolocalización válida para graficar.")
        return

    # Centro del mapa
    center_lat, center_lon = gdf['lat'].mean(), gdf['lon'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles='OpenStreetMap')

    # Controles útiles
    LocateControl().add_to(m)

    # Cluster de marcadores
    cluster = MarkerCluster(name="Propiedades").add_to(m)

    # Construye popup/tooltip seguros
    def safe(x): 
        return "" if pd.isna(x) else str(x)

    for _, r in gdf.iterrows():
        gmaps_q = quote(f"{r.get('direccion', '')}, Lima, Perú")
        popup_html = f"""
        <b>Dirección:</b> {safe(r.get('direccion_fix') or r.get('direccion'))}<br>
        <b>Caracteristicas:</b> {r.get('caracteristica','-')}<br>
        <b>Precio PEN:</b> {f"S/ {r.get('precio_pen'):,.0f}" if pd.notna(r.get('precio_pen')) else '-'}<br/>
        <b>Precio USD:</b> {f"US$ {r.get('precio_usd'):,.0f}" if pd.notna(r.get('precio_usd')) else '-'}<br/>
        <b>Enlace:</b> <a href="{r['enlace']}" target="_blank">Abrir en {r.get('fuente','-')}</a><br>
        <a href="https://www.google.com/maps/search/?api=1&query={gmaps_q}" target="_blank">Abrir en Google Maps</a>
        """
        
        color = 'blue' if r.get('operacion') == 'alquiler' else 'green'

        folium.CircleMarker(
            location=[r['lat'], r['lon']],
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.8,
            tooltip=safe(r.get('direccion_fix') or r.get('direccion')),
            popup=folium.Popup(popup_html, max_width=350),
        ).add_to(cluster)

    st_folium(m, height=600, use_container_width=True)

def display_kpis(df: pd.DataFrame, operation: str, distrito: str, inmueble: str):
    """Calcula y muestra los KPIs de precios para una operación específica."""
    
    if operation == "alquiler":
        price_col = "precio_pen"
        symbol = "S/"
        title = f"KPIs de precios Alquiler ({symbol}) en {distrito}"
    else:  # venta
        price_col = "precio_usd"
        symbol = "$"
        title = f"KPIs de precios Venta ({symbol}) en {distrito}"

    st.subheader(title, divider="blue")
    
    df_kpi = df.copy()
    df_kpi[price_col] = pd.to_numeric(df_kpi[price_col], errors="coerce")
    df_kpi.dropna(subset=[price_col], inplace=True)

    if df_kpi.empty:
        st.info("No hay datos de precios para mostrar KPIs.")
        return

    fmt = lambda x: f"{symbol} {x:,.0f}"
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(f"Total {inmueble}", len(df_kpi), border=True)
    with c2: st.metric("Mínimo", fmt(df_kpi[price_col].min()), border=True)
    with c3: st.metric("Máximo", fmt(df_kpi[price_col].max()), border=True)
    
    c4, c5 = st.columns(2)
    with c4: st.metric("Promedio", fmt(df_kpi[price_col].mean()), border=True)
    with c5: st.metric("Mediana", fmt(df_kpi[price_col].median()), border=True)

def display_details_table(df: pd.DataFrame, operation: str):
    """Muestra la tabla de detalles de propiedades para una operación específica."""
    
    df_display = df.copy()

    # Configuración base común para ambas operaciones
    config = {
        "fuente": st.column_config.TextColumn("Fuente", disabled=True),
        "direccion": st.column_config.TextColumn("Dirección", disabled=True),
        "area": st.column_config.NumberColumn("Área", format="%d m²", width="small", disabled=True),
        "dormitorio": st.column_config.NumberColumn("Dorm.", width="small", disabled=True),
        "baños": st.column_config.NumberColumn("Baños", width="small", disabled=True),
        "estacionamientos": st.column_config.NumberColumn("Estac.", width="small", disabled=True),
        "caracteristica": st.column_config.TextColumn("Características", disabled=True),
        "enlace": st.column_config.LinkColumn("Anuncio", display_text="🔗 Abrir", validate=r"^https?://.*$"),
    }

    if operation == "alquiler":
        price_col = "precio_pen"
        cols_to_show = ["fuente", "direccion", "precio_pen", "area", "dormitorio", "baños", "estacionamientos", "mantenimiento", "caracteristica", "enlace"]
        config.update({
            "precio_pen": st.column_config.NumberColumn("Precio (S/.)", format="S/. %d", disabled=True),
            "mantenimiento": st.column_config.NumberColumn("Mant. (S/.)", format="S/. %d", disabled=True),
        })
    else:  # venta
        price_col = "precio_usd"
        cols_to_show = ["fuente", "direccion", "precio_usd", "area", "dormitorio", "baños", "estacionamientos", "caracteristica", "enlace"]
        config.update({
            "precio_usd": st.column_config.NumberColumn("Precio ($)", format="$ %d", disabled=True),
        })

    existing_cols = [col for col in cols_to_show if col in df_display.columns]
    
    st.data_editor(
        df_display[existing_cols].sort_values(price_col, ascending=True),
        hide_index=True, use_container_width=True, column_config=config, disabled=True
    )

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
    
    display_kpis(df_filtrado_aquiler, "alquiler", input_distrito, input_inmueble)
    
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
    
    # Usamos la función refactorizada para mostrar la tabla
    display_details_table(df_filtrado_aquiler, "alquiler")
    
    ## ==============================##
    ## Mapa de ALquiler por Distrito ##
    ## ==============================##
    
    st.subheader(f"Mapa de {input_inmueble} en Alquiler en {input_distrito}", divider="blue")
    
    # Usamos la función refactorizada para crear el mapa
    create_map(df_filtrado_aquiler)
    
    
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
    
    display_kpis(df_filtrado_venta, "venta", input_distrito, input_inmueble)

    ## ====================================##
    ## TABLA Detalle de Venta por Distrito ##
    ## ====================================##
    
    st.subheader(f"Lista de {input_inmueble} en Venta en {input_distrito}", divider="blue")
    
    e1, e2 = st.columns([2, 2], gap="small")
    with e1:
        st.markdown("**Precio**")
        labels_venta_precio = ["Todos", "Hasta $ 50k", "De $ 50k a $ 100k", "De $ 100k a $ 200k", "De $ 100k a $ 500k", "De $ 500k a más"]
        input_rango_precio_venta = st.selectbox(
            "seleccione el precio:"
            , options=labels_venta_precio
            , index=0
            , key="rango_precio_venta"
        )
        
    with e2:
        st.markdown("**Área**")       
        labels_area_venta = ["Todos", "Hasta 50m2", "De 50m2 a 100m2", "De 100m2 a 200m2", "De 200m2 a 300m2", "De 300m2 a más"]
        input_rango_area_venta = st.selectbox(
            "seleccione el area:"
            , options=labels_area_venta
            , index=0 
            , key="rango_area_venta"
        )
        
    ## Filtrado de Venta
    if input_rango_precio_venta == "Todos" and input_rango_area_venta == "Todos":
        df_filtrado_venta = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "venta")
        ].copy()
        
    else:
        df_filtrado_venta = data[
            (data["inmueble"] == input_inmueble) &
            (data["distrito_oficial"] == input_distrito) &
            (data["operacion"] == "venta") &
            (data["area_agp"] == input_rango_area_venta) &
            (data["precio_venta_agp"] == input_rango_precio_venta)
        ].copy()
    
    # Usamos la función refactorizada para mostrar la tabla
    display_details_table(df_filtrado_venta, "venta")
    
    ## ===========================##
    ## Mapa de Venta por Distrito ##
    ## ===========================##
    
    st.subheader(f"Mapa de {input_inmueble} en Venta en {input_distrito}", divider="blue")
    
    # Usamos la función refactorizada para crear el mapa
    create_map(df_filtrado_venta)
