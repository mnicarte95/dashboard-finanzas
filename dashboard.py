# =========================================================
# 📊 DASHBOARD FINANCIERO FINAL (CORREGIDO Y OPTIMIZADO)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# =========================================================
# 🎨 COLORES PROFESIONALES
# =========================================================
COLOR_AZUL = "#1f4e79"
COLOR_VERDE = "#2ecc71"
COLOR_GRIS = "#7f8c8d"

st.title("📊 Dashboard Ejecutivo Financiero")

# =========================================================
# 📂 CARGA Y LIMPIEZA DE COLUMNAS (Evita espacios en blanco)
# =========================================================
@st.cache_data
def cargar_datos():
    ventas = pd.read_excel("Ventas.xlsx")
    costos = pd.read_excel("Costos.xlsx")
    eerr = pd.read_excel("EERR.xlsx")
    balance = pd.read_excel("Balance.xlsx")
    
    # Limpiar espacios en los nombres de columnas
    for df in [ventas, costos, eerr, balance]:
        df.columns = df.columns.str.strip()
    return ventas, costos, eerr, balance

try:
    ventas_raw, costos_raw, eerr_raw, balance_raw = cargar_datos()
except Exception as e:
    st.error(f"Error al cargar los archivos Excel. Asegúrate de que estén en la misma carpeta. Detalle: {e}")
    st.stop()

# Copias para no mutar el cache
ventas = ventas_raw.copy()
costos = costos_raw.copy()
eerr = eerr_raw.copy()
balance = balance_raw.copy()

# Renombrar
ventas.rename(columns={"Fecha": "fecha", "Unidades vendidas": "unidades", "Ingreso neto (CLP)": "ingreso_neto", "Región": "region", "Tipo de servicio": "servicio"}, inplace=True)
costos.rename(columns={"Fecha": "fecha", "Región": "region", "Tipo de servicio": "servicio", "Costo directo (CLP)": "costo_directo", "Costo indirecto (CLP)": "costo_indirecto", "Costo de transporte total (CLP)": "costo_transporte"}, inplace=True)
eerr.rename(columns={"Mes": "mes", "Grupo": "grupo", "Cuenta": "cuenta", "Monto (CLP)": "monto"}, inplace=True)
balance.rename(columns={"Mes": "mes", "Grupo": "grupo", "Cuenta": "cuenta", "Monto (CLP)": "monto"}, inplace=True)

# =========================================================
# 📅 CONVERSIÓN DE FECHAS
# =========================================================
def convertir_fecha(df, col):
    if not np.issubdtype(df[col].dtype, np.datetime64):
        df[col] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df[col], unit="D")
    return df

ventas = convertir_fecha(ventas, "fecha")
costos = convertir_fecha(costos, "fecha")

ventas["mes"] = ventas["fecha"].dt.month
costos["mes"] = costos["fecha"].dt.month

# Mapa de meses largo a número
mapa = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
eerr["mes"] = eerr["mes"].map(mapa)
balance["mes"] = balance["mes"].map(mapa)

eerr = eerr.dropna(subset=["mes"]).astype({"mes": int})
balance = balance.dropna(subset=["mes"]).astype({"mes": int})

# =========================================================
# 🎛️ FILTROS GLOBALES (Se aplican uniformemente)
# =========================================================
st.sidebar.header("Filtros Generales")

todos_los_meses = sorted(list(set(ventas["mes"].unique()).union(set(eerr["mes"].unique()))))
mes_sel = st.sidebar.multiselect("Meses a Analizar", todos_los_meses, default=todos_los_meses)
region_sel = st.sidebar.multiselect("Región", ventas["region"].unique(), default=ventas["region"].unique())
servicio_sel = st.sidebar.multiselect("Servicio", ventas["servicio"].unique(), default=ventas["servicio"].unique())

# Filtrado de Dataframes respetando si tienen o no la columna
ventas_f = ventas[(ventas["mes"].isin(mes_sel)) & (ventas["region"].isin(region_sel)) & (ventas["servicio"].isin(servicio_sel))]
costos_f = costos[(costos["mes"].isin(mes_sel)) & (costos["region"].isin(region_sel)) & (costos["servicio"].isin(servicio_sel))]
eerr_f = eerr[eerr["mes"].isin(mes_sel)]
balance_f = balance[balance["mes"].isin(mes_sel)]

# =========================================================
# 📊 PROCESAMIENTO DEL MODELO FINANCIERO
# =========================================================
ventas_m = ventas_f.groupby("mes")["ingreso_neto"].sum().reset_index()
costos_f["costo_total"] = costos_f["costo_directo"] + costos_f["costo_indirecto"] + costos_f["costo_transporte"]
costos_m = costos_f.groupby("mes")["costo_total"].sum().reset_index()

df_global = pd.merge(ventas_m, costos_m, on="mes", how="outer").fillna(0)
df_global["utilidad"] = df_global["ingreso_neto"] - df_global["costo_total"]

# ROIC Dinámico basado en filtros de mes
utilidad_neta = eerr_f[eerr_f["cuenta"].str.contains("resultado", case=False, na=False)].groupby("mes")["monto"].sum().reset_index()
capital = balance_f[balance_f["grupo"].str.contains("patrimonio", case=False, na=False)].groupby("mes")["monto"].sum().reset_index()

df_roic = pd.merge(utilidad_neta, capital, on="mes", how="inner")
df_roic["roic"] = (df_roic["monto_x"] / df_roic["monto_y"] * 100).fillna(0)

# =========================================================
# 🧭 PESTAÑAS DE LA INTERFAZ
# =========================================================
tab1, tab2, tab3 = st.tabs(["📊 Resumen Ejecutivo", "🔍 Análisis Detallado", "📈 Proyección y Simulación"])

# ---------------------------------------------------------
# PESTAÑA 1: RESUMEN EJECUTIVO
# ---------------------------------------------------------
with tab1:
    st.subheader("Indicadores Clave de Rendimiento (KPIs)")
    
    v_totales = df_global['ingreso_neto'].sum()
    c_totales = df_global['costo_total'].sum()
    u_total = df_global['utilidad'].sum()
    
    # CORRECCIÓN FINANCIERA: Margen Real, no promedio de promedios
    margen_real = (u_total / v_totales * 100) if v_totales > 0 else 0
    roic_promedio = df_roic['roic'].mean() if not df_roic.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ventas Totales", f"${v_totales:,.0f}")
    col2.metric("Costos Totales", f"${c_totales:,.0f}")
    col3.metric("Utilidad Operativa", f"${u_total:,.0f}")
    col4.metric("Margen Real", f"{margen_real:.1f}%")
    col5.metric("ROIC Promedio", f"{roic_promedio:.1f}%")

    st.markdown("---")
    st.subheader("Tendencia Mensual de Ingresos vs Costos")
    st.plotly_chart(
        px.line(df_global, x="mes", y=["ingreso_neto", "costo_total"],
                labels={"value": "Monto (CLP)", "mes": "Mes"},
                color_discrete_sequence=[COLOR_AZUL, COLOR_GRIS]),
        use_container_width=True
    )

    st.subheader("Evolución de la Utilidad Neta")
    st.plotly_chart(
        px.bar(df_global, x="mes", y="utilidad",
               labels={"utilidad": "Utilidad (CLP)", "mes": "Mes"},
               color_discrete_sequence=[COLOR_VERDE]),
        use_container_width=True
    )

# ---------------------------------------------------------
# PESTAÑA 2: ANÁLISIS DETALLADO
# ---------------------------------------------------------
with tab2:
    st.subheader("Rentabilidad por Tipo de Servicio")
    
    rent_serv = ventas_f.groupby("servicio")["ingreso_neto"].sum().reset_index()
    cost_serv = costos_f.groupby("servicio")["costo_total"].sum().reset_index()
    df_serv = pd.merge(rent_serv, cost_serv, on="servicio", how="outer").fillna(0)
    df_serv["utilidad"] = df_serv["ingreso_neto"] - df_serv["costo_total"]

    st.plotly_chart(
        px.bar(df_serv, x="servicio", y="utilidad",
               title="Utilidad Neta por Unidad de Negocio / Servicio",
               color_discrete_sequence=[COLOR_AZUL]),
        use_container_width=True
    )

    st.subheader("Rendimiento por Trimestre")
    ventas_f["trimestre"] = ((ventas_f["mes"] - 1) // 3) + 1
    ventas_trim = ventas_f.groupby("trimestre")["ingreso_neto"].sum().reset_index()
    
    st.plotly_chart(
        px.bar(ventas_trim, x="trimestre", y="ingreso_neto",
               title="Ingresos Consolidados por Trimestre (Q)",
               color_discrete_sequence=[COLOR_GRIS]),
        use_container_width=True
    )

# ---------------------------------------------------------
# PESTAÑA 3: PROYECCIÓN Y ESTRATEGIA
# ---------------------------------------------------------
with tab3:
    st.subheader("Eficiencia del Capital vs Tamaño del Patrimonio")
    if not df_roic.empty:
        st.plotly_chart(
            px.scatter(df_roic, x="monto_y", y="roic",
                       labels={"monto_y": "Monto Patrimonio (CLP)", "roic": "ROIC (%)"},
                       color_discrete_sequence=[COLOR_VERDE]),
            use_container_width=True
        )
    else:
        st.warning("No hay suficientes datos de Balance/EERR para graficar el ROIC.")

    st.markdown("---")
    st.subheader("Simulador de Escenarios Financieros (Stress Test)")
    
    # COLOCACIÓN CORRECTA DE SLIDERS ANTES DE LOS CÁLCULOS
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        v_ventas = st.slider("Variación proyectada en Ventas (%)", -50, 50, 0, step=5)
    with col_s2:
        v_costos = st.slider("Variación proyectada en Costos (%)", -50, 50, 0, step=5)

    df_sim = df_global.copy()
    df_sim["ventas_sim"] = df_sim["ingreso_neto"] * (1 + v_ventas / 100)
    df_sim["costos_sim"] = df_sim["costo_total"] * (1 + v_costos / 100)
    df_sim["utilidad_sim"] = df_sim["ventas_sim"] - df_sim["costos_sim"]

    st.metric("Utilidad Simulada Bajo Escenario", f"${df_sim['utilidad_sim'].sum():,.0f}")

    st.markdown("---")
    st.subheader("Proyección Automática de Tendencia")
    
    if len(df_global) > 1:
        tendencia = df_global["ingreso_neto"].pct_change().mean()
        proy = df_global["ingreso_neto"].iloc[-1] * (1 + tendencia)
        st.metric(f"Ingreso Proyectado (Mes {int(df_global['mes'].iloc[-1]+1)})", f"${proy:,.0f}", f"{tendencia*100:+.1f}% tendencia")
    else:
        st.info("Se necesitan datos de más de un mes para calcular una tendencia de proyección.")

    st.info("""
    💡 **Nota Estratégica:** La empresa presenta una operación comercial saludable en márgenes, 
    pero la dispersión en el ROIC sugiere la necesidad de optimizar el uso de los activos fijos 
    o el capital de trabajo retenido en el patrimonio.
    """)
