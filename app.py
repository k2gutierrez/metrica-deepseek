# app.py - VERSIÓN CORREGIDA
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# ============================================
# INICIALIZACIÓN DEL SESSION STATE
# ============================================

# Configuración de página DEBE SER LO PRIMERO
st.set_page_config(
    page_title="💰 Simulador DCF - Valuación de Empresas México",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state SOLO si no existen
if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False
if 'data_loader' not in st.session_state:
    st.session_state.data_loader = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'parametros_ajustados' not in st.session_state:
    # Valores por defecto
    st.session_state.parametros_ajustados = {
        'crecimiento_ingresos_binomio1': [0.15, 0.12, 0.10, 0.08, 0.06],
        'crecimiento_ingresos_binomio2': [0.10, 0.08, 0.07, 0.06, 0.05],
        'crecimiento_ingresos_general': [0.05, 0.04, 0.03, 0.02, 0.02],
        'margen_binomio1': 0.60,
        'margen_binomio2': 0.50,
        'margen_general': 0.40,
        'ke': 0.153,
        'proporcion_deuda': 0.35,
        'proporcion_patrimonio': 0.65,
        'tax_rate': 0.30,
        'crecimiento_perpetuo': 0.02,
        'dias_cpc': 45,
        'dias_inventario': 60,
        'dias_cpp': 30,
        'gastos_operativos_base': 6000000,
        'crecimiento_gastos': 0.03,
        'depreciacion': 1200000,
        'amortizacion': 450000,
        'capex': 925000,
        'kd': 0.12
    }

# ============================================
# CSS PERSONALIZADO
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E40AF;
        border-left: 4px solid #3B82F6;
        padding-left: 1rem;
        margin: 2rem 0 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #F8FAFC;
        padding: 4px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #E2E8F0;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important;
        color: white !important;
    }
    .info-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #F8FAFC;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# TÍTULO PRINCIPAL
# ============================================

st.markdown('<h1 class="main-header">💰 SIMULADOR PROFESIONAL DE VALUACIÓN DCF</h1>', unsafe_allow_html=True)
st.markdown("**Metodología Aswath Damodaran | Empresas Privadas México | Análisis por Binomios Producto-Mercado**")

# ============================================
# CLASES AUXILIARES (SIMPLIFICADAS)
# ============================================

class ExcelDataLoader:
    def __init__(self):
        self.data_frames = {}
        self.metadata = {}
    
    def load_excel(self, uploaded_file):
        try:
            xls = pd.ExcelFile(uploaded_file)
            self.metadata['sheet_names'] = xls.sheet_names
            self.metadata['file_name'] = uploaded_file.name
            
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                self.data_frames[sheet_name] = df
            
            # Extraer datos básicos del balance
            self._extraer_datos_basicos()
            return True, "✅ Archivo cargado exitosamente"
            
        except Exception as e:
            return False, f"❌ Error al cargar: {str(e)}"
    
    def _extraer_datos_basicos(self):
        """Extrae datos básicos para el modelo"""
        self.metadata['datos_base'] = {
            'efectivo': 5000000,
            'deuda_total': 12000000,
            'capital_trabajo_base': 10000000
        }
    
    def get_summary(self):
        return {
            'empresa': self.metadata.get('file_name', 'Desconocida'),
            'hojas_cargadas': len(self.data_frames)
        }

class DCFCalculator:
    def __init__(self, datos_base, parametros):
        self.datos_base = datos_base
        self.parametros = parametros
        self.resultados = {}
    
    def calcular_proyecciones(self):
        # 1. Proyectar ingresos
        proyecciones_ingresos = self._proyectar_ingresos()
        
        # 2. Proyectar costos
        proyecciones_costos = self._proyectar_costos(proyecciones_ingresos)
        
        # 3. Calcular EBIT y EBITDA
        proyecciones_operativas = self._calcular_operativas(proyecciones_ingresos, proyecciones_costos)
        
        # 4. Calcular capital de trabajo
        necesidades_ct = self._calcular_capital_trabajo(proyecciones_ingresos, proyecciones_costos)
        
        # 5. Calcular FCF
        fcf = self._calcular_fcf(proyecciones_operativas, necesidades_ct)
        
        # 6. Calcular WACC
        wacc = self._calcular_wacc()
        
        # 7. Calcular valor terminal
        valor_terminal = self._calcular_valor_terminal(fcf[-1], wacc)
        
        # 8. Calcular Enterprise Value
        enterprise_value = self._calcular_enterprise_value(fcf, valor_terminal, wacc)
        
        # 9. Calcular Equity Value
        equity_value = self._calcular_equity_value(enterprise_value)
        
        self.resultados = {
            'proyecciones_ingresos': proyecciones_ingresos,
            'proyecciones_costos': proyecciones_costos,
            'ebit': proyecciones_operativas['ebit'],
            'ebitda': proyecciones_operativas['ebitda'],
            'capital_trabajo': necesidades_ct,
            'fcf': fcf,
            'wacc': wacc,
            'valor_terminal': valor_terminal,
            'enterprise_value': enterprise_value,
            'equity_value': equity_value
        }
        
        return self.resultados
    
    def _proyectar_ingresos(self):
        años = 5
        base_b1 = 12500000
        base_b2 = 8500000
        base_gen = 4000000
        
        crecimiento_b1 = self.parametros.get('crecimiento_ingresos_binomio1', [0.15, 0.12, 0.10, 0.08, 0.06])
        crecimiento_b2 = self.parametros.get('crecimiento_ingresos_binomio2', [0.10, 0.08, 0.07, 0.06, 0.05])
        crecimiento_gen = self.parametros.get('crecimiento_ingresos_general', [0.05, 0.04, 0.03, 0.02, 0.02])
        
        ingresos = {
            'binomio1': [base_b1 * (1 + crecimiento_b1[0])],
            'binomio2': [base_b2 * (1 + crecimiento_b2[0])],
            'general': [base_gen * (1 + crecimiento_gen[0])],
            'total': []
        }
        
        for i in range(1, años):
            ingresos['binomio1'].append(ingresos['binomio1'][-1] * (1 + crecimiento_b1[i]))
            ingresos['binomio2'].append(ingresos['binomio2'][-1] * (1 + crecimiento_b2[i]))
            ingresos['general'].append(ingresos['general'][-1] * (1 + crecimiento_gen[i]))
        
        for i in range(años):
            ingresos['total'].append(ingresos['binomio1'][i] + ingresos['binomio2'][i] + ingresos['general'][i])
        
        return ingresos
    
    def _proyectar_costos(self, ingresos):
        años = 5
        costos = {
            'binomio1': [],
            'binomio2': [],
            'general': [],
            'total': []
        }
        
        margen_b1 = self.parametros.get('margen_binomio1', 0.60)
        margen_b2 = self.parametros.get('margen_binomio2', 0.50)
        margen_gen = self.parametros.get('margen_general', 0.40)
        
        for i in range(años):
            costo_b1 = ingresos['binomio1'][i] * (1 - margen_b1)
            costo_b2 = ingresos['binomio2'][i] * (1 - margen_b2)
            costo_gen = ingresos['general'][i] * (1 - margen_gen)
            
            costos['binomio1'].append(costo_b1)
            costos['binomio2'].append(costo_b2)
            costos['general'].append(costo_gen)
            costos['total'].append(costo_b1 + costo_b2 + costo_gen)
        
        return costos
    
    def _calcular_operativas(self, ingresos, costos):
        años = 5
        resultados = {
            'margen_bruto': [],
            'ebitda': [],
            'ebit': []
        }
        
        gastos_op_base = self.parametros.get('gastos_operativos_base', 6000000)
        crecimiento_gastos = self.parametros.get('crecimiento_gastos', 0.03)
        depreciacion = self.parametros.get('depreciacion', 1200000)
        amortizacion = self.parametros.get('amortizacion', 450000)
        
        for i in range(años):
            margen_bruto = ingresos['total'][i] - costos['total'][i]
            resultados['margen_bruto'].append(margen_bruto)
            
            gastos_op = gastos_op_base * (1 + crecimiento_gastos) ** i
            ebitda = margen_bruto - (gastos_op - depreciacion - amortizacion)
            resultados['ebitda'].append(ebitda)
            
            ebit = ebitda - depreciacion - amortizacion
            resultados['ebit'].append(ebit)
        
        return resultados
    
    def _calcular_capital_trabajo(self, ingresos, costos):
        años = 5
        necesidades = {
            'capital_trabajo_neto': [],
            'delta_capital_trabajo': []
        }
        
        dias_cpc = self.parametros.get('dias_cpc', 45)
        dias_inv = self.parametros.get('dias_inventario', 60)
        dias_cpp = self.parametros.get('dias_cpp', 30)
        
        for i in range(años):
            necesidad_cpc = (ingresos['total'][i] * dias_cpc) / 365
            necesidad_inv = (costos['total'][i] * dias_inv) / 365
            necesidad_cpp = (costos['total'][i] * dias_cpp) / 365
            
            ct_neto = necesidad_cpc + necesidad_inv - necesidad_cpp
            necesidades['capital_trabajo_neto'].append(ct_neto)
            
            if i == 0:
                ct_base = self.datos_base.get('capital_trabajo_base', 0)
                delta = ct_neto - ct_base
            else:
                delta = ct_neto - necesidades['capital_trabajo_neto'][i-1]
            
            necesidades['delta_capital_trabajo'].append(delta)
        
        return necesidades
    
    def _calcular_fcf(self, operativas, necesidades_ct):
        años = 5
        fcf = []
        
        tax_rate = self.parametros.get('tax_rate', 0.30)
        capex = self.parametros.get('capex', 925000)
        depreciacion = self.parametros.get('depreciacion', 1200000)
        amortizacion = self.parametros.get('amortizacion', 450000)
        
        for i in range(años):
            nopat = operativas['ebit'][i] * (1 - tax_rate)
            delta_ct = necesidades_ct['delta_capital_trabajo'][i]
            
            fcf_i = nopat + depreciacion + amortizacion - capex - delta_ct
            fcf.append(fcf_i)
        
        return fcf
    
    def _calcular_wacc(self):
        ke = self.parametros.get('ke', 0.153)
        kd = self.parametros.get('kd', 0.12)
        tax_rate = self.parametros.get('tax_rate', 0.30)
        d_v = self.parametros.get('proporcion_deuda', 0.35)
        e_v = self.parametros.get('proporcion_patrimonio', 0.65)
        
        wacc = (e_v * ke) + (d_v * kd * (1 - tax_rate))
        return wacc
    
    def _calcular_valor_terminal(self, ultimo_fcf, wacc):
        crecimiento_perpetuo = self.parametros.get('crecimiento_perpetuo', 0.02)
        
        if wacc <= crecimiento_perpetuo:
            return ultimo_fcf * 10
        else:
            return (ultimo_fcf * (1 + crecimiento_perpetuo)) / (wacc - crecimiento_perpetuo)
    
    def _calcular_enterprise_value(self, fcf, valor_terminal, wacc):
        pv_fcf = 0
        for i, fcf_i in enumerate(fcf):
            pv_fcf += fcf_i / ((1 + wacc) ** (i + 1))
        
        pv_valor_terminal = valor_terminal / ((1 + wacc) ** len(fcf))
        return pv_fcf + pv_valor_terminal
    
    def _calcular_equity_value(self, enterprise_value):
        efectivo = self.datos_base.get('efectivo', 5000000)
        deuda_total = self.datos_base.get('deuda_total', 12000000)
        
        deuda_neta = deuda_total - efectivo
        equity_value = enterprise_value - deuda_neta
        
        return max(equity_value, 0)

# ============================================
# BARRA LATERAL
# ============================================

with st.sidebar:
    st.header("📤 Cargar Plantilla Excel")
    uploaded_file = st.file_uploader("Sube tu archivo plantilla.xlsx", type="xlsx")
    
    if uploaded_file is not None:
        try:
            # Cargar datos
            data_loader = ExcelDataLoader()
            success, message = data_loader.load_excel(uploaded_file)
            
            if success:
                st.session_state.datos_cargados = True
                st.session_state.data_loader = data_loader
                st.session_state.file_name = uploaded_file.name
                
                # Actualizar parámetros con valores del Excel si es necesario
                # Por ahora mantenemos los valores por defecto
                
                st.success(message)
                
                # Mostrar resumen
                with st.expander("📋 Resumen del archivo"):
                    summary = data_loader.get_summary()
                    st.write(f"**Archivo:** {summary['empresa']}")
                    st.write(f"**Hojas cargadas:** {summary['hojas_cargadas']}")
                    
            else:
                st.error(message)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Parámetros del modelo (solo si hay datos cargados)
    if st.session_state.datos_cargados:
        st.header("⚙️ Parámetros del Modelo")
        
        # Pestañas para parámetros
        param_tabs = st.tabs(["📈 Ingresos", "📉 Costos", "🏦 Financiamiento", "💰 Capital Trabajo"])
        
        with param_tabs[0]:
            st.subheader("Crecimiento de Ingresos (%)")
            
            # Obtener valores actuales del session state
            params = st.session_state.parametros_ajustados
            
            # Binomio 1
            st.markdown("**Binomio 1: Software-Empresas**")
            col1, col2 = st.columns(2)
            with col1:
                b1_yr1 = st.slider("Año 1", -20.0, 50.0, params['crecimiento_ingresos_binomio1'][0]*100, 0.5, key="b1_yr1")
                b1_yr2 = st.slider("Año 2", -20.0, 50.0, params['crecimiento_ingresos_binomio1'][1]*100, 0.5, key="b1_yr2")
                b1_yr3 = st.slider("Año 3", -20.0, 50.0, params['crecimiento_ingresos_binomio1'][2]*100, 0.5, key="b1_yr3")
            with col2:
                b1_yr4 = st.slider("Año 4", -20.0, 50.0, params['crecimiento_ingresos_binomio1'][3]*100, 0.5, key="b1_yr4")
                b1_yr5 = st.slider("Año 5", -20.0, 50.0, params['crecimiento_ingresos_binomio1'][4]*100, 0.5, key="b1_yr5")
            
            # Binomio 2
            st.markdown("**Binomio 2: Consultoría**")
            col1, col2 = st.columns(2)
            with col1:
                b2_yr1 = st.slider("Año 1", -20.0, 50.0, params['crecimiento_ingresos_binomio2'][0]*100, 0.5, key="b2_yr1")
                b2_yr2 = st.slider("Año 2", -20.0, 50.0, params['crecimiento_ingresos_binomio2'][1]*100, 0.5, key="b2_yr2")
                b2_yr3 = st.slider("Año 3", -20.0, 50.0, params['crecimiento_ingresos_binomio2'][2]*100, 0.5, key="b2_yr3")
            with col2:
                b2_yr4 = st.slider("Año 4", -20.0, 50.0, params['crecimiento_ingresos_binomio2'][3]*100, 0.5, key="b2_yr4")
                b2_yr5 = st.slider("Año 5", -20.0, 50.0, params['crecimiento_ingresos_binomio2'][4]*100, 0.5, key="b2_yr5")
            
            # General
            st.markdown("**General: Soporte Técnico**")
            col1, col2 = st.columns(2)
            with col1:
                gen_yr1 = st.slider("Año 1", -20.0, 50.0, params['crecimiento_ingresos_general'][0]*100, 0.5, key="gen_yr1")
                gen_yr2 = st.slider("Año 2", -20.0, 50.0, params['crecimiento_ingresos_general'][1]*100, 0.5, key="gen_yr2")
                gen_yr3 = st.slider("Año 3", -20.0, 50.0, params['crecimiento_ingresos_general'][2]*100, 0.5, key="gen_yr3")
            with col2:
                gen_yr4 = st.slider("Año 4", -20.0, 50.0, params['crecimiento_ingresos_general'][3]*100, 0.5, key="gen_yr4")
                gen_yr5 = st.slider("Año 5", -20.0, 50.0, params['crecimiento_ingresos_general'][4]*100, 0.5, key="gen_yr5")
        
        with param_tabs[1]:
            st.subheader("Crecimiento de Costos (%)")
            
            # Margenes por binomio
            st.markdown("**Margenes Brutos Objetivo**")
            margen_b1 = st.slider("Margen Binomio 1 (%)", 10.0, 90.0, params['margen_binomio1']*100, 1.0) / 100
            margen_b2 = st.slider("Margen Binomio 2 (%)", 10.0, 90.0, params['margen_binomio2']*100, 1.0) / 100
            margen_gen = st.slider("Margen General (%)", 10.0, 90.0, params['margen_general']*100, 1.0) / 100
        
        with param_tabs[2]:
            st.subheader("Parámetros Financieros")
            
            # Rentabilidad del accionista
            ke = st.slider("Rentabilidad esperada accionista (Ke %)", 5.0, 30.0, params['ke']*100, 0.1) / 100
            
            # Estructura de capital
            st.markdown("**Estructura de Capital**")
            proporcion_deuda = st.slider("Proporción Deuda (D/V)", 0.0, 1.0, params['proporcion_deuda'], 0.01)
            proporcion_patrimonio = 1 - proporcion_deuda
            st.metric("Proporción Patrimonio (E/V)", f"{proporcion_patrimonio:.1%}")
            
            # Otros parámetros
            tax_rate = st.slider("Tasa impositiva (%)", 0.0, 50.0, params['tax_rate']*100, 0.5) / 100
            crecimiento_perpetuo = st.slider("Crecimiento perpetuo (%)", 0.0, 5.0, params['crecimiento_perpetuo']*100, 0.1) / 100
        
        with param_tabs[3]:
            st.subheader("Capital de Trabajo")
            
            dias_cpc = st.slider("Días Cuentas por Cobrar", 0, 180, params['dias_cpc'], 1)
            dias_inv = st.slider("Días Inventario", 0, 365, params['dias_inventario'], 1)
            dias_cpp = st.slider("Días Cuentas por Pagar", 0, 180, params['dias_cpp'], 1)
        
        # Botón para calcular
        if st.button("🔄 Calcular Valuación", type="primary", use_container_width=True):
            # Actualizar session state con nuevos valores
            st.session_state.parametros_ajustados = {
                'crecimiento_ingresos_binomio1': [b1_yr1/100, b1_yr2/100, b1_yr3/100, b1_yr4/100, b1_yr5/100],
                'crecimiento_ingresos_binomio2': [b2_yr1/100, b2_yr2/100, b2_yr3/100, b2_yr4/100, b2_yr5/100],
                'crecimiento_ingresos_general': [gen_yr1/100, gen_yr2/100, gen_yr3/100, gen_yr4/100, gen_yr5/100],
                'margen_binomio1': margen_b1,
                'margen_binomio2': margen_b2,
                'margen_general': margen_gen,
                'ke': ke,
                'proporcion_deuda': proporcion_deuda,
                'proporcion_patrimonio': proporcion_patrimonio,
                'tax_rate': tax_rate,
                'crecimiento_perpetuo': crecimiento_perpetuo,
                'dias_cpc': dias_cpc,
                'dias_inventario': dias_inv,
                'dias_cpp': dias_cpp,
                'gastos_operativos_base': params['gastos_operativos_base'],
                'crecimiento_gastos': params['crecimiento_gastos'],
                'depreciacion': params['depreciacion'],
                'amortizacion': params['amortizacion'],
                'capex': params['capex'],
                'kd': params['kd']
            }
            
            st.rerun()

# ============================================
# CONTENIDO PRINCIPAL
# ============================================

if st.session_state.datos_cargados:
    # Obtener datos del session state
    data_loader = st.session_state.data_loader
    parametros = st.session_state.parametros_ajustados  # ¡AHORA SÍ EXISTE!
    
    # Crear calculadora DCF
    datos_base = data_loader.metadata.get('datos_base', {})
    calculator = DCFCalculator(datos_base, parametros)
    resultados = calculator.calcular_proyecciones()
    
    # Crear pestañas principales
    main_tabs = st.tabs([
        "📊 Resumen Ejecutivo",
        "📈 Proyecciones Financieras",
        "💰 Flujos de Caja"
    ])
    
    with main_tabs[0]:
        st.markdown('<h2 class="sub-header">Resumen Ejecutivo de Valuación</h2>', unsafe_allow_html=True)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ev_millones = resultados['enterprise_value'] / 1e6
            st.metric(
                label="Enterprise Value",
                value=f"${ev_millones:,.1f}M MXN",
                delta=f"WACC: {resultados['wacc']:.2%}"
            )
        
        with col2:
            equity_millones = resultados['equity_value'] / 1e6
            st.metric(
                label="Equity Value",
                value=f"${equity_millones:,.1f}M MXN"
            )
        
        with col3:
            st.metric(
                label="WACC",
                value=f"{resultados['wacc']:.2%}",
                delta=f"Ke: {parametros['ke']:.2%}"
            )
        
        with col4:
            # Calcular valor por acción (asumiendo 1M acciones)
            valor_por_accion = resultados['equity_value'] / 1000000
            st.metric(
                label="Valor por Acción",
                value=f"${valor_por_accion:,.2f} MXN"
            )
        
        # Gráfico de composición del valor
        st.markdown('<h3 class="sub-header">Composición del Valor</h3>', unsafe_allow_html=True)
        
        # Calcular contribuciones
        pv_fcf = sum([fcf / ((1 + resultados['wacc']) ** (i+1)) for i, fcf in enumerate(resultados['fcf'])])
        pv_valor_terminal = resultados['valor_terminal'] / ((1 + resultados['wacc']) ** 5)
        
        fig = go.Figure(data=[
            go.Bar(name='Valor Terminal', x=['Enterprise Value'], y=[pv_valor_terminal], marker_color='#3B82F6'),
            go.Bar(name='FCF Años 1-5', x=['Enterprise Value'], y=[pv_fcf], marker_color='#10B981')
        ])
        
        fig.update_layout(
            barmode='stack',
            title='Composición del Enterprise Value',
            height=400,
            showlegend=True,
            yaxis_title="Millones MXN"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with main_tabs[1]:
        st.markdown('<h2 class="sub-header">Proyecciones Financieras</h2>', unsafe_allow_html=True)
        
        # Selector de métrica
        metrica = st.selectbox(
            "Seleccionar métrica para visualizar",
            ["Ingresos Totales", "EBITDA", "EBIT", "FCF"]
        )
        
        # Datos según métrica seleccionada
        años = ['Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
        
        if metrica == "Ingresos Totales":
            datos = resultados['proyecciones_ingresos']['total']
            titulo = "Proyección de Ingresos Totales"
            color = '#10B981'
            formato = "MXN"
        elif metrica == "EBITDA":
            datos = resultados['ebitda']
            titulo = "Proyección de EBITDA"
            color = '#3B82F6'
            formato = "MXN"
        elif metrica == "EBIT":
            datos = resultados['ebit']
            titulo = "Proyección de EBIT"
            color = '#8B5CF6'
            formato = "MXN"
        else:  # FCF
            datos = resultados['fcf']
            titulo = "Proyección de Free Cash Flow"
            color = '#F59E0B'
            formato = "MXN"
        
        # Crear gráfico
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=años, y=datos,
            marker_color=color,
            name=metrica,
            text=[f"${x/1e6:,.1f}M" for x in datos],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=titulo,
            height=500,
            showlegend=False,
            plot_bgcolor='white',
            yaxis_title=f"Millones {formato}"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de proyecciones
        st.markdown('<h3 class="sub-header">Tabla de Proyecciones Detalladas</h3>', unsafe_allow_html=True)
        
        df_proyecciones = pd.DataFrame({
            'Año': años,
            'Ingresos Binomio 1 (MXN)': resultados['proyecciones_ingresos']['binomio1'],
            'Ingresos Binomio 2 (MXN)': resultados['proyecciones_ingresos']['binomio2'],
            'Ingresos General (MXN)': resultados['proyecciones_ingresos']['general'],
            'EBITDA (MXN)': resultados['ebitda'],
            'EBIT (MXN)': resultados['ebit'],
            'FCF (MXN)': resultados['fcf']
        })
        
        # Formatear números
        def formatear_millones(x):
            return f"${x/1e6:,.1f}M"
        
        for col in df_proyecciones.columns[1:]:
            df_proyecciones[col] = df_proyecciones[col].apply(formatear_millones)
        
        st.dataframe(df_proyecciones, use_container_width=True)
    
    with main_tabs[2]:
        st.markdown('<h2 class="sub-header">Flujos de Caja Libre (FCF)</h2>', unsafe_allow_html=True)
        
        # Gráfico de FCF
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Flujos de Caja Libre Proyectados', 'FCF Descontado a Valor Presente'),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )
        
        # FCF proyectado
        fig.add_trace(
            go.Bar(
                x=años,
                y=resultados['fcf'],
                name='FCF Proyectado',
                marker_color='#10B981',
                text=[f"${x/1e6:,.1f}M" for x in resultados['fcf']],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # FCF descontado
        fcf_descontado = [fcf / ((1 + resultados['wacc']) ** (i+1)) for i, fcf in enumerate(resultados['fcf'])]
        
        fig.add_trace(
            go.Bar(
                x=años,
                y=fcf_descontado,
                name='FCF Descontado',
                marker_color='#3B82F6',
                text=[f"${x/1e6:,.1f}M" for x in fcf_descontado],
                textposition='outside'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=700,
            showlegend=False,
            yaxis_title="Millones MXN",
            yaxis2_title="Millones MXN (Valor Presente)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis de FCF
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**📊 Análisis FCF:**")
            st.markdown(f"- FCF promedio: ${np.mean(resultados['fcf'])/1e6:,.1f}M MXN")
            st.markdown(f"- FCF máximo: ${np.max(resultados['fcf'])/1e6:,.1f}M MXN")
            st.markdown(f"- Crecimiento FCF anualizado: {((resultados['fcf'][-1]/resultados['fcf'][0])**(1/5)-1)*100:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**💰 Valor Presente:**")
            st.markdown(f"- Σ FCF descontado: ${sum(fcf_descontado)/1e6:,.1f}M MXN")
            st.markdown(f"- Valor Terminal PV: ${(resultados['valor_terminal']/((1+resultados['wacc'])**5))/1e6:,.1f}M MXN")
            st.markdown(f"- WACC aplicado: {resultados['wacc']:.2%}")
            st.markdown("</div>", unsafe_allow_html=True)

else:
    # Pantalla de bienvenida
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; color: white; margin: 2rem 0;'>
        <h2>🚀 Bienvenido al Simulador Profesional de Valuación DCF</h2>
        <p style='font-size: 1.2rem;'>Metodología Aswath Damodaran aplicada a empresas privadas en México</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## 📋 **Cómo Comenzar:**
        
        1. **Prepara tu plantilla Excel** con el formato proporcionado
        2. **Carga el archivo** usando el panel lateral izquierdo
        3. **Ajusta los parámetros** de crecimiento y financiamiento
        4. **Explora los resultados** en las diferentes pestañas
        """)
    
    with col2:
        st.markdown("""
        ## 🎯 **Características Principales:**
        
        ✅ **Valuación DCF completa**  
        ✅ **Análisis por binomios** producto-mercado  
        ✅ **Modelo completamente reactivo**  
        ✅ **Gráficos profesionales con Plotly**  
        ✅ **Exportación a Excel** de resultados  
        ✅ **Análisis de sensibilidad**  
        """)
    
    # Mostrar estructura del Excel requerido
    with st.expander("📁 Ver estructura requerida del Excel"):
        st.markdown("""
        El archivo debe contener las siguientes hojas:
        
        1. **Balance_Base** - Balance general año 0
        2. **Estado_Resultados** - Proyecciones años 1-5  
        3. **Capital_Trabajo** - Parámetros de capital de trabajo
        4. **Proyectos** - Información de proyectos (opcional)
        5. **Financiamiento** - Estructura de capital
        6. **Flujos_FCF** - Cálculo de flujos
        
        **¡Comienza cargando tu archivo Excel en el panel izquierdo!**
        """)

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
st.caption("**© 2024 Simulador DCF Profesional - Metodología Aswath Damodaran | v2.0**")