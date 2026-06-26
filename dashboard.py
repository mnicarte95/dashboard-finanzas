# =========================================================
# 📊 DASHBOARD FINANZAS - FINAL PROFESIONAL
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# =========================================================
# 🎨 PALETA PROFESIONAL
# =========================================================
COLOR_AZUL = "#1f4e79"
COLOR_VERDE = "#2ecc71"
COLOR_GRIS = "#7f8c8d"

st.title("📊 Dashboard Ejecutivo Financiero")

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
# 📅 FECHAS
# =========================================================
def convertir_fecha(df, col):
    if not np.issubdtype(df[col].dtype, np.datetime64):
        df[col] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df[col], unit="D")
    return df

ventas = convertir_fecha(ventas, "fecha")
costos = convertir_fecha(costos, "fecha")

ventas["mes"] = ventas["fecha"].dt.month
costos["mes"] = costos["fecha"].dt.month

# =========================================================
# 🔧 MESES DESDE TEXTO
# =========================================================
mapa = {
    "January":1,"February":2,"March":3,"April":4,"May":5,
    "June":6,"July":7,"August":8,"September":9,
    "October":10,"November":11,"December":12
}

eerr["mes"] = eerr["mes"].map(mapa)
eerr = eerr.dropna(subset=["mes"])
eerr["mes"] = eerr["mes"].astype(int)

balance["mes"] = balance["mes"].map(mapa)
balance = balance.dropna(subset=["mes"])
balance["mes"] = balance["mes"].astype(int)

# =========================================================
# 🎛️ FILTROS (COMPLETOS)
# =========================================================
st.sidebar.header("Filtros")

mes = st.sidebar.multiselect(
    "Mes", sorted(ventas["mes"].unique()),
    default=sorted(ventas["mes"].unique())
)

region = st.sidebar.multiselect(
    "Región", ventas["region"].unique(),
    default=ventas["region"].unique()
)

servicio = st.sidebar.multiselect(
    "Tipo de servicio", ventas["servicio"].unique(),
    default=ventas["servicio"].unique()
)

ventas = ventas[
    (ventas["mes"].isin(mes)) &
    (ventas["region"].isin(region)) &
    (ventas["servicio"].isin(servicio))
]

costos = costos[
    (costos["mes"].isin(mes)) &
    (costos["region"].isin(region)) &
    (costos["servicio"].isin(servicio))
]

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

df["utilidad"] = df["ingreso_neto"] - df["costo_total"]
df["margen"] = df["utilidad"] / df["ingreso_neto"] * 100

# =========================================================
# 💰 EBITDA
# =========================================================
ebitda = eerr[eerr["cuenta"].str.contains("resultado|ebitda", case=False, na=False)]
ebitda = ebitda.groupby("mes")["monto"].sum().reset_index()

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
# ✅ KPIs
# =========================================================
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Ventas", f"${df['ingreso_neto'].sum():,.0f}")
col2.metric("Costos", f"${df['costo_total'].sum():,.0f}")
col3.metric("Utilidad", f"${df['utilidad'].sum():,.0f}")

margen = df["margen"].mean()
if margen > 30:
    col4.metric("Margen", f"{margen:.1f}%", "🟢")
elif margen > 10:
    col4.metric("Margen", f"{margen:.1f}%", "🟡")
else:
    col4.metric("Margen", f"{margen:.1f}%", "🔴")

roic_val = roic["roic"].mean()
if roic_val < 0:
    col5.metric("ROIC", f"{roic_val:.1f}%", "🔴")
else:
    col5.metric("ROIC", f"{roic_val:.1f}%", "🟢")

# =========================================================
# 📊 VISTA 1
# =========================================================
st.subheader("📈 Evolución")

st.plotly_chart(
    px.line(df, x="mes", y=["ingreso_neto","costo_total"],
            color_discrete_sequence=[COLOR_AZUL, COLOR_GRIS]),
    use_container_width=True
)

st.plotly_chart(
    px.bar(df, x="mes", y="utilidad",
           color_discrete_sequence=[COLOR_VERDE]),
    use_container_width=True
)

# =========================================================
# 📊 VISTA 2
# =========================================================
st.subheader("📊 Análisis Detallado")

# Rentabilidad por servicio
rent_serv = ventas.groupby("servicio")["ingreso_neto"].sum().reset_index()
cost_serv = costos.groupby("servicio")["costo_total"].sum().reset_index()

df_serv = pd.merge(rent_serv, cost_serv, on="servicio")
df_serv["utilidad"] = df_serv["ingreso_neto"] - df_serv["costo_total"]

st.plotly_chart(
    px.bar(df_serv, x="servicio", y="utilidad",
           color_discrete_sequence=[COLOR_AZUL]),
    use_container_width=True
)

# Trimestres
ventas["trimestre"] = ((ventas["mes"] - 1) // 3) + 1
ventas_trim = ventas.groupby("trimestre")["ingreso_neto"].sum().reset_index()

st.plotly_chart(
    px.bar(ventas_trim, x="trimestre", y="ingreso_neto",
           color_discrete_sequence=[COLOR_GRIS]),
    use_container_width=True
)

# =========================================================
# 📊 VISTA 3
# =========================================================
st.subheader("📊 Proyección")

# Scatter
st.plotly_chart(
    px.scatter(roic, x="monto_y", y="roic",
               color_discrete_sequence=[COLOR_VERDE]),
    use_container_width=True
)

# Simulación
v_ventas = st.slider("Variación ventas %", -50, 50, 0)
v_costos = st.slider("Variación costos %", -50, 50, 0)

df_sim = df.copy()
df_sim["ventas_sim"] = df_sim["ingreso_neto"] * (1 + v_ventas / 100)
df_sim["costos_sim"] = df_sim["costo_total"] * (1 + v_costos / 100)
df_sim["utilidad_sim"] = df_sim["ventas_sim"] - df_sim["costos_sim"]

st.metric("Utilidad simulada", f"${df_sim['utilidad_sim'].sum():,.0f}")

# Proyección
tendencia = df["ingreso_neto"].pct_change().mean()
proy = df["ingreso_neto"].iloc[-1] * (1 + tendencia)

st.metric("Ingreso proyectado", f"${proy:,.0f}")

# =========================================================
# 🧠 CONCLUSIONES
# =========================================================
st.subheader("Conclusión")

st.write("""
La empresa muestra alta rentabilidad operativa. Sin embargo,
el ROIC bajo indica posibles problemas en la eficiencia del capital.
""")

# =========================================================
# 📋 TABLA
# =========================================================
st.dataframe(df)
