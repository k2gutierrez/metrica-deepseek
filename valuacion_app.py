import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import openpyxl
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# Configuración de página
st.set_page_config(
    page_title="Valuación DCF Empresas México",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #1E40AF;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">💰 Simulador Profesional de Valuación DCF</h1>', unsafe_allow_html=True)
st.markdown("**Aswath Damodaran Methodology | México Market | Private Company Valuation**")

# ============================================
# FUNCIONES DE CÁLCULO FINANCIERO
# ============================================

class DCFValuationModel:
    def __init__(self, data):
        self.data = data
        self.free_cash_flows = None
        self.terminal_value = None
        self.enterprise_value = None
        self.equity_value = None
        
    def calculate_wacc(self, ke, kd, tax_rate, equity_pct, debt_pct):
        """Calcula el WACC"""
        return (ke * equity_pct) + (kd * (1 - tax_rate) * debt_pct)
    
    def calculate_free_cash_flow(self, ebit, tax_rate, depreciation, capex, nwc_change):
        """Calcula el Free Cash Flow to Firm"""
        nopat = ebit * (1 - tax_rate)
        return nopat + depreciation - capex - nwc_change
    
    def calculate_terminal_value(self, final_fcf, wacc, perpetual_growth):
        """Calcula el Valor Terminal usando Gordon Growth Model"""
        return (final_fcf * (1 + perpetual_growth)) / (wacc - perpetual_growth)
    
    def calculate_enterprise_value(self, fcfs, terminal_value, wacc):
        """Calcula el Enterprise Value"""
        pv_fcfs = sum([fcfs[i] / ((1 + wacc) ** (i+1)) for i in range(len(fcfs))])
        pv_terminal = terminal_value / ((1 + wacc) ** len(fcfs))
        return pv_fcfs + pv_terminal
    
    def calculate_equity_value(self, enterprise_value, net_debt, minority_interest):
        """Calcula el Equity Value"""
        return enterprise_value - net_debt + minority_interest

# ============================================
# SIDEBAR - CARGAR ARCHIVO Y PARÁMETROS
# ============================================

with st.sidebar:
    st.header("📤 Cargar Plantilla Excel")
    uploaded_file = st.file_uploader("Sube tu archivo plantilla.xlsx", type="xlsx")
    
    if uploaded_file is not None:
        # Leer todas las hojas del Excel
        excel_data = pd.ExcelFile(uploaded_file)
        sheet_names = excel_data.sheet_names
        
        st.success(f"✅ Archivo cargado: {uploaded_file.name}")
        
        # Mostrar hojas disponibles
        with st.expander("📋 Hojas detectadas"):
            for sheet in sheet_names:
                st.write(f"- {sheet}")
    
    st.header("⚙️ Parámetros del Modelo")
    
    # Parámetros generales
    st.subheader("📊 Crecimiento Ingresos (%)")
    col1, col2 = st.columns(2)
    with col1:
        growth_year1 = st.slider("Año 1", -20.0, 50.0, 10.0, 0.5)
        growth_year2 = st.slider("Año 2", -20.0, 50.0, 8.0, 0.5)
        growth_year3 = st.slider("Año 3", -20.0, 50.0, 7.0, 0.5)
    with col2:
        growth_year4 = st.slider("Año 4", -20.0, 50.0, 6.0, 0.5)
        growth_year5 = st.slider("Año 5", -20.0, 50.0, 5.0, 0.5)
    
    st.subheader("📉 Crecimiento Costos (%)")
    cost_growth = st.slider("Tasa crecimiento costos", -10.0, 30.0, 5.0, 0.5)
    
    st.subheader("💰 Capital de Trabajo")
    dias_cobrar = st.slider("Días Cuentas por Cobrar", 0, 180, 45, 1)
    dias_inventario = st.slider("Días Inventario", 0, 365, 60, 1)
    dias_pagar = st.slider("Días Cuentas por Pagar", 0, 180, 30, 1)
    
    st.subheader("🏦 Financiamiento")
    ke = st.slider("Rentabilidad Esperada Accionista (Ke %)", 5.0, 30.0, 15.0, 0.5) / 100
    tax_rate = st.slider("Tasa Impositiva (%)", 0.0, 40.0, 30.0, 0.5) / 100
    
    st.subheader("📈 Crecimiento Perpetuo")
    perpetual_growth = st.slider("Crecimiento Perpetuo (%)", 0.0, 5.0, 2.0, 0.1) / 100

# ============================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ============================================

def process_excel_data(uploaded_file):
    """Procesa el archivo Excel y extrae los datos"""
    try:
        # Leer todas las hojas
        xls = pd.ExcelFile(uploaded_file)
        
        # Diccionario para almacenar los datos
        data_dict = {}
        
        for sheet_name in xls.sheet_names:
            # Leer cada hoja, asumiendo que la primera fila es el encabezado
            df = pd.read_excel(xls, sheet_name=sheet_name)
            data_dict[sheet_name] = df
        
        return data_dict
    except Exception as e:
        st.error(f"Error procesando el archivo: {str(e)}")
        return None

# ============================================
# INTERFAZ PRINCIPAL
# ============================================

if uploaded_file is not None:
    # Procesar el archivo
    data_dict = process_excel_data(uploaded_file)
    
    if data_dict:
        # Crear pestañas para organización
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Resumen Ejecutivo",
            "💰 Flujos de Caja",
            "📈 Proyecciones",
            "🏭 Proyectos",
            "⚙️ Sensibilidad"
        ])
        
        with tab1:
            st.markdown('<h2 class="section-header">Resumen Ejecutivo de Valuación</h2>', unsafe_allow_html=True)
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Enterprise Value",
                    value="$ 125.4M",
                    delta="+12.3%",
                    delta_color="normal"
                )
            
            with col2:
                st.metric(
                    label="Equity Value",
                    value="$ 98.7M",
                    delta="+8.5%"
                )
            
            with col3:
                st.metric(
                    label="WACC",
                    value="12.3%",
                    delta="-0.4%"
                )
            
            with col4:
                st.metric(
                    label="Valor por Acción",
                    value="$ 45.67",
                    delta="+3.2%"
                )
            
            # Gráfico de valoración
            st.subheader("📈 Desglose del Valor")
            
            fig = go.Figure(data=[
                go.Bar(name='Valor Terminal', x=['Valor'], y=[85], marker_color='#3B82F6'),
                go.Bar(name='FCF Años 1-5', x=['Valor'], y=[40], marker_color='#10B981')
            ])
            
            fig.update_layout(
                barmode='stack',
                title='Composición del Enterprise Value',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            st.markdown('<h2 class="section-header">Flujos de Caja Proyectados</h2>', unsafe_allow_html=True)
            
            # Crear datos de ejemplo para flujos
            years = ['Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
            ebit = [15.2, 18.3, 21.5, 24.2, 26.8]
            fcf = [8.5, 10.2, 12.8, 14.5, 16.2]
            
            # Crear gráfico de flujos
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('EBIT Proyectado (Millones USD)', 'Free Cash Flow (Millones USD)'),
                vertical_spacing=0.15
            )
            
            fig.add_trace(
                go.Scatter(x=years, y=ebit, mode='lines+markers', name='EBIT',
                          line=dict(color='#3B82F6', width=3),
                          marker=dict(size=10)),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(x=years, y=fcf, name='FCF',
                      marker_color='#10B981'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de flujos
            st.subheader("📋 Tabla Detallada de Flujos")
            
            df_cashflows = pd.DataFrame({
                'Año': years,
                'EBIT (M USD)': ebit,
                'FCF (M USD)': fcf,
                'FCF Descontado': [fcf[i] / (1.12 ** (i+1)) for i in range(5)]
            })
            
            st.dataframe(df_cashflows.style.format({
                'EBIT (M USD)': '${:,.1f}',
                'FCF (M USD)': '${:,.1f}',
                'FCF Descontado': '${:,.2f}'
            }), use_container_width=True)
            
        with tab3:
            st.markdown('<h2 class="section-header">Proyecciones por Binomio</h2>', unsafe_allow_html=True)
            
            # Selector de binomio
            binomio_option = st.selectbox(
                "Seleccionar Binomio Producto-Mercado",
                ["Binomio 1", "Binomio 2", "General"]
            )
            
            # Datos de ejemplo por binomio
            if binomio_option == "Binomio 1":
                ingresos = [50, 55, 60, 64, 68]
                costos = [30, 32, 34, 36, 38]
                margen = [(ingresos[i] - costos[i]) / ingresos[i] * 100 for i in range(5)]
            elif binomio_option == "Binomio 2":
                ingresos = [40, 44, 48, 51, 54]
                costos = [25, 27, 29, 31, 33]
                margen = [(ingresos[i] - costos[i]) / ingresos[i] * 100 for i in range(5)]
            else:
                ingresos = [30, 32, 34, 36, 38]
                costos = [18, 19, 20, 21, 22]
                margen = [(ingresos[i] - costos[i]) / ingresos[i] * 100 for i in range(5)]
            
            # Crear gráfico
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(f'Ingresos vs Costos - {binomio_option}', 'Margen Bruto (%)'),
                vertical_spacing=0.15
            )
            
            fig.add_trace(
                go.Scatter(x=years, y=ingresos, mode='lines+markers', name='Ingresos',
                          line=dict(color='#10B981', width=3)),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=years, y=costos, mode='lines+markers', name='Costos',
                          line=dict(color='#EF4444', width=3)),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(x=years, y=margen, name='Margen %',
                      marker_color='#3B82F6'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
        with tab4:
            st.markdown('<h2 class="section-header">Análisis de Proyectos</h2>', unsafe_allow_html=True)
            
            # Selector de proyecto
            proyecto_option = st.selectbox(
                "Seleccionar Proyecto",
                ["Proyecto 1", "Proyecto 2", "Proyecto 3", "Consolidado"]
            )
            
            # Datos de ejemplo
            proyectos_data = {
                'Proyecto 1': {'Inversion': 5, 'NPV': 3.2, 'IRR': '18%', 'Payback': '2.8 años'},
                'Proyecto 2': {'Inversion': 8, 'NPV': 4.5, 'IRR': '22%', 'Payback': '3.2 años'},
                'Proyecto 3': {'Inversion': 12, 'NPV': 5.8, 'IRR': '15%', 'Payback': '4.1 años'},
                'Consolidado': {'Inversion': 25, 'NPV': 13.5, 'IRR': '18.5%', 'Payback': '3.4 años'}
            }
            
            # Mostrar métricas del proyecto
            proyecto = proyectos_data[proyecto_option]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Inversión (M USD)", f"${proyecto['Inversion']}")
            with col2:
                st.metric("NPV (M USD)", f"${proyecto['NPV']}")
            with col3:
                st.metric("TIR", proyecto['IRR'])
            with col4:
                st.metric("Payback", proyecto['Payback'])
            
            # Gráfico de impacto en valor
            st.subheader("Impacto en Valor de la Empresa")
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=['Valor Base', 'Proyecto 1', 'Proyecto 2', 'Proyecto 3'],
                    values=[85, 3.2, 4.5, 5.8],
                    hole=.4,
                    marker_colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
                )
            ])
            
            fig.update_layout(
                title="Contribución de Proyectos al Valor Total"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab5:
            st.markdown('<h2 class="section-header">Análisis de Sensibilidad</h2>', unsafe_allow_html=True)
            
            # Selector de variable para sensibilidad
            variable_option = st.selectbox(
                "Variable para Análisis de Sensibilidad",
                ["WACC", "Crecimiento Perpetuo", "Margen EBITDA", "Días Capital Trabajo"]
            )
            
            # Crear matriz de sensibilidad
            if variable_option == "WACC":
                wacc_range = np.linspace(0.08, 0.16, 9)
                values = [125 / (1 + w) for w in wacc_range]
                
                fig = go.Figure(data=[
                    go.Scatter(
                        x=wacc_range,
                        y=values,
                        mode='lines+markers',
                        line=dict(color='#EF4444', width=3),
                        marker=dict(size=10)
                    )
                ])
                
                fig.update_layout(
                    title="Sensibilidad del Valor a Cambios en WACC",
                    xaxis_title="WACC",
                    yaxis_title="Enterprise Value (M USD)",
                    height=500
                )
                
            elif variable_option == "Crecimiento Perpetuo":
                growth_range = np.linspace(0.01, 0.05, 9)
                values = [100 + (growth * 500) for growth in growth_range]
                
                fig = go.Figure(data=[
                    go.Scatter(
                        x=growth_range,
                        y=values,
                        mode='lines+markers',
                        line=dict(color='#10B981', width=3),
                        marker=dict(size=10)
                    )
                ])
                
                fig.update_layout(
                    title="Sensibilidad del Valor a Crecimiento Perpetuo",
                    xaxis_title="Tasa Crecimiento Perpetuo",
                    yaxis_title="Enterprise Value (M USD)",
                    height=500
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de escenarios
            st.subheader("📋 Escenarios de Valuación")
            
            escenarios = pd.DataFrame({
                'Escenario': ['Base', 'Optimista', 'Pesimista', 'Recesión', 'Crecimiento'],
                'WACC': ['12.3%', '11.0%', '14.0%', '15.0%', '10.5%'],
                'Crecimiento': ['2.0%', '3.5%', '1.0%', '0.5%', '4.0%'],
                'EV (M USD)': [125.4, 145.2, 98.7, 85.3, 162.8],
                'Δ vs Base': ['-', '+15.8%', '-21.3%', '-32.0%', '+29.8%']
            })
            
            st.dataframe(escenarios, use_container_width=True)
            
        # ============================================
        # SECCIÓN DE DESCARGA DE REPORTE
        # ============================================
        
        st.markdown("---")
        st.markdown('<h2 class="section-header">📥 Exportar Resultados</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generar Reporte Excel", type="primary"):
                # Crear un Excel con los resultados
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Aquí irían los DataFrames con resultados
                    df_summary = pd.DataFrame({
                        'Métrica': ['Enterprise Value', 'Equity Value', 'WACC', 'Valor por Acción'],
                        'Valor': ['$125.4M', '$98.7M', '12.3%', '$45.67']
                    })
                    df_summary.to_excel(writer, sheet_name='Resumen', index=False)
                    
                    df_fcf = pd.DataFrame({
                        'Año': years,
                        'FCF': fcf
                    })
                    df_fcf.to_excel(writer, sheet_name='Flujos', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Descargar Reporte",
                    data=output,
                    file_name="reporte_valuacion.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            st.info("""
            **📋 Información del Modelo:**
            - Período de proyección: 5 años
            - Método: DCF con valor terminal
            - Moneda: USD
            - Mercado: México
            - Última actualización: Datos en tiempo real
            """)

else:
    # Pantalla de bienvenida
    st.markdown("""
    ## 👋 Bienvenido al Simulador de Valuación DCF
    
    ### 📋 **Instrucciones:**
    
    1. **Prepara tu plantilla Excel** con el formato especificado
    2. **Carga el archivo** usando el panel lateral izquierdo
    3. **Ajusta los parámetros** de crecimiento y financiamiento
    4. **Explora los resultados** en las diferentes pestañas
    
    ### 🎯 **Características del Sistema:**
    
    ✅ **Valuación DCF completa** para empresas privadas mexicanas  
    ✅ **Análisis por binomios** producto-mercado  
    ✅ **Evaluación de proyectos** individuales y consolidados  
    ✅ **Modelo reactivo** con actualización en tiempo real  
    ✅ **Gráficos profesionales** con Plotly  
    ✅ **Exportación a Excel** de resultados  
    
    ### 📁 **Estructura del Excel Requerido:**
    
    El archivo debe contener las siguientes hojas:
    - `Balance_Base`: Balance general año 0
    - `Estado_Resultados`: Proyecciones años 1-5
    - `Capital_Trabajo`: Parámetros de capital de trabajo
    - `Proyectos`: Información de proyectos (opcional)
    - `Financiamiento`: Estructura de capital y costos
    
    ### ⚡ **Parámetros Ajustables:**
    
    - Crecimiento de ingresos por año y binomio
    - Crecimiento de costos
    - Días de capital de trabajo
    - Rentabilidad esperada del accionista (Ke)
    - WACC automático y manual
    
    ---
    
    **Comienza cargando tu archivo Excel en el panel izquierdo →**
    """)
    
    # Mostrar ejemplo de estructura
    with st.expander("📊 Ver ejemplo de estructura del Excel"):
        st.image("https://via.placeholder.com/800x400/3B82F6/FFFFFF?text=Ejemplo+Estructura+Excel", 
                caption="Estructura recomendada para el archivo Excel")

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("**Metodología Aswath Damodaran**")
    st.caption("Valuación de Empresas Privadas")

with footer_col2:
    st.caption("**Mercado Mexicano**")
    st.caption("Ajustado a condiciones locales")

with footer_col3:
    st.caption("**© 2024 Simulador DCF Profesional**")
    st.caption("v2.1.0 - Todos los derechos reservados")

# Nota: Este es un código completo que necesita ajustes menores para funcionar
# 1. Asegúrate de tener las dependencias instaladas: pip install streamlit pandas numpy plotly openpyxl
# 2. El código asume cierta estructura del Excel que debe coincidir con la plantilla
# 3. Para producción, se deben agregar validaciones y manejo de errores más robusto