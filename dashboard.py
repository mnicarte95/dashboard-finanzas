# =========================================================
# 📊 DASHBOARD NIVEL SOCIO - FINANZAS
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# =========================================================
# 🎨 ESTILO
# =========================================================
PRIMARY = "#0b3c5d"
SUCCESS = "#27ae60"
DANGER = "#e74c3c"
ACCENT = "#f39c12"

st.markdown(f"<h1 style='color:{PRIMARY};'>📊 Reporte Ejecutivo</h1>", unsafe_allow_html=True)

# =========================================================
# 📂 CARGA
# =========================================================
ventas = pd.read_excel("Ventas.xlsx")
costos = pd.read_excel("Costos.xlsx")
eerr = pd.read_excel("EERR.xlsx")
balance = pd.read_excel("Balance.xlsx")

# =========================================================
# 🧹 LIMPIEZA
# =========================================================

ventas.rename(columns={
    "Fecha": "fecha",
    "Unidades vendidas": "unidades",
    "Ingreso neto (CLP)": "ingreso_neto",
    "Región": "region",
    "Tipo de servicio": "servicio"
}, inplace=True)

costos.rename(columns={
    "Fecha": "fecha",
    "Región": "region",
    "Tipo de servicio": "servicio",
    "Costo directo (CLP)": "costo_directo",
    "Costo indirecto (CLP)": "costo_indirecto",
    "Costo de transporte total (CLP)": "costo_transporte"
}, inplace=True)

eerr.rename(columns={
    "Mes": "mes",
    "Grupo": "grupo",
    "Cuenta": "cuenta",
    "Monto (CLP)": "monto"
}, inplace=True)

balance.rename(columns={
    "Mes": "mes",
    "Grupo": "grupo",
    "Cuenta": "cuenta",
    "Monto (CLP)": "monto"
}, inplace=True)

# =========================================================
# 📅 FECHAS SEGURAS
# =========================================================
def convertir_fecha(df, col):
    if not np.issubdtype(df[col].dtype, np.datetime64):
        df[col] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df[col], unit="D")
    else:
        df[col] = pd.to_datetime(df[col])
    return df

ventas = convertir_fecha(ventas, "fecha")
costos = convertir_fecha(costos, "fecha")

# =========================================================
# 📆 MES
# =========================================================
ventas["mes"] = ventas["fecha"].dt.month
costos["mes"] = costos["fecha"].dt.month

# ✅ convertir meses texto → número
mapa_meses = {
    "January": 1, "February": 2, "March": 3,
    "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9,
    "October": 10, "November": 11, "December": 12
}

if eerr["mes"].dtype == object:
    eerr["mes"] = eerr["mes"].map(mapa_meses)

# ✅ eliminar nulos
eerr = eerr.dropna(subset=["mes"])

# ✅ convertir a entero (CLAVE)
eerr["mes"] = eerr["mes"].astype(int)


if balance["mes"].dtype == object:
    balance["mes"] = balance["mes"].map(mapa_meses)

balance = balance.dropna(subset=["mes"])
balance["mes"] = balance["mes"].astype(int)


# eliminar nulos después de map
eerr = eerr.dropna(subset=["mes"])
balance = balance.dropna(subset=["mes"])

# =========================================================
# 🎛️ FILTROS
# =========================================================
st.sidebar.header("Filtros")

mes = st.sidebar.multiselect("Mes", sorted(ventas["mes"].unique()), default=sorted(ventas["mes"].unique()))
region = st.sidebar.multiselect("Región", ventas["region"].unique(), default=ventas["region"].unique())

ventas = ventas[(ventas["mes"].isin(mes)) & (ventas["region"].isin(region))]
costos = costos[(costos["mes"].isin(mes)) & (costos["region"].isin(region))]

# =========================================================
# 📊 MODELO
# =========================================================

ventas_m = ventas.groupby("mes")["ingreso_neto"].sum().reset_index()

costos["costo_total"] = (
    costos["costo_directo"] +
    costos["costo_indirecto"] +
    costos["costo_transporte"]
)

costos_m = costos.groupby("mes")["costo_total"].sum().reset_index()

df = pd.merge(ventas_m, costos_m, on="mes")
df["mes"] = df["mes"].astype(int)
df["utilidad"] = df["ingreso_neto"] - df["costo_total"]
df["margen"] = df["utilidad"] / df["ingreso_neto"] * 100

# =========================================================
# 💰 EBITDA (robusto)
# =========================================================

ebitda = eerr[eerr["cuenta"].str.contains("resultado|ebitda", case=False, na=False)]
ebitda = ebitda.groupby("mes")["monto"].sum().reset_index()
# ✅ convertir meses texto → número
mapa_meses = {
    "January": 1, "February": 2, "March": 3,
    "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9,
    "October": 10, "November": 11, "December": 12
}

# aplicar solo si es texto
if eerr["mes"].dtype == object:
    eerr["mes"] = eerr["mes"].map(mapa_meses)

# eliminar nulos
eerr = eerr.dropna(subset=["mes"])
df = pd.merge(df, ebitda, on="mes", how="left")

# =========================================================
# 🏦 ROIC
# =========================================================

utilidad_neta = eerr[eerr["cuenta"].str.contains("resultado", case=False, na=False)]
utilidad_neta = utilidad_neta.groupby("mes")["monto"].sum().reset_index()

capital = balance[balance["grupo"].str.contains("patrimonio", case=False, na=False)]
capital = capital.groupby("mes")["monto"].sum().reset_index()

roic = pd.merge(utilidad_neta, capital, on="mes")
roic["roic"] = roic["monto_x"] / roic["monto_y"] * 100

# =========================================================
# 📊 KPIs
# =========================================================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Ventas", f"${df['ingreso_neto'].sum():,.0f}")
col2.metric("Costos", f"${df['costo_total'].sum():,.0f}")
col3.metric("Utilidad", f"${df['utilidad'].sum():,.0f}")
col4.metric("Margen", f"{df['margen'].mean():.1f}%")
col5.metric("ROIC", f"{roic['roic'].mean():.1f}%")

# =========================================================
# 📈 VISUALES
# =========================================================

st.plotly_chart(px.line(df, x="mes", y=["ingreso_neto","costo_total"], title="Ingresos vs Costos"), use_container_width=True)

st.plotly_chart(px.bar(df, x="mes", y="utilidad", title="Utilidad"), use_container_width=True)

st.plotly_chart(px.line(roic, x="mes", y="roic", title="ROIC (%)"), use_container_width=True)

# =========================================================
# 🧪 SIMULADOR
# =========================================================

st.subheader("Simulación")

v_ventas = st.slider("Variación ventas %", -50, 50, 0)
v_costos = st.slider("Variación costos %", -50, 50, 0)

df_sim = df.copy()

df_sim["ventas_sim"] = df_sim["ingreso_neto"]*(1+v_ventas/100)
df_sim["costos_sim"] = df_sim["costo_total"]*(1+v_costos/100)
df_sim["utilidad_sim"] = df_sim["ventas_sim"] - df_sim["costos_sim"]
df_sim["margen_sim"] = df_sim["utilidad_sim"]/df_sim["ventas_sim"]*100

st.metric("Utilidad simulada", f"${df_sim['utilidad_sim'].sum():,.0f}")
st.metric("Margen simulado", f"{df_sim['margen_sim'].mean():.1f}%")

st.plotly_chart(px.line(df_sim, x="mes", y=["utilidad","utilidad_sim"], title="Escenario"), use_container_width=True)

# =========================================================
# 🔮 PROYECCIÓN
# =========================================================

st.subheader("Proyección")

tendencia = df["ingreso_neto"].pct_change().mean()
proy = df["ingreso_neto"].iloc[-1] * (1 + tendencia)

st.metric("Ingreso próximo mes", f"${proy:,.0f}")

# =========================================================
# 🧠 DIAGNÓSTICO
# =========================================================

st.subheader("Diagnóstico")

if df["margen"].mean() > 70:
    st.warning("Margen muy alto: revisar costos")

if df["ingreso_neto"].pct_change().mean() > 0:
    st.success("Empresa en crecimiento")
else:
    st.error("Caída en ingresos")

# =========================================================
# 📋 TABLA
# =========================================================

st.dataframe(df)
