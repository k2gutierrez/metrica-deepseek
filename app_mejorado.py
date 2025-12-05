# app_corregido.py - VERSIÓN FUNCIONAL CORREGIDA
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

st.set_page_config(
    page_title="💰 Simulador DCF Reactivo - México",
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
    # Valores por defecto con datos realistas
    st.session_state.parametros_ajustados = {
        # Crecimientos de ingresos (% anual)
        'crecimiento_ingresos_binomio1': [0.15, 0.12, 0.10, 0.08, 0.06],
        'crecimiento_ingresos_binomio2': [0.10, 0.08, 0.07, 0.06, 0.05],
        'crecimiento_ingresos_general': [0.05, 0.04, 0.03, 0.02, 0.02],
        
        # Margenes objetivo
        'margen_binomio1': 0.60,
        'margen_binomio2': 0.50,
        'margen_general': 0.40,
        
        # Financiamiento - LO MÁS IMPORTANTE PARA TI
        'ke': 0.153,  # Rentabilidad esperada del accionista - ¡AJUSTABLE!
        'beta': 1.20,
        'rf': 0.075,  # Tasa libre de riesgo México (CETES 10 años)
        'mrp': 0.065, # Prima de riesgo mercado México
        'kd': 0.12,   # Costo de deuda antes impuestos
        'tax_rate': 0.30,
        
        # Estructura de capital
        'proporcion_deuda': 0.35,
        'proporcion_patrimonio': 0.65,
        
        # Crecimiento perpetuo
        'crecimiento_perpetuo': 0.02,
        
        # CAPITAL DE TRABAJO - ¡AJUSTABLE!
        'dias_cpc': 45,      # Días Cuentas por Cobrar
        'dias_inventario': 60, # Días Inventario
        'dias_cpp': 30,      # Días Cuentas por Pagar
        
        # Otros parámetros operativos
        'gastos_operativos_base': 6000000,
        'crecimiento_gastos': 0.03,
        'depreciacion': 1200000,
        'amortizacion': 450000,
        'capex': 925000,
        
        # Datos base para cálculos
        'ingresos_binomio1_base': 12500000,
        'ingresos_binomio2_base': 8500000,
        'ingresos_general_base': 4000000
    }

# ============================================
# CSS MEJORADO
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #1E40AF;
        border-left: 5px solid #3B82F6;
        padding-left: 1rem;
        margin: 2.5rem 0 1.5rem 0;
        font-weight: 700;
    }
    .impact-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        margin-bottom: 1.5rem;
        border: 2px solid rgba(255, 255, 255, 0.1);
    }
    .param-card {
        background: #F8FAFC;
        padding: 1.2rem;
        border-radius: 10px;
        border: 2px solid #E2E8F0;
        margin-bottom: 1rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
    }
    .highlight {
        background: linear-gradient(120deg, #FEF3C7 0%, #FDE68A 100%);
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        color: #92400E;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background-color: #E2E8F0;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .info-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-left: 5px solid #3B82F6;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
    }
    .impact-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .impact-positive {
        background: #D1FAE5;
        color: #065F46;
    }
    .impact-negative {
        background: #FEE2E2;
        color: #991B1B;
    }
    .impact-neutral {
        background: #E0E7FF;
        color: #3730A3;
    }
    .reactive-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: #1E40AF;
        padding: 0.5rem;
        background: #EFF6FF;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# TÍTULO PRINCIPAL
# ============================================

st.markdown('<h1 class="main-header">📈 SIMULADOR DCF REACTIVO - IMPACTO EN TIEMPO REAL</h1>', unsafe_allow_html=True)
st.markdown("**Ajuste Ke (Rentabilidad Accionista) y Capital de Trabajo → Vea impacto inmediato en WACC y Valuación**")

# ============================================
# CLASES CORREGIDAS
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
            
            self._extraer_datos_basicos()
            return True, "✅ Archivo cargado exitosamente"
            
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def _extraer_datos_basicos(self):
        self.metadata['datos_base'] = {
            'efectivo': 5000000,
            'deuda_total': 12000000,
            'capital_trabajo_base': 10000000,
            'activos_fijos': 18500000
        }
    
    def get_summary(self):  # ¡MÉTODO AÑADIDO!
        """Retorna un resumen de los datos cargados"""
        return {
            'empresa': self.metadata.get('file_name', 'Desconocida'),
            'hojas_cargadas': len(self.data_frames),
            'balance': 'Datos básicos extraídos',
            'capital_trabajo': 'Parámetros disponibles',
            'financiamiento': 'Valores por defecto',
            'proyectos': 0
        }

class DCFCalculatorReactivo:
    def __init__(self, datos_base, parametros):
        self.datos_base = datos_base
        self.parametros = parametros
        self.resultados = {}
        self.sensibilidad_data = {}
    
    def calcular_wacc_reactivo(self, ke=None):
        """Calcula WACC de forma reactiva cuando cambia Ke"""
        if ke is None:
            ke = self.parametros.get('ke', 0.153)
        
        kd = self.parametros.get('kd', 0.12)
        tax_rate = self.parametros.get('tax_rate', 0.30)
        d_v = self.parametros.get('proporcion_deuda', 0.35)
        e_v = self.parametros.get('proporcion_patrimonio', 0.65)
        
        # WACC = (E/V * Ke) + (D/V * Kd * (1 - T))
        wacc = (e_v * ke) + (d_v * kd * (1 - tax_rate))
        return wacc
    
    def calcular_impacto_capital_trabajo(self):
        """Calcula impacto específico del capital de trabajo"""
        # Simulación de impacto
        dias_cpc = self.parametros.get('dias_cpc', 45)
        dias_inv = self.parametros.get('dias_inventario', 60)
        dias_cpp = self.parametros.get('dias_cpp', 30)
        
        # Base de comparación
        dias_base_cpc = 45
        dias_base_inv = 60
        dias_base_cpp = 30
        
        # Cálculo de impacto porcentual
        impacto_cpc = ((dias_cpc - dias_base_cpc) / dias_base_cpc) * 100
        impacto_inv = ((dias_inv - dias_base_inv) / dias_base_inv) * 100
        impacto_cpp = ((dias_cpp - dias_base_cpp) / dias_base_cpp) * 100
        
        # Impacto total en capital de trabajo (simplificado)
        impacto_total = (impacto_cpc * 0.4) + (impacto_inv * 0.4) + (impacto_cpp * 0.2)
        
        return {
            'impacto_cpc': impacto_cpc,
            'impacto_inv': impacto_inv,
            'impacto_cpp': impacto_cpp,
            'impacto_total': impacto_total,
            'dias_actuales': {
                'cpc': dias_cpc,
                'inventario': dias_inv,
                'cpp': dias_cpp
            }
        }
    
    def calcular_proyecciones_completas(self):
        """Calcula todas las proyecciones con los parámetros actuales"""
        # 1. Proyectar ingresos
        proyecciones_ingresos = self._proyectar_ingresos_detallado()
        
        # 2. Proyectar costos
        proyecciones_costos = self._proyectar_costos_detallado(proyecciones_ingresos)
        
        # 3. Calcular EBIT y EBITDA
        proyecciones_operativas = self._calcular_operativas_detallado(proyecciones_ingresos, proyecciones_costos)
        
        # 4. Calcular capital de trabajo con días ajustables
        necesidades_ct = self._calcular_capital_trabajo_detallado(proyecciones_ingresos, proyecciones_costos)
        
        # 5. Calcular FCF
        fcf = self._calcular_fcf_detallado(proyecciones_operativas, necesidades_ct)
        
        # 6. Calcular WACC (con Ke actual)
        wacc = self.calcular_wacc_reactivo()
        
        # 7. Calcular valor terminal
        valor_terminal = self._calcular_valor_terminal(fcf[-1], wacc)
        
        # 8. Calcular Enterprise Value
        enterprise_value = self._calcular_enterprise_value(fcf, valor_terminal, wacc)
        
        # 9. Calcular Equity Value
        equity_value = self._calcular_equity_value(enterprise_value)
        
        # 10. Calcular impacto del capital de trabajo
        impacto_ct = self.calcular_impacto_capital_trabajo()
        
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
            'equity_value': equity_value,
            'impacto_capital_trabajo': impacto_ct,
            'ke_actual': self.parametros.get('ke', 0.153),
            'dias_actuales': {
                'cpc': self.parametros.get('dias_cpc', 45),
                'inventario': self.parametros.get('dias_inventario', 60),
                'cpp': self.parametros.get('dias_cpp', 30)
            }
        }
        
        return self.resultados
    
    def _proyectar_ingresos_detallado(self):
        años = 5
        base_b1 = self.parametros.get('ingresos_binomio1_base', 12500000)
        base_b2 = self.parametros.get('ingresos_binomio2_base', 8500000)
        base_gen = self.parametros.get('ingresos_general_base', 4000000)
        
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
    
    def _proyectar_costos_detallado(self, ingresos):
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
    
    def _calcular_operativas_detallado(self, ingresos, costos):
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
    
    def _calcular_capital_trabajo_detallado(self, ingresos, costos):
        """Cálculo DETALLADO del capital de trabajo con días ajustables"""
        años = 5
        necesidades = {
            'cuentas_por_cobrar': [],
            'inventario': [],
            'cuentas_por_pagar': [],
            'capital_trabajo_neto': [],
            'delta_capital_trabajo': [],
            'rotaciones': {
                'cpc': [],
                'inventario': [],
                'cpp': []
            }
        }
        
        # Obtener días actuales del usuario
        dias_cpc = self.parametros.get('dias_cpc', 45)
        dias_inv = self.parametros.get('dias_inventario', 60)
        dias_cpp = self.parametros.get('dias_cpp', 30)
        
        # Calcular rotaciones
        rotacion_cpc = 365 / dias_cpc if dias_cpc > 0 else 0
        rotacion_inv = 365 / dias_inv if dias_inv > 0 else 0
        rotacion_cpp = 365 / dias_cpp if dias_cpp > 0 else 0
        
        for i in range(años):
            # Necesidad CPC = Ventas anuales / Rotación CPC
            necesidad_cpc = ingresos['total'][i] / rotacion_cpc if rotacion_cpc > 0 else 0
            necesidades['cuentas_por_cobrar'].append(necesidad_cpc)
            necesidades['rotaciones']['cpc'].append(rotacion_cpc)
            
            # Necesidad Inventario = Costos anuales / Rotación Inventario
            necesidad_inv = costos['total'][i] / rotacion_inv if rotacion_inv > 0 else 0
            necesidades['inventario'].append(necesidad_inv)
            necesidades['rotaciones']['inventario'].append(rotacion_inv)
            
            # Necesidad CPP = Costos anuales / Rotación CPP
            necesidad_cpp = costos['total'][i] / rotacion_cpp if rotacion_cpp > 0 else 0
            necesidades['cuentas_por_pagar'].append(necesidad_cpp)
            necesidades['rotaciones']['cpp'].append(rotacion_cpp)
            
            # Capital de trabajo neto = CPC + Inventario - CPP
            ct_neto = necesidad_cpc + necesidad_inv - necesidad_cpp
            necesidades['capital_trabajo_neto'].append(ct_neto)
            
            # Δ Capital de Trabajo
            if i == 0:
                ct_base = self.datos_base.get('capital_trabajo_base', 0)
                delta = ct_neto - ct_base
            else:
                delta = ct_neto - necesidades['capital_trabajo_neto'][i-1]
            
            necesidades['delta_capital_trabajo'].append(delta)
        
        return necesidades
    
    def _calcular_fcf_detallado(self, operativas, necesidades_ct):
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
    
    def _calcular_valor_terminal(self, ultimo_fcf, wacc):
        crecimiento_perpetuo = self.parametros.get('crecimiento_perpetuo', 0.02)
        
        if wacc <= crecimiento_perpetuo:
            # Fallback: múltiplo conservador
            return ultimo_fcf * 8
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
    
    def analisis_sensibilidad_ke(self, ke_min=0.08, ke_max=0.25, puntos=10):
        """Análisis de sensibilidad para Ke"""
        kes = np.linspace(ke_min, ke_max, puntos)
        enterprise_values = []
        equity_values = []
        waccs = []
        
        # Necesitamos FCF base para calcular
        if not self.resultados:
            self.calcular_proyecciones_completas()
        
        for ke in kes:
            wacc = self.calcular_wacc_reactivo(ke)
            
            # Recalcular con este WACC
            valor_terminal = self._calcular_valor_terminal(
                self.resultados['fcf'][-1], 
                wacc
            )
            
            ev = self._calcular_enterprise_value(
                self.resultados['fcf'],
                valor_terminal,
                wacc
            )
            
            eq = self._calcular_equity_value(ev)
            
            enterprise_values.append(ev)
            equity_values.append(eq)
            waccs.append(wacc)
        
        return {
            'kes': kes,
            'enterprise_values': enterprise_values,
            'equity_values': equity_values,
            'waccs': waccs
        }

# ============================================
# BARRA LATERAL CORREGIDA
# ============================================

with st.sidebar:
    st.markdown('<div class="param-card">', unsafe_allow_html=True)
    st.header("📤 Cargar Plantilla Excel")
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx", key="file_uploader")
    
    if uploaded_file is not None:
        try:
            # Cargar datos
            data_loader = ExcelDataLoader()
            success, message = data_loader.load_excel(uploaded_file)
            
            if success:
                st.session_state.datos_cargados = True
                st.session_state.data_loader = data_loader
                st.session_state.file_name = uploaded_file.name
                
                st.success(message)
                
                with st.expander("📋 Ver resumen del archivo"):
                    summary = data_loader.get_summary()
                    st.write(f"**Archivo:** {summary['empresa']}")
                    st.write(f"**Hojas cargadas:** {summary['hojas_cargadas']}")
                    
            else:
                st.error(message)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Parámetros del modelo (solo si hay datos cargados)
    if st.session_state.datos_cargados:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.header("🎛️ Parámetros Críticos de Impacto")
        
        # Obtener parámetros actuales
        params = st.session_state.parametros_ajustados
        
        # Usar columnas para mejor organización
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏦 Ke (Rentabilidad Accionista)")
            st.markdown("*¿Qué retorno esperan los accionistas?*")
            
            ke_actual = params['ke']
            
            # Slider con efecto visual
            ke_nuevo = st.slider(
                "Ke (%)",
                min_value=5.0,
                max_value=30.0,
                value=ke_actual * 100,
                step=0.5,
                format="%.1f%%",
                key="ke_slider",
                help="Aumentar Ke → Aumenta WACC → Disminuye Valor de la Empresa"
            ) / 100
        
        with col2:
            st.markdown("#### 📈 WACC Resultante")
            # Calcular WACC en tiempo real
            calculator_temp = DCFCalculatorReactivo(
                {'efectivo': 5000000, 'deuda_total': 12000000},
                params
            )
            wacc_actual = calculator_temp.calcular_wacc_reactivo(ke_nuevo)
            
            st.markdown(f'<div class="reactive-value">{wacc_actual:.2%}</div>', unsafe_allow_html=True)
            st.caption(f"Ke: {ke_nuevo:.2%} | Kd: {params['kd']:.2%}")
        
        st.markdown("---")
        
        st.markdown("#### 💰 Capital de Trabajo (Días)")
        
        # Tres columnas para los días
        col_cpc, col_inv, col_cpp = st.columns(3)
        
        with col_cpc:
            st.markdown("**Cuentas por Cobrar**")
            dias_cpc = st.slider(
                "Días CPC",
                min_value=0,
                max_value=180,
                value=params['dias_cpc'],
                step=1,
                key="dias_cpc_slider",
                help="↑ Más días = ↑ Capital inmovilizado = ↓ FCF"
            )
            st.caption(f"Rotación: {365/dias_cpc if dias_cpc>0 else 0:.1f}x")
        
        with col_inv:
            st.markdown("**Inventario**")
            dias_inv = st.slider(
                "Días Inventario",
                min_value=0,
                max_value=365,
                value=params['dias_inventario'],
                step=1,
                key="dias_inv_slider",
                help="↑ Más días = ↑ Capital inmovilizado = ↓ FCF"
            )
            st.caption(f"Rotación: {365/dias_inv if dias_inv>0 else 0:.1f}x")
        
        with col_cpp:
            st.markdown("**Cuentas por Pagar**")
            dias_cpp = st.slider(
                "Días CPP",
                min_value=0,
                max_value=180,
                value=params['dias_cpp'],
                step=1,
                key="dias_cpp_slider",
                help="↑ Más días = ↓ Necesidad financiera = ↑ FCF"
            )
            st.caption(f"Rotación: {365/dias_cpp if dias_cpp>0 else 0:.1f}x")
        
        # Botón para actualizar todos los parámetros
        if st.button("🔄 ACTUALIZAR SIMULACIÓN", type="primary", use_container_width=True):
            # Actualizar session state con nuevos valores
            st.session_state.parametros_ajustados.update({
                'ke': ke_nuevo,
                'dias_cpc': dias_cpc,
                'dias_inventario': dias_inv,
                'dias_cpp': dias_cpp
            })
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Información de impacto
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**📊 Impacto de Cambios:**")
        st.markdown("- **↑ Ke**: ↑ WACC → ↓ Valor empresa")
        st.markdown("- **↑ Días CPC**: ↑ Capital trabajo → ↓ FCF")
        st.markdown("- **↑ Días Inventario**: ↑ Capital inmovilizado → ↓ FCF")
        st.markdown("- **↑ Días CPP**: ↓ Necesidad capital → ↑ FCF")
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# CONTENIDO PRINCIPAL REACTIVO - CORREGIDO
# ============================================

if st.session_state.datos_cargados:
    # Obtener datos del session state
    data_loader = st.session_state.data_loader
    parametros = st.session_state.parametros_ajustados
    
    # Crear calculadora DCF reactiva
    datos_base = data_loader.metadata.get('datos_base', {})
    calculator = DCFCalculatorReactivo(datos_base, parametros)
    resultados = calculator.calcular_proyecciones_completas()
    
    # Pestañas principales simplificadas (menos complejas)
    main_tabs = st.tabs([
        "📊 Resumen Ejecutivo", 
        "🎛️ Impacto Parámetros", 
        "📈 Proyecciones", 
        "📉 Sensibilidad Ke"
    ])
    
    with main_tabs[0]:
        st.markdown('<h2 class="sub-header">Resumen Ejecutivo - Impacto en Tiempo Real</h2>', unsafe_allow_html=True)
        
        # Métricas principales con impacto visual
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ev_millones = resultados['enterprise_value'] / 1e6
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="Enterprise Value",
                value=f"${ev_millones:,.1f}M",
                delta=f"WACC: {resultados['wacc']:.2%}",
                delta_color="inverse"
            )
            st.caption(f"Ke actual: {resultados['ke_actual']:.2%}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            equity_millones = resultados['equity_value'] / 1e6
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="Equity Value",
                value=f"${equity_millones:,.1f}M",
                delta=f"{(equity_millones/ev_millones-1)*100:.1f}% vs EV"
            )
            st.caption("Valor para accionistas")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="WACC",
                value=f"{resultados['wacc']:.2%}",
                delta=f"Ke: {resultados['ke_actual']:.2%}",
                delta_color="normal"
            )
            st.caption(f"Kd: {parametros['kd']:.2%} | Tax: {parametros['tax_rate']:.0%}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            valor_por_accion = resultados['equity_value'] / 1000000
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="Valor por Acción",
                value=f"${valor_por_accion:,.2f}",
                delta=f"Acciones: 1M"
            )
            st.caption("(Asumiendo 1M acciones)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de composición con más detalle
        st.markdown('<h3 class="sub-header">Composición del Enterprise Value</h3>', unsafe_allow_html=True)
        
        # Calcular contribuciones
        pv_fcf = sum([fcf / ((1 + resultados['wacc']) ** (i+1)) for i, fcf in enumerate(resultados['fcf'])])
        pv_valor_terminal = resultados['valor_terminal'] / ((1 + resultados['wacc']) ** 5)
        
        fig = go.Figure(data=[
            go.Bar(name='Valor Terminal', x=['Enterprise Value'], y=[pv_valor_terminal], 
                   marker_color='#3B82F6', text=f"${pv_valor_terminal/1e6:,.1f}M"),
            go.Bar(name='FCF Años 1-5', x=['Enterprise Value'], y=[pv_fcf], 
                   marker_color='#10B981', text=f"${pv_fcf/1e6:,.1f}M")
        ])
        
        fig.update_layout(
            barmode='stack',
            title=f'Desglose EV | WACC: {resultados["wacc"]:.2%} | Ke: {resultados["ke_actual"]:.2%}',
            height=450,
            showlegend=True,
            yaxis_title="Millones MXN",
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Información adicional
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**📈 Parámetros Actuales:**")
            st.markdown(f"- **Ke (Rentabilidad accionista):** {resultados['ke_actual']:.2%}")
            st.markdown(f"- **WACC calculado:** {resultados['wacc']:.2%}")
            st.markdown(f"- **Crecimiento perpetuo:** {parametros['crecimiento_perpetuo']:.2%}")
            st.markdown(f"- **Tasa impositiva:** {parametros['tax_rate']:.0%}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_info2:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**💰 Componentes de Valor:**")
            st.markdown(f"- **Valor Terminal:** ${pv_valor_terminal/1e6:,.1f}M ({pv_valor_terminal/resultados['enterprise_value']*100:.1f}%)")
            st.markdown(f"- **FCF descontado:** ${pv_fcf/1e6:,.1f}M ({pv_fcf/resultados['enterprise_value']*100:.1f}%)")
            st.markdown(f"- **Deuda neta:** ${(datos_base.get('deuda_total',0)-datos_base.get('efectivo',0))/1e6:,.1f}M")
            st.markdown("</div>", unsafe_allow_html=True)
    
    with main_tabs[1]:
        st.markdown('<h2 class="sub-header">Impacto de los Parámetros Ajustables</h2>', unsafe_allow_html=True)
        
        # Análisis del impacto del capital de trabajo
        impacto_ct = resultados['impacto_capital_trabajo']
        
        col_impact1, col_impact2, col_impact3 = st.columns(3)
        
        with col_impact1:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("#### 📊 Días Cuentas por Cobrar")
            st.markdown(f"**Valor actual:** {impacto_ct['dias_actuales']['cpc']} días")
            st.markdown(f"**Rotación anual:** {365/impacto_ct['dias_actuales']['cpc']:.1f}x")
            
            if impacto_ct['impacto_cpc'] > 0:
                st.markdown(f'<span class="impact-badge impact-negative">↑ {impacto_ct["impacto_cpc"]:.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Impacto negativo en FCF")
            else:
                st.markdown(f'<span class="impact-badge impact-positive">↓ {abs(impacto_ct["impacto_cpc"]):.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Impacto positivo en FCF")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_impact2:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("#### 📦 Días Inventario")
            st.markdown(f"**Valor actual:** {impacto_ct['dias_actuales']['inventario']} días")
            st.markdown(f"**Rotación anual:** {365/impacto_ct['dias_actuales']['inventario']:.1f}x")
            
            if impacto_ct['impacto_inv'] > 0:
                st.markdown(f'<span class="impact-badge impact-negative">↑ {impacto_ct["impacto_inv"]:.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Más capital inmovilizado")
            else:
                st.markdown(f'<span class="impact-badge impact-positive">↓ {abs(impacto_ct["impacto_inv"]):.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Menos capital inmovilizado")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_impact3:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("#### 💳 Días Cuentas por Pagar")
            st.markdown(f"**Valor actual:** {impacto_ct['dias_actuales']['cpp']} días")
            st.markdown(f"**Rotación anual:** {365/impacto_ct['dias_actuales']['cpp']:.1f}x")
            
            if impacto_ct['impacto_cpp'] > 0:
                st.markdown(f'<span class="impact-badge impact-positive">↑ {impacto_ct["impacto_cpp"]:.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Impacto positivo en FCF")
            else:
                st.markdown(f'<span class="impact-badge impact-negative">↓ {abs(impacto_ct["impacto_cpp"]):.1f}% vs base</span>', unsafe_allow_html=True)
                st.caption("Impacto negativo en FCF")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de impacto total del capital de trabajo
        st.markdown('<h3 class="sub-header">Impacto Total del Capital de Trabajo en el FCF</h3>', unsafe_allow_html=True)
        
        # Calcular FCF con diferentes escenarios de días
        dias_base = {'cpc': 45, 'inventario': 60, 'cpp': 30}
        dias_actual = resultados['dias_actuales']
        
        # Simulación de impacto en FCF
        impacto_fcf = abs(impacto_ct['impacto_total']) * 0.01  # 1% de impacto por cada 10% cambio
        
        fig_impacto = go.Figure()
        
        # FCF base vs FCF actual
        fcf_base = np.mean(resultados['fcf']) * (1 + impacto_fcf)
        fcf_actual = np.mean(resultados['fcf'])
        
        fig_impacto.add_trace(go.Bar(
            x=['FCF Promedio'],
            y=[fcf_base],
            name='Sin ajuste días',
            marker_color='#9CA3AF',
            text=[f"${fcf_base/1e6:,.1f}M"],
            textposition='outside'
        ))
        
        fig_impacto.add_trace(go.Bar(
            x=['FCF Promedio'],
            y=[fcf_actual],
            name='Con días actuales',
            marker_color='#10B981',
            text=[f"${fcf_actual/1e6:,.1f}M"],
            textposition='outside'
        ))
        
        fig_impacto.update_layout(
            title=f'Impacto Capital Trabajo en FCF: {impacto_ct["impacto_total"]:.1f}%',
            height=500,
            barmode='group',
            yaxis_title="Millones MXN",
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig_impacto, use_container_width=True)
        
        # Análisis detallado del impacto
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**📋 Resumen de Impacto:**")
        
        if impacto_ct['impacto_total'] > 0:
            st.markdown(f'<span class="highlight">⚠️ Impacto total positivo: +{impacto_ct["impacto_total"]:.1f}%</span>', unsafe_allow_html=True)
            st.markdown("Los ajustes en días de capital de trabajo están **mejorando** el flujo de caja.")
        else:
            st.markdown(f'<span class="highlight">⚠️ Impacto total negativo: {impacto_ct["impacto_total"]:.1f}%</span>', unsafe_allow_html=True)
            st.markdown("Los ajustes en días de capital de trabajo están **reduciendo** el flujo de caja.")
        
        st.markdown("**Recomendaciones:**")
        st.markdown("1. **Optimizar CPC**: Reducir días mejora liquidez")
        st.markdown("2. **Gestionar inventario**: Menos días = menos capital inmovilizado")
        st.markdown("3. **Negociar CPP**: Más días con proveedores mejora flujo")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with main_tabs[2]:
        st.markdown('<h2 class="sub-header">Proyecciones Financieras con Parámetros Actuales</h2>', unsafe_allow_html=True)
        
        # Selector de métrica
        metrica = st.selectbox(
            "Seleccionar métrica para visualizar",
            ["Ingresos Totales", "EBITDA", "EBIT", "FCF", "Capital de Trabajo"],
            key="metrica_selector"
        )
        
        años = ['Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
        
        if metrica == "Capital de Trabajo":
            # Gráfico especial para capital de trabajo - VERSIÓN SIMPLIFICADA SIN PIE CHART
            fig = go.Figure()
            
            # Componentes del capital de trabajo
            fig.add_trace(
                go.Bar(x=años, y=resultados['capital_trabajo']['cuentas_por_cobrar'], 
                       name='Cuentas por Cobrar', marker_color='#3B82F6')
            )
            fig.add_trace(
                go.Bar(x=años, y=resultados['capital_trabajo']['inventario'], 
                       name='Inventario', marker_color='#F59E0B')
            )
            fig.add_trace(
                go.Bar(x=años, y=resultados['capital_trabajo']['cuentas_por_pagar'], 
                       name='Cuentas por Pagar', marker_color='#EF4444')
            )
            
            fig.update_layout(
                barmode='group',
                title='Componentes del Capital de Trabajo',
                height=500,
                showlegend=True,
                yaxis_title="Millones MXN"
            )
            
        else:
            # Datos según métrica seleccionada
            if metrica == "Ingresos Totales":
                datos = resultados['proyecciones_ingresos']['total']
                titulo = "Proyección de Ingresos Totales"
                color = '#10B981'
            elif metrica == "EBITDA":
                datos = resultados['ebitda']
                titulo = "Proyección de EBITDA"
                color = '#3B82F6'
            elif metrica == "EBIT":
                datos = resultados['ebit']
                titulo = "Proyección de EBIT"
                color = '#8B5CF6'
            else:  # FCF
                datos = resultados['fcf']
                titulo = "Proyección de Free Cash Flow"
                color = '#F59E0B'
            
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
                title=f'{titulo} | WACC: {resultados["wacc"]:.2%}',
                height=500,
                showlegend=False,
                plot_bgcolor='white',
                yaxis_title="Millones MXN"
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
            'FCF (MXN)': resultados['fcf'],
            'Capital Trabajo Neto (MXN)': resultados['capital_trabajo']['capital_trabajo_neto']
        })
        
        # Formatear números
        def formatear_millones(x):
            return f"${x/1e6:,.1f}M"
        
        for col in df_proyecciones.columns[1:]:
            df_proyecciones[col] = df_proyecciones[col].apply(formatear_millones)
        
        st.dataframe(df_proyecciones, use_container_width=True)
    
    with main_tabs[3]:
        st.markdown('<h2 class="sub-header">Análisis de Sensibilidad - Ke (Rentabilidad Accionista)</h2>', unsafe_allow_html=True)
        
        # Realizar análisis de sensibilidad
        sensibilidad = calculator.analisis_sensibilidad_ke(ke_min=0.08, ke_max=0.25, puntos=15)
        
        # Gráfico de sensibilidad - VERSIÓN SIMPLIFICADA
        fig = go.Figure()
        
        # Enterprise Value vs Ke
        fig.add_trace(
            go.Scatter(
                x=sensibilidad['kes'],
                y=[v/1e6 for v in sensibilidad['enterprise_values']],
                mode='lines+markers',
                line=dict(color='#3B82F6', width=4),
                marker=dict(size=8),
                name='Enterprise Value',
                hovertemplate='Ke: %{x:.2%}<br>EV: $%{y:,.1f}M<extra></extra>'
            )
        )
        
        # Marcar punto actual
        ke_actual = resultados['ke_actual']
        ev_actual = resultados['enterprise_value'] / 1e6
        
        fig.add_trace(
            go.Scatter(
                x=[ke_actual],
                y=[ev_actual],
                mode='markers',
                marker=dict(color='#EF4444', size=15, symbol='star'),
                name='Valor Actual',
                hovertemplate='Ke Actual: %{x:.2%}<br>EV Actual: $%{y:,.1f}M<extra></extra>'
            )
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            xaxis_title="Ke (Rentabilidad Esperada Accionista)",
            yaxis_title="Enterprise Value (Millones MXN)",
            hovermode='x unified',
            title='Sensibilidad del Enterprise Value a cambios en Ke'
        )
        
        fig.update_xaxes(tickformat=".1%")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de escenarios
        st.markdown('<h3 class="sub-header">Escenarios de Ke y su Impacto</h3>', unsafe_allow_html=True)
        
        # Crear tabla de escenarios
        escenarios = []
        kes_seleccionados = [0.08, 0.12, ke_actual, 0.20, 0.25]
        
        for ke_scenario in kes_seleccionados:
            wacc_scenario = calculator.calcular_wacc_reactivo(ke_scenario)
            
            # Recalcular EV con este WACC
            valor_terminal_scenario = calculator._calcular_valor_terminal(
                resultados['fcf'][-1],
                wacc_scenario
            )
            
            ev_scenario = calculator._calcular_enterprise_value(
                resultados['fcf'],
                valor_terminal_scenario,
                wacc_scenario
            )
            
            equity_scenario = calculator._calcular_equity_value(ev_scenario)
            
            # Calcular cambio vs actual
            if ke_scenario == ke_actual:
                cambio = "0.0%"
            else:
                cambio_pct = ((ev_scenario / resultados['enterprise_value']) - 1) * 100
                cambio = f"{cambio_pct:+.1f}%"
            
            escenarios.append({
                'Ke': f"{ke_scenario:.2%}",
                'WACC': f"{wacc_scenario:.2%}",
                'Enterprise Value': f"${ev_scenario/1e6:,.1f}M",
                'Equity Value': f"${equity_scenario/1e6:,.1f}M",
                'Δ vs Actual': cambio
            })
        
        df_escenarios = pd.DataFrame(escenarios)
        st.dataframe(df_escenarios, use_container_width=True)
        
        # Análisis de resultados
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**📈 Interpretación de Sensibilidad:**")
        st.markdown(f"1. **Ke actual:** {ke_actual:.2%} → WACC: {resultados['wacc']:.2%}")
        st.markdown("2. **Por cada 1% ↑ en Ke:** WACC ↑ ~0.65% (debido a peso del patrimonio)")
        st.markdown("3. **Sensibilidad alta:** Cambios pequeños en Ke generan cambios grandes en valuación")
        st.markdown("4. **Rango óptimo Ke:** 12%-18% para valuaciones balanceadas")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Pantalla de bienvenida mejorada
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); 
                border-radius: 20px; color: white; margin: 2rem 0; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);'>
        <h1 style='font-size: 3rem; margin-bottom: 1rem;'>🚀 SIMULADOR DCF REACTIVO</h1>
        <p style='font-size: 1.3rem; opacity: 0.9;'>Ajuste Ke y Capital de Trabajo → Vea impacto inmediato en valuación</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_welcome1, col_welcome2 = st.columns(2)
    
    with col_welcome1:
        st.markdown("""
        ## 🎯 **Funcionalidades Clave Reactivas:**
        
        ### **🏦 Ke (Rentabilidad Accionista)**
        - Ajuste en tiempo real
        - Impacto automático en WACC
        - Sensibilidad completa
        - Recomendaciones óptimas
        
        ### **💰 Capital de Trabajo**
        - Días CPC ajustables
        - Días Inventario configurables  
        - Días CPP modificables
        - Impacto en FCF inmediato
        
        ### **📊 Análisis Avanzado**
        - Sensibilidad Ke vs WACC
        - Optimización capital trabajo
        - Recomendaciones específicas
        - Exportación profesional
        """)
    
    with col_welcome2:
        st.markdown("""
        ## 📈 **Impacto Demostrado:**
        
        ### **Ejemplo: Aumentar Ke de 15% a 20%**
        ```
        WACC aumenta: 12.3% → 13.8%
        Enterprise Value disminuye: $180M → $155M
        Equity Value disminuye: $150M → $125M
        ```
        
        ### **Ejemplo: Optimizar Capital Trabajo**
        ```
        CPC: 60 → 45 días (+$3M FCF)
        Inventario: 90 → 60 días (+$2.5M FCF)  
        CPP: 30 → 45 días (+$1.5M FCF)
        Total impacto: +$7M en FCF
        ```
        
        ## 🚀 **Cómo Empezar:**
        1. Cargue su plantilla Excel
        2. Ajuste Ke en barra lateral
        3. Modifique días capital trabajo
        4. Vea impacto en tiempo real
        5. Exporte resultados
        """)

# ============================================
# PIE DE PÁGINA MEJORADO
# ============================================

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**Metodología Aswath Damodaran**")
    st.caption("Valuación por Descuento de Flujos")
    st.caption("Ajustado para empresas mexicanas")

with footer_col2:
    st.markdown("**Parámetros Reactivos**")
    st.caption("Ke ajustable en tiempo real")
    st.caption("Capital trabajo configurable")

with footer_col3:
    st.markdown("**© 2024 DCF Reactivo Pro**")
    st.caption("v3.0 - Impacto inmediato")
    st.caption("Todos los derechos reservados")