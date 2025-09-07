
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
import plotly.express as px
import base64


st.set_page_config(layout="wide")

IMG_PATH = Path(r"C:\Users\PC\Desktop\Proyectos\Proyectos_Py\6.Analisis_Alquiler_Venta\vivienda\vivienda\img\calles.png")

# Convertir a base64 para embeberla en el HTML (funciona igual en deploy)
def get_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_base64(IMG_PATH)

# HTML + CSS responsivo
st.markdown(
    f"""
    <div class="banner"></div>
    <style>
        .banner {{
            width: 100%;
            height: 220px;  /* Ajusta la altura a tu gusto */
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;   /* Se adapta al ancho */
            background-position: center; /* Centrado */
            border-radius: 10px; /* opcional: esquinas redondeadas */
        }}
    </style>
    """,
    unsafe_allow_html=True
)

## Titulo
st.set_page_config(layout="wide")
st.title("Análisis Inmobiliario 🏡📊")

"""
Bienvenido a la plataforma interactiva de análisis inmobiliario de Lima.  

Aquí podrás explorar **departamentos, casas y terrenos** en venta y alquiler, con datos reales y actualizados. 
Esta es una herramienta diseñada para ayudarte a entender **cómo se mueve el mercado inmobiliario en Lima**, detectar oportunidades y tomar mejores decisiones.  

Las fuentes que se usaron para recopilar esta información al 19 de agosto de 2025 fueron: 
- 🏡 [Urbania](https://urbania.pe)
- 🏠 [Adondevivir](https://www.adondevivir.com)

La aplicación te permite:

- 📍 Visualizar la distribución geográfica de las propiedades en los distintos distritos.  
- 💰 Comparar precios en **soles** (alquiler) y **dólares** (venta), con métricas como precio por m² y variación.  
- 📐 Filtrar fácilmente por área, dormitorios, baños, estacionamientos y mantenimiento.  
- 🔗 Acceder directamente al anuncio original de cada propiedad.  

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
    
    # --- MEJORA: Deduplicación de Anuncios ---
    # Identificamos y eliminamos anuncios duplicados que aparecen en múltiples fuentes (ej. Urbania y Adondevivir). 
    # Un anuncio se considera único por la combinación de su dirección, área, precios y tipo de operación.
    # Mantenemos la primera aparición ('first') que encuentre pandas.
    subset_cols = ['distrito_oficial', 'direccion']
    
    # Eliminamos los duplicados basándonos en las columnas clave.
    # `inplace=True` modifica el DataFrame directamente.
    df.drop_duplicates(subset=subset_cols, keep='first', inplace=True)

    # --- MEJORA: Creación de Categoría de Distrito ---
    # Se crea una nueva columna 'distrito_categoria' para segmentar los distritos en zonas de Lima.
    zonas_lima = {
        'Lima Top': ['Miraflores', 'San Isidro', 'La Molina', 'Santiago de Surco', 'San Borja', 'Barranco'],
        'Lima Moderna': ['Jesús María', 'Lince', 'Magdalena', 'San Miguel', 'Pueblo Libre', 'Surquillo'],
        'Lima Centro': ['Lima Cercado', 'Breña', 'La Victoria', 'Rímac', 'San Luis'],
        'Lima Este': ['Ate Vitarte', 'Cieneguilla', 'Chaclacayo', 'Chosica Lurigancho', 'Santa Anita', 'El Agustino', 'San Juan de Lurigancho'],
        'Lima Norte': ['Carabayllo', 'Comas', 'Independencia', 'Los Olivos', 'Puente Piedra', 'San Martín de Porres', 'Ancón', 'Santa Rosa'],
        'Lima Sur': ['Chorrillos', 'Lurín', 'Pachacámac', 'San Juan de Miraflores', 'Villa El Salvador', 'Villa María del Triunfo', 'Pucusana', 'Punta Hermosa', 'Punta Negra', 'San Bartolo', 'Santa María del Mar']
    }

    # Se crea un mapeo inverso (distrito -> zona) para una asignación eficiente.
    distrito_a_zona = {distrito: zona for zona, distritos_en_zona in zonas_lima.items() for distrito in distritos_en_zona}
    # Se aplica el mapeo para crear la nueva columna.
    df['distrito_categoria'] = df['distrito_oficial'].map(distrito_a_zona).fillna('Otra Zona')
    df['distrito_categoria'] = df['distrito_categoria'].astype('category')

    # --- MEJORA: Creación de columnas de agrupación para filtros ---
    # Se crean columnas categóricas para los rangos de precio y área, que se usarán en los filtros de las pestañas.
    df['precio_pen'] = pd.to_numeric(df['precio_pen'], errors='coerce')
    df['precio_usd'] = pd.to_numeric(df['precio_usd'], errors='coerce')
    df['area'] = pd.to_numeric(df['area'], errors='coerce')

    # Bins y labels para precio de alquiler (Soles)
    bins_alquiler = [-1, 1000, 2500, 5000, 10000, float('inf')]
    labels_alquiler = ["Hasta S/ 1000", "De S/ 1000 a S/ 2500", "De S/ 2500 a S/ 5000", "De S/ 5000 a S/ 10000", "De S/ 10000 a más"]
    df['precio_alquiler_agp'] = pd.cut(df['precio_pen'], bins=bins_alquiler, labels=labels_alquiler, right=False)

    # Bins y labels para precio de venta (Dólares)
    bins_venta = [-1, 50000, 100000, 200000, 500000, float('inf')]
    labels_venta = ["Hasta $ 50k", "De $ 50k a $ 100k", "De $ 100k a $ 200k", "De $ 200k a $ 500k", "De $ 500k a más"]
    df['precio_venta_agp'] = pd.cut(df['precio_usd'], bins=bins_venta, labels=labels_venta, right=False)

    # Bins y labels para área (m²)
    bins_area = [-1, 50, 100, 200, 300, float('inf')]
    labels_area = ["Hasta 50m2", "De 50m2 a 100m2", "De 100m2 a 200m2", "De 200m2 a 300m2", "De 300m2 a más"]
    df['area_agp'] = pd.cut(df['area'], bins=bins_area, labels=labels_area, right=False)

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

    df_kpi = df.copy()
    df_kpi[price_col] = pd.to_numeric(df_kpi[price_col], errors="coerce")
    df_kpi.dropna(subset=[price_col], inplace=True)

    st.subheader(title, divider="blue")

    if df_kpi.empty:
        st.info("No hay datos de precios para mostrar KPIs.")
        return

    # --- MEJORA: Calcular métricas globales para comparación ---
    df_global = data[
        (data["inmueble"] == inmueble) &
        (data["operacion"] == operation)
    ].copy()
    
    
    df_global[price_col] = pd.to_numeric(df_global[price_col], errors="coerce")
    global_avg = df_global[price_col].mean()
    global_md = df_global[price_col].median()

    # --- Cálculo de métricas locales ---
    
    fmt = lambda x: f"{symbol} {x:,.0f}"
    
    district_avg = df_kpi[price_col].mean()
    delta_avg = district_avg - global_avg

    district_md = df_kpi[price_col].median()
    delta_md = district_md - global_md
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(f"🚪 Total {inmueble}", len(df_kpi))
    with c2: st.metric("📉 Mínimo", fmt(df_kpi[price_col].min()))
    with c3: st.metric("📈 Máximo", fmt(df_kpi[price_col].max()))
    
    c4, c5 = st.columns(2)
    with c4: 
        st.metric(
            label="📊 Promedio", 
            value=fmt(district_avg), 
            delta=f"{delta_avg:,.0f} vs. promedio general",
        )
    with c5: 
        st.metric(
            label="📊 Mediana", 
            value=fmt(district_md), 
            delta=f"{delta_md:,.0f} vs. mediana general",
        )

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
    
    MiniMap(toggle_display=True).add_to(m)
    Fullscreen(position='topright').add_to(m)

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

## ==================##
##      Pestañas     ##
## ==================##
    
tab1, tab2, tab3 = st.tabs(["🔎 Análisis Distrito", "📦 Alquiler", "📊 Venta"])


## ===========================##
##      Analisis Distrito     ##
## ===========================##


with tab1:

    c1, c2, c3 = st.columns(3, gap="small")
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
        
    with c3:
        st.markdown("**Zona de Lima**")
        # Usamos la nueva columna 'distrito_categoria' para el filtro
        zonas = ['Todos','Lima Top', 'Lima Moderna', 'Lima Centro',  'Lima Este', 'Lima Norte',  'Lima Sur']
        input_zona = st.selectbox(
            "Zona"
            , zonas
            , key="f_zona"
            , label_visibility="collapsed"
            , index=0
        )

    col_precio = "precio_usd" if input_operacion == "venta" else "precio_pen"
    simbolo   = "US$" if input_operacion == "venta" else "S/"
    
    
    ## Filtrado de Alquiler
    if input_zona == "Todos":
        df_filtrado = data[
            (data["inmueble"] == input_inmueble) &
            (data["operacion"] == input_operacion) 
        ].copy()
        
    else:
        df_filtrado = data[
            (data["inmueble"] == input_inmueble) &
            (data["operacion"] == input_operacion) &
            (data["distrito_categoria"] == input_zona) # Filtro por la nueva zona
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
    
    st.subheader(f"Resumen de {input_inmueble} en {input_operacion} para **{input_zona}**")
    
    st.data_editor(
        data_agrupada_df_fmt.sort_values("n", ascending=False),
        use_container_width=True,
        column_config={
            "distrito_oficial": st.column_config.TextColumn("Distrito", disabled=True)
        },
        disabled=True,
        key="data_agrupada_fmt"
    )
    
    
    st.subheader("Análisis Gráfico Interactivo", divider="blue")

    if df_filtrado.empty:
        st.warning("No hay datos suficientes para generar gráficos con los filtros seleccionados.")
    else:
        # Gráfico 1: Distribución de Precios por Distrito (Box Plot)
        # Este gráfico es ideal para comparar la dispersión de precios entre distritos.
        st.markdown(f"##### Distribución de Precios de {input_inmueble} en {input_operacion}")
        fig1 = px.box(df_filtrado, 
                    x="distrito_oficial", 
                    y=col_precio,
                    color="distrito_oficial",
                    points="all",
                    labels={"distrito_oficial": "Distrito", col_precio: f"Precio ({simbolo})"})
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

        # --- Columnas para los siguientes gráficos ---
        g1, g2 = st.columns(2)

        with g1:
            # Gráfico 2: Número de Propiedades por Distrito (Bar Chart)
            st.markdown("##### Cantidad de Propiedades por Distrito")
            prop_por_distrito = df_filtrado['distrito_oficial'].value_counts()
            st.bar_chart(prop_por_distrito)

        with g2:
            # Gráfico 3: Precio Promedio por m² por Distrito (Bar Chart)
            st.markdown(f"##### Precio Promedio por m² ({simbolo})")
            df_plot = df_filtrado[(df_filtrado['area'] > 0) & (df_filtrado[col_precio] > 0)].copy()
            if not df_plot.empty:
                df_plot['precio_m2'] = round(df_plot[col_precio] / df_plot['area'],2)
                precio_m2_distrito = df_plot.groupby('distrito_oficial')['precio_m2'].mean().round(2).sort_values(ascending=False)
                st.bar_chart(precio_m2_distrito)
            else:
                st.info("No hay datos de área o precio para calcular el precio por m².")

        # Gráfico 4: Relación Área vs. Precio (Scatter Plot)
        st.markdown(f"##### Relación Área vs. Precio para {input_inmueble}")
        # Filtrar outliers para una mejor visualización, mostrando el 95% de los datos
        area_limite = df_filtrado['area'].quantile(0.95)
        precio_limite = df_filtrado[col_precio].quantile(0.95)
        
        df_scatter = df_filtrado[
            (df_filtrado['area'] > 0) & (df_filtrado[col_precio] > 0) &
            (df_filtrado['area'] <= area_limite) & 
            (df_filtrado[col_precio] <= precio_limite)
        ].copy()

        if not df_scatter.empty:
            fig4 = px.scatter(df_scatter, x="area", y=col_precio, color="distrito_oficial",
                            hover_data=['direccion'], title=f"Precio vs. Área (mostrando el 95% de los datos)",
                            labels={"area": "Área (m²)", col_precio: f"Precio ({simbolo})"})
            st.plotly_chart(fig4, use_container_width=True)
    
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
            , key="rango_precio_alquiler" # <- Clave única para el widget
            , index=0
        )
        
    with d2:
        st.markdown("**Área**")       
        labels_area = ["Todos", "Hasta 50m2", "De 50m2 a 100m2", "De 100m2 a 200m2", "De 200m2 a 300m2", "De 300m2 a más"]
        input_rango_area_alquiler = st.selectbox(
            "seleccione el area:"
            , options=labels_area
            , key="rango_area_alquiler" # <- Clave única para el widget
            , index=0 
            
        )
        
    # Se crea una copia del DataFrame filtrado por distrito para aplicar los filtros de rango.
    df_tabla_alquiler = df_filtrado_aquiler.copy()

    # Se aplica el filtro de rango de precio si no es "Todos".
    if input_rango_precio_aquiler != "Todos":
        df_tabla_alquiler = df_tabla_alquiler[df_tabla_alquiler["precio_alquiler_agp"] == input_rango_precio_aquiler]

    # Se aplica el filtro de rango de área si no es "Todos".
    if input_rango_area_alquiler != "Todos":
        df_tabla_alquiler = df_tabla_alquiler[df_tabla_alquiler["area_agp"] == input_rango_area_alquiler]

    # Usamos la función refactorizada para mostrar la tabla
    display_details_table(df_tabla_alquiler, "alquiler")
    
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
        # Se corrigen las etiquetas para que los rangos no se superpongan.
        labels_venta_precio = ["Todos", "Hasta $ 50k", "De $ 50k a $ 100k", "De $ 100k a $ 200k", "De $ 200k a $ 500k", "De $ 500k a más"]
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
        
    # Se crea una copia del DataFrame filtrado por distrito para aplicar los filtros de rango.
    df_tabla_venta = df_filtrado_venta.copy()

    # Se aplica el filtro de rango de precio si no es "Todos".
    if input_rango_precio_venta != "Todos":
        df_tabla_venta = df_tabla_venta[df_tabla_venta["precio_venta_agp"] == input_rango_precio_venta]

    # Se aplica el filtro de rango de área si no es "Todos".
    if input_rango_area_venta != "Todos":
        df_tabla_venta = df_tabla_venta[df_tabla_venta["area_agp"] == input_rango_area_venta]

    
    # Usamos la función refactorizada para mostrar la tabla
    display_details_table(df_tabla_venta, "venta")
    
    ## ===========================##
    ## Mapa de Venta por Distrito ##
    ## ===========================##
    
    st.subheader(f"Mapa de {input_inmueble} en Venta en {input_distrito}", divider="blue")
    
    # Usamos la función refactorizada para crear el mapa
    create_map(df_filtrado_venta)
