# =========================================================
# 📊 DASHBOARD FINANCIERO - LOGÍSTICA ANDINA S.A.
# =========================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Ocultar el botón de Deploy y los elementos de la barra superior
st.markdown(
    """
    <style>
    /* Oculta los botones flotantes de la comunidad en Streamlit Cloud (esquina inferior derecha) */
    div[data-testid="stStatusWidget"],
    .stAppDeployButton,
    [data-testid="stDecoration"],
    #tabs-bui3-tab-0 + div {
        visibility: hidden !important;
        display: none !important;
    }

    /* Remueve el contenedor inferior por completo */
    footer, [data-testid="stFooter"] {
        visibility: hidden !important;
        display: none !important;
        height: 0px !important;
    }

    /* Oculta la barra superior gris/blanca */
    header, [data-testid="stHeader"] {
        visibility: hidden !important;
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Configuración de página profesional
st.set_page_config(page_title="Dashboard Ejecutivo Financiero", layout="wide", page_icon="📊")

# 🎨 COLORES INSTITUCIONALES / PROFESIONALES
COLOR_AZUL = "#1f4e79"
COLOR_VERDE = "#2ecc71"
COLOR_GRIS = "#7f8c8d"

st.title("📊 Dashboard Ejecutivo de Gestión Financiera")
st.markdown("### **Logística Andina S.A.** - Optimización de Gestión Operativa y Financiera")
st.markdown("---")

# =========================================================
# 📂 CARGA DE DATOS CON CACHÉ Y LIMPIEZA
# =========================================================
@st.cache_data
def cargar_y_limpiar_datos():
    # Leer hojas específicas de los archivos provistos
    ventas = pd.read_excel("Ventas.xlsx")
    costos = pd.read_excel("Costos.xlsx")
    balance = pd.read_excel("Balance.xlsx", sheet_name="Balance General")
    eerr = pd.read_excel("EERR.xlsx", sheet_name="Estado de Resultados")
    
    # Estandarizar columnas eliminando espacios fantasmas
    for df in [ventas, costos, balance, eerr]:
        df.columns = df.columns.str.strip()
        
    return ventas, costos, balance, eerr

try:
    v_raw, c_raw, b_raw, e_raw = cargar_y_limpiar_datos()
except Exception as ex:
    st.error(f"❌ Error crítico al cargar los archivos Excel obligatorios: {ex}")
    st.stop()

# Copias de trabajo
ventas = v_raw.copy()
costos = c_raw.copy()
balance = b_raw.copy()
eerr = e_raw.copy()

# =========================================================
# 🧹 NORMALIZACIÓN DE TIEMPO Y FORMATO
# =========================================================
# Fechas en Ventas y Costos
for df_temp in [ventas, costos]:
    if not np.issubdtype(df_temp["Fecha"].dtype, np.datetime64):
        df_temp["Fecha"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df_temp["Fecha"], unit="D")
    df_temp["mes_num"] = df_temp["Fecha"].dt.month

# Mapa de meses para Balance y EERR (Textual a Numérico)
mapa_meses = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
balance["mes_num"] = balance["Mes"].str.strip().map(mapa_meses)
eerr["mes_num"] = eerr["Mes"].str.strip().map(mapa_meses)

# Filtrar nulos si existen en los meses mapeados
balance = balance.dropna(subset=["mes_num"]).astype({"mes_num": int})
eerr = eerr.dropna(subset=["mes_num"]).astype({"mes_num": int})

# =========================================================
# 🎛️ FILTROS (SIDEBAR) - REQUERIMIENTO DE SEGMENTACIÓN
# =========================================================
st.sidebar.header("🕹️ Panel de Control y Filtros")

todos_meses = sorted(ventas["mes_num"].unique())
meses_sel = st.sidebar.multiselect("Filtrar por Mes", todos_meses, default=todos_meses)

regiones_unicas = ventas["Región"].unique()
region_sel = st.sidebar.multiselect("Filtrar por Región", regiones_unicas, default=regiones_unicas)

servicios_unicos = ventas["Tipo de servicio"].unique()
servicio_sel = st.sidebar.multiselect("Centro de Costo / Servicio", servicios_unicos, default=servicios_unicos)

# Aplicar filtros a transacciones operativas
ventas_f = ventas[(ventas["mes_num"].isin(meses_sel)) & (ventas["Región"].isin(region_sel)) & (ventas["Tipo de servicio"].isin(servicio_sel))]
costos_f = costos[(costos["mes_num"].isin(meses_sel)) & (costos["Región"].isin(region_sel)) & (costos["Tipo de servicio"].isin(servicio_sel))]

# Aplicar filtros temporales a EE.FF. generales
balance_f = balance[balance["mes_num"].isin(meses_sel)]
eerr_f = eerr[eerr["mes_num"].isin(meses_sel)]

# =========================================================
# 📊 CONSTRUCCIÓN DEL MODELO FINANCIERO CONSOLIDADO
# =========================================================
# 1. Ventas e Ingresos por mes
v_mensual = ventas_f.groupby("mes_num")["Ingreso neto (CLP)"].sum().reset_index()

# 2. Costos por mes
costos_f["costo_total"] = costos_f["Costo directo (CLP)"] + costos_f["Costo indirecto (CLP)"] + costos_f["Costo de transporte total (CLP)"]
c_mensual = costos_f.groupby("mes_num")["costo_total"].sum().reset_index()

# Pivotar EERR y Balance para extracción limpia de cuentas corporativas
eerr_pivot = eerr_f.pivot_table(index="mes_num", columns="Cuenta", values="Monto (CLP)", aggfunc="sum").fillna(0)
balance_pivot = balance_f.pivot_table(index="mes_num", columns="Cuenta", values="Monto (CLP)", aggfunc="sum").fillna(0)
balance_grupo_pivot = balance_f.pivot_table(index="mes_num", columns="Grupo", values="Monto (CLP)", aggfunc="sum").fillna(0)

# Asegurar columnas requeridas en los pivots en caso de filtros extremos
cuentas_eerr = ["Ventas Netas", "Descuentos y Devoluciones", "Costo de Ventas", "Gastos Totales", "Resultado Otros"]
for c in cuentas_eerr:
    if c not in eerr_pivot.columns: eerr_pivot[c] = 0

cuentas_bal = ["Clientes", "Inventarios", "Proveedores", "Total Activos Corrientes", "Total Activos No Corrientes", "Total Pasivos Corrientes", "Total Pasivos No Corrientes", "Total Patrimonio"]
for c in cuentas_bal:
    if c not in balance_pivot.columns: balance_pivot[c] = 0

# Construcción de métricas avanzadas por mes
df_mes = pd.DataFrame({"mes_num": todos_meses}).set_index("mes_num")

# EBITDA corporativo = Ventas Netas + Devoluciones + Costo de Ventas + Gastos Totales (vienen con sus signos correspondientes)
df_mes["Ventas_Netas"] = eerr_pivot["Ventas Netas"]
df_mes["EBITDA"] = eerr_pivot["Ventas Netas"] + eerr_pivot["Descuentos y Devoluciones"] + eerr_pivot["Costo de Ventas"] + eerr_pivot["Gastos Totales"]
df_mes["EBITDA_Margin"] = (df_mes["EBITDA"] / df_mes["Ventas_Netas"] * 100).fillna(0)

# Rotación de Activos e Inversión
activos_totales = balance_pivot["Total Activos Corrientes"] + balance_pivot["Total Activos No Corrientes"]
df_mes["Rotacion_Activos"] = (df_mes["Ventas_Netas"] / activos_totales).fillna(0)

# CCE (Ciclo de Conversión de Efectivo) en días mensuales (Base 30 días)
df_mes["Dias_CxC"] = (balance_pivot["Clientes"] / df_mes["Ventas_Netas"] * 30).fillna(0)
df_mes["Dias_Inventario"] = (balance_pivot["Inventarios"] / np.abs(eerr_pivot["Costo de Ventas"]) * 30).fillna(0)
df_mes["Dias_CxP"] = (balance_pivot["Proveedores"] / np.abs(eerr_pivot["Costo de Ventas"]) * 30).fillna(0)
df_mes["CCE"] = df_mes["Dias_CxC"] + df_mes["Dias_Inventario"] - df_mes["Dias_CxP"]

# Apalancamiento Financiero
pasivo_total = balance_pivot["Total Pasivos Corrientes"] + balance_pivot["Total Pasivos No Corrientes"]
df_mes["Apalancamiento"] = (pasivo_total / balance_pivot["Total Patrimonio"]).fillna(0)

# ROIC (Utilidad Operativa Neta después de Impuestos / Capital Invertido)
# NOPAT aproximado: EBITDA + Resultado Otros - Impuestos (con tasa 27%)
df_mes["NOPAT"] = (df_mes["EBITDA"] + eerr_pivot["Resultado Otros"]) * (1 - 0.27)
df_mes["ROIC"] = (df_mes["NOPAT"] / balance_pivot["Total Patrimonio"] * 100).fillna(0)

# Variación de ventas mensual (%)
df_mes["Var_Ventas_Pct"] = df_mes["Ventas_Netas"].pct_change() * 100

df_mes = df_mes.reset_index()

# =========================================================
# 🧭 VISTAS INTERACTIVAS (TABS DEL ENUNCIADO)
# =========================================================
tab1, tab2, tab3 = st.tabs(["📋 Vista 1: Resumen Ejecutivo", "🔍 Vista 2: Análisis Detallado", "📈 Vista 3: Proyección y Estrategia"])

# ---------------------------------------------------------
# PESTAÑA 1: RESUMEN EJECUTIVO
# ---------------------------------------------------------
with tab1:
    st.subheader("Indicadores Financieros Clave (KPIs Globales)")
    
    # Cálculos agregados consistentes con finanzas empresariales
    total_v = df_mes["Ventas_Netas"].sum()
    total_ebitda = df_mes["EBITDA"].sum()
    margen_ebitda_global = (total_ebitda / total_v * 100) if total_v > 0 else 0
    rot_activos_global = df_mes["Rotacion_Activos"].mean()
    apalanc_global = df_mes["Apalancamiento"].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Jerarquía visual superior con formato dinámico implícito
    col1.metric("Ventas Netas Totales", f"${total_v:,.0f} CLP")
    col2.metric("EBITDA Consolidado", f"${total_ebitda:,.0f} CLP")
    col3.metric("Margen EBITDA Real", f"{margen_ebitda_global:.2f}%")
    col4.metric("Apalancamiento Promedio", f"{apalanc_global:.2f}x")
    
    st.markdown("---")
    st.subheader("Evolución Mensual de Ventas, EBITDA y Margen Operativo")
    
    # Gráfico de tendencia de Ingresos y EBITDA
    fig_line = px.line(df_mes, x="mes_num", y=["Ventas_Netas", "EBITDA"], 
                       labels={"value": "Monto en CLP", "mes_num": "Mes de Operación"},
                       title="Evolución Mensual: Ingresos vs. EBITDA",
                       color_discrete_sequence=[COLOR_AZUL, COLOR_VERDE])
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Métricas de Estructura de Capital y Productividad
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.write("**Eficiencia de Activos (Rotación)**")
        st.plotly_chart(px.bar(df_mes, x="mes_num", y="Rotacion_Activos", color_discrete_sequence=[COLOR_AZUL]), use_container_width=True)
    with col_g2:
        st.write("**Nivel de Apalancamiento Financiero**")
        st.plotly_chart(px.line(df_mes, x="mes_num", y="Apalancamiento", color_discrete_sequence=[COLOR_GRIS]), use_container_width=True)

# ---------------------------------------------------------
# PESTAÑA 2: ANÁLISIS DETALLADO
# ---------------------------------------------------------
with tab2:
    st.subheader("Análisis de Rentabilidad por Centro de Costos y Eficiencia de Capital")
    
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.write("**Rentabilidad Operativa por Tipo de Servicio / Centro de Costos**")
        # Unificación de rentabilidad por segmento operacional directo
        rent_serv = ventas_f.groupby("Tipo de servicio")["Ingreso neto (CLP)"].sum().reset_index()
        cost_serv = costos_f.groupby("Tipo de servicio")["costo_total"].sum().reset_index()
        df_serv = pd.merge(rent_serv, cost_serv, on="Tipo de servicio")
        df_serv["Utilidad Operativa"] = df_serv["Ingreso neto (CLP)"] - df_serv["costo_total"]
        
        fig_serv = px.bar(df_serv, x="Tipo de servicio", y="Utilidad Operativa",
                          color="Tipo de servicio", color_discrete_sequence=[COLOR_AZUL, COLOR_VERDE, COLOR_GRIS])
        st.plotly_chart(fig_serv, use_container_width=True)
        
    with col_det2:
        st.write("**Desglose del Ciclo de Conversión de Efectivo (CCE) Promedio**")
        cce_mean = df_mes[["Dias_CxC", "Dias_Inventario", "Dias_CxP"]].mean().reset_index()
        cce_mean.columns = ["Componente", "Días Promedio"]
        
        fig_cce = px.bar(cce_mean, x="Componente", y="Días Promedio", 
                         title=f"CCE Neto Promedio: {df_mes['CCE'].mean():.1f} Días",
                         color_discrete_sequence=[COLOR_VERDE])
        st.plotly_chart(fig_cce, use_container_width=True)

    st.markdown("---")
    st.subheader("Análisis Trimestral Combinado de Variaciones")
    
    # Agrupación trimestral para variaciones
    df_mes["trimestre"] = ((df_mes["mes_num"] - 1) // 3) + 1
    df_trim = df_mes.groupby("trimestre")[["Ventas_Netas", "EBITDA"]].sum().reset_index()
    df_trim["Var_Ventas_Trim"] = df_trim["Ventas_Netas"].pct_change() * 100
    df_trim["Var_EBITDA_Trim"] = df_trim["EBITDA"].pct_change() * 100
    
    fig_trim = px.bar(df_trim, x="trimestre", y=["Var_Ventas_Trim", "Var_EBITDA_Trim"],
                      barmode="group", title="Variación Trimestral de Ventas y EBITDA (%)",
                      labels={"value": "Variación (%)", "trimestre": "Trimestre (Q)"},
                      color_discrete_sequence=[COLOR_AZUL, COLOR_GRIS])
    st.plotly_chart(fig_trim, use_container_width=True)

# ---------------------------------------------------------
# PESTAÑA 3: PROYECCIÓN Y RECOMENDACIONES STRATEGIC
# ---------------------------------------------------------
with tab3:
    st.subheader("Matriz Estratégica: ROIC vs. Apalancamiento")
    
    # Scatter plot requerido explícitamente por el requerimiento de la Vista 3
    fig_scatter = px.scatter(df_mes, x="Apalancamiento", y="ROIC", text="mes_num",
                             size="Ventas_Netas", title="Relación ROIC vs. Apalancamiento Financiero",
                             labels={"Apalancamiento": "Apalancamiento (Pasivo / Patrimonio)", "ROIC": "ROIC (%)"},
                             color_discrete_sequence=[COLOR_VERDE])
    fig_scatter.update_traces(textposition='top center')
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Tabla Resumen de Indicadores Promedio por Trimestre")
    
    # Tabla formal requerida
    tabla_trim = df_mes.groupby("trimestre")[["EBITDA_Margin", "Rotacion_Activos", "CCE", "Apalancamiento", "ROIC"]].mean()
    tabla_trim.columns = ["Margen EBITDA (%)", "Rotación de Activos (x)", "CCE (Días)", "Apalancamiento (x)", "ROIC (%)"]
    st.dataframe(tabla_trim.style.format("{:.2f}"))
    
    st.markdown("---")
    st.subheader("💡 Conclusiones Estratégicas (Informe Ejecutivo)")
    
    st.success("""
    **Principales Hallazgos para la Toma de Decisiones:**
    * **Presión Logística e Inflacionaria:** El centro de costos **Refrigerado** presenta la mayor sensibilidad en el margen debido al incremento directo en costos de energía y distribución, mientras que el transporte **Interregional** sostiene los mayores volúmenes agregados.
    * **Ciclo de Conversión de Efectivo (CCE):** Se evidencia un desfase entre los días de cobro a clientes y los días de pago a proveedores. Optimizar las políticas de crédito comercial liberará flujo de caja operativo de forma inmediata.
    * **Eficiencia del Capital (ROIC):** La dispersión observada en la matriz muestra que un apalancamiento controlado incrementa la rentabilidad sobre el capital invertido (ROIC) siempre y cuando la rotación de activos se mantenga por encima del umbral de equilibrio operativo.
    """)
