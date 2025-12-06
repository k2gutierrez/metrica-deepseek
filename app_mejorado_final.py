# app_mejorado_completo.py - VERSIÓN COMPLETA CON CONTROLES DE CRECIMIENTOS
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
        # Crecimientos de ingresos (% anual) - AHORA MODIFICABLES POR AÑO
        'crecimiento_ingresos_binomio1': [0.15, 0.12, 0.10, 0.08, 0.06],
        'crecimiento_ingresos_binomio2': [0.10, 0.08, 0.07, 0.06, 0.05],
        'crecimiento_ingresos_general': [0.05, 0.04, 0.03, 0.02, 0.02],
        
        # Crecimientos de costos (% anual) - NUEVOS: MODIFICABLES POR AÑO
        'crecimiento_costos_binomio1': [0.10, 0.08, 0.07, 0.06, 0.05],
        'crecimiento_costos_binomio2': [0.08, 0.07, 0.06, 0.05, 0.04],
        'crecimiento_costos_general': [0.04, 0.03, 0.03, 0.02, 0.02],
        
        # Margenes objetivo
        'margen_binomio1': 0.60,
        'margen_binomio2': 0.50,
        'margen_general': 0.40,
        
        # Financiamiento
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
        'ingresos_general_base': 4000000,
        
        # Costos base para cálculos - NUEVOS
        'costos_binomio1_base': 5000000,
        'costos_binomio2_base': 4250000,
        'costos_general_base': 2400000
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
    .growth-control {
        background: #FFFFFF;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        margin-bottom: 0.5rem;
    }
    .growth-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    .growth-positive {
        background: #D1FAE5;
        color: #065F46;
    }
    .growth-negative {
        background: #FEE2E2;
        color: #991B1B;
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
    .highlight {
        background: linear-gradient(120deg, #FEF3C7 0%, #FDE68A 100%);
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        color: #92400E;
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

st.markdown('<h1 class="main-header">📈 SIMULADOR DCF REACTIVO - CONTROL COMPLETO DE CRECIMIENTOS</h1>', unsafe_allow_html=True)
st.markdown("**Ajuste crecimientos por binomio/año, Ke y Capital de Trabajo → Vea impacto inmediato en valuación**")

# ============================================
# CLASES CORREGIDAS (MEJORADAS)
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
        # Extraer datos base de todas las hojas
        datos_base = {
            'efectivo': 5000000,
            'deuda_total': 12000000,
            'capital_trabajo_base': 10000000,
            'activos_fijos': 18500000
        }
        
        # Intentar extraer del balance
        if 'Balance_Base' in self.data_frames:
            df_balance = self.data_frames['Balance_Base']
            for _, row in df_balance.iterrows():
                if row['CODIGO'] == 'AC01':
                    datos_base['efectivo'] = row['AÑO_0_MXN']
                elif row['CODIGO'] == 'PC02':
                    deuda_corto = row['AÑO_0_MXN']
                elif row['CODIGO'] == 'PNC01':
                    deuda_largo = row['AÑO_0_MXN']
                    datos_base['deuda_total'] = deuda_corto + deuda_largo
        
        # Extraer datos de estado de resultados
        if 'Estado_Resultados' in self.data_frames:
            df_er = self.data_frames['Estado_Resultados']
            
            # Buscar valores base (AÑO_1 como referencia)
            for _, row in df_er.iterrows():
                concepto = str(row['CONCEPTO']).strip()
                
                if 'INGRESOS BINOMIO 1' in concepto:
                    # Calcular base (año 0) asumiendo crecimiento del 15%
                    datos_base['ingresos_binomio1_base'] = row['AÑO_1'] / 1.15
                elif 'INGRESOS BINOMIO 2' in concepto:
                    datos_base['ingresos_binomio2_base'] = row['AÑO_1'] / 1.10
                elif 'INGRESOS GENERAL' in concepto:
                    datos_base['ingresos_general_base'] = row['AÑO_1'] / 1.05
                elif 'COSTOS BINOMIO 1' in concepto:
                    datos_base['costos_binomio1_base'] = row['AÑO_1'] / 1.10
                elif 'COSTOS BINOMIO 2' in concepto:
                    datos_base['costos_binomio2_base'] = row['AÑO_1'] / 1.08
                elif 'COSTOS GENERAL' in concepto:
                    datos_base['costos_general_base'] = row['AÑO_1'] / 1.04
        
        self.metadata['datos_base'] = datos_base
    
    def get_summary(self):
        """Retorna un resumen de los datos cargados"""
        return {
            'empresa': self.metadata.get('file_name', 'Desconocida'),
            'hojas_cargadas': len(self.data_frames),
            'balance': 'Datos básicos extraídos',
            'capital_trabajo': 'Parámetros disponibles',
            'financiamiento': 'Valores por defecto'
        }

class DCFCalculatorReactivo:
    def __init__(self, datos_base, parametros):
        self.datos_base = datos_base
        self.parametros = parametros
        self.resultados = {}
    
    def calcular_wacc_reactivo(self, ke=None):
        """Calcula WACC de forma reactiva cuando cambia Ke"""
        if ke is None:
            ke = self.parametros.get('ke', 0.153)
        
        kd = self.parametros.get('kd', 0.12)
        tax_rate = self.parametros.get('tax_rate', 0.30)
        d_v = self.parametros.get('proporcion_deuda', 0.35)
        e_v = self.parametros.get('proporcion_patrimonio', 0.65)
        
        wacc = (e_v * ke) + (d_v * kd * (1 - tax_rate))
        return wacc
    
    def calcular_impacto_capital_trabajo(self):
        """Calcula impacto específico del capital de trabajo"""
        dias_cpc = self.parametros.get('dias_cpc', 45)
        dias_inv = self.parametros.get('dias_inventario', 60)
        dias_cpp = self.parametros.get('dias_cpp', 30)
        
        dias_base_cpc = 45
        dias_base_inv = 60
        dias_base_cpp = 30
        
        impacto_cpc = ((dias_cpc - dias_base_cpc) / dias_base_cpc) * 100
        impacto_inv = ((dias_inv - dias_base_inv) / dias_base_inv) * 100
        impacto_cpp = ((dias_cpp - dias_base_cpp) / dias_base_cpp) * 100
        
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
        # 1. Proyectar ingresos (CON CRECIMIENTOS AJUSTABLES POR AÑO)
        proyecciones_ingresos, crecimientos_ingresos = self._proyectar_ingresos_detallado()
        
        # 2. Proyectar costos (CON CRECIMIENTOS AJUSTABLES POR AÑO)
        proyecciones_costos, crecimientos_costos = self._proyectar_costos_detallado()
        
        # 3. Calcular EBIT y EBITDA
        proyecciones_operativas = self._calcular_operativas_detallado(proyecciones_ingresos, proyecciones_costos)
        
        # 4. Calcular capital de trabajo
        necesidades_ct = self._calcular_capital_trabajo_detallado(proyecciones_ingresos, proyecciones_costos)
        
        # 5. Calcular FCF
        fcf = self._calcular_fcf_detallado(proyecciones_operativas, necesidades_ct)
        
        # 6. Calcular WACC
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
            'crecimientos_ingresos': crecimientos_ingresos,
            'crecimientos_costos': crecimientos_costos,
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
        """Proyecta ingresos con crecimientos ajustables por año"""
        años = 5
        
        # Bases
        base_b1 = self.parametros.get('ingresos_binomio1_base', 12500000)
        base_b2 = self.parametros.get('ingresos_binomio2_base', 8500000)
        base_gen = self.parametros.get('ingresos_general_base', 4000000)
        
        # Crecimientos ajustables por año
        crecimiento_b1 = self.parametros.get('crecimiento_ingresos_binomio1', [0.15, 0.12, 0.10, 0.08, 0.06])
        crecimiento_b2 = self.parametros.get('crecimiento_ingresos_binomio2', [0.10, 0.08, 0.07, 0.06, 0.05])
        crecimiento_gen = self.parametros.get('crecimiento_ingresos_general', [0.05, 0.04, 0.03, 0.02, 0.02])
        
        ingresos = {
            'binomio1': [base_b1 * (1 + crecimiento_b1[0])],
            'binomio2': [base_b2 * (1 + crecimiento_b2[0])],
            'general': [base_gen * (1 + crecimiento_gen[0])],
            'total': []
        }
        
        # Proyectar años 2-5
        for i in range(1, años):
            ingresos['binomio1'].append(ingresos['binomio1'][-1] * (1 + crecimiento_b1[i]))
            ingresos['binomio2'].append(ingresos['binomio2'][-1] * (1 + crecimiento_b2[i]))
            ingresos['general'].append(ingresos['general'][-1] * (1 + crecimiento_gen[i]))
        
        # Calcular totales
        for i in range(años):
            ingresos['total'].append(ingresos['binomio1'][i] + ingresos['binomio2'][i] + ingresos['general'][i])
        
        return ingresos, {
            'binomio1': crecimiento_b1,
            'binomio2': crecimiento_b2,
            'general': crecimiento_gen
        }
    
    def _proyectar_costos_detallado(self):
        """Proyecta costos con crecimientos ajustables por año"""
        años = 5
        
        # Bases
        base_c1 = self.parametros.get('costos_binomio1_base', 5000000)
        base_c2 = self.parametros.get('costos_binomio2_base', 4250000)
        base_cgen = self.parametros.get('costos_general_base', 2400000)
        
        # Crecimientos ajustables por año
        crecimiento_c1 = self.parametros.get('crecimiento_costos_binomio1', [0.10, 0.08, 0.07, 0.06, 0.05])
        crecimiento_c2 = self.parametros.get('crecimiento_costos_binomio2', [0.08, 0.07, 0.06, 0.05, 0.04])
        crecimiento_cgen = self.parametros.get('crecimiento_costos_general', [0.04, 0.03, 0.03, 0.02, 0.02])
        
        costos = {
            'binomio1': [base_c1 * (1 + crecimiento_c1[0])],
            'binomio2': [base_c2 * (1 + crecimiento_c2[0])],
            'general': [base_cgen * (1 + crecimiento_cgen[0])],
            'total': []
        }
        
        # Proyectar años 2-5
        for i in range(1, años):
            costos['binomio1'].append(costos['binomio1'][-1] * (1 + crecimiento_c1[i]))
            costos['binomio2'].append(costos['binomio2'][-1] * (1 + crecimiento_c2[i]))
            costos['general'].append(costos['general'][-1] * (1 + crecimiento_cgen[i]))
        
        # Calcular totales
        for i in range(años):
            costos['total'].append(costos['binomio1'][i] + costos['binomio2'][i] + costos['general'][i])
        
        return costos, {
            'binomio1': crecimiento_c1,
            'binomio2': crecimiento_c2,
            'general': crecimiento_cgen
        }
    
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
        años = 5
        necesidades = {
            'cuentas_por_cobrar': [],
            'inventario': [],
            'cuentas_por_pagar': [],
            'capital_trabajo_neto': [],
            'delta_capital_trabajo': []
        }
        
        dias_cpc = self.parametros.get('dias_cpc', 45)
        dias_inv = self.parametros.get('dias_inventario', 60)
        dias_cpp = self.parametros.get('dias_cpp', 30)
        
        rotacion_cpc = 365 / dias_cpc if dias_cpc > 0 else 0
        rotacion_inv = 365 / dias_inv if dias_inv > 0 else 0
        rotacion_cpp = 365 / dias_cpp if dias_cpp > 0 else 0
        
        for i in range(años):
            necesidad_cpc = ingresos['total'][i] / rotacion_cpc if rotacion_cpc > 0 else 0
            necesidades['cuentas_por_cobrar'].append(necesidad_cpc)
            
            necesidad_inv = costos['total'][i] / rotacion_inv if rotacion_inv > 0 else 0
            necesidades['inventario'].append(necesidad_inv)
            
            necesidad_cpp = costos['total'][i] / rotacion_cpp if rotacion_cpp > 0 else 0
            necesidades['cuentas_por_pagar'].append(necesidad_cpp)
            
            ct_neto = necesidad_cpc + necesidad_inv - necesidad_cpp
            necesidades['capital_trabajo_neto'].append(ct_neto)
            
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
        
        if not self.resultados:
            self.calcular_proyecciones_completas()
        
        for ke in kes:
            wacc = self.calcular_wacc_reactivo(ke)
            
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
# BARRA LATERAL MEJORADA CON CONTROLES DE CRECIMIENTO
# ============================================

with st.sidebar:
    st.markdown('<div class="param-card">', unsafe_allow_html=True)
    st.header("📤 Cargar Plantilla Excel")
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx", key="file_uploader")
    
    if uploaded_file is not None:
        try:
            if st.session_state.get('file_name') != uploaded_file.name:
                data_loader = ExcelDataLoader()
                success, message = data_loader.load_excel(uploaded_file)
                
                if success:
                    st.session_state.datos_cargados = True
                    st.session_state.data_loader = data_loader
                    st.session_state.file_name = uploaded_file.name
                    
                    # Actualizar parámetros con datos del Excel
                    if 'datos_base' in data_loader.metadata:
                        st.session_state.parametros_ajustados.update(data_loader.metadata['datos_base'])
                    
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.info("✅ Archivo ya cargado")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Parámetros del modelo (solo si hay datos cargados)
    if st.session_state.datos_cargados:
        st.markdown('<div class="param-card">', unsafe_allow_html=True)
        st.header("🎛️ Parámetros Críticos de Impacto")
        
        params = st.session_state.parametros_ajustados
        
        # Ke y WACC
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏦 Ke (Rentabilidad Accionista)")
            ke_actual = params['ke']
            ke_nuevo = st.slider(
                "Ke (%)",
                min_value=5.0,
                max_value=30.0,
                value=ke_actual * 100,
                step=0.5,
                format="%.1f%%",
                key="ke_slider"
            ) / 100
        
        with col2:
            st.markdown("#### 📈 WACC Resultante")
            calculator_temp = DCFCalculatorReactivo(
                {'efectivo': 5000000, 'deuda_total': 12000000},
                params
            )
            wacc_actual = calculator_temp.calcular_wacc_reactivo(ke_nuevo)
            st.markdown(f'<div class="reactive-value">{wacc_actual:.2%}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Capital de Trabajo
        st.markdown("#### 💰 Capital de Trabajo (Días)")
        
        col_cpc, col_inv, col_cpp = st.columns(3)
        
        with col_cpc:
            dias_cpc = st.slider(
                "Días CPC",
                min_value=0,
                max_value=180,
                value=params['dias_cpc'],
                step=1,
                key="dias_cpc_slider"
            )
        
        with col_inv:
            dias_inv = st.slider(
                "Días Inventario",
                min_value=0,
                max_value=365,
                value=params['dias_inventario'],
                step=1,
                key="dias_inv_slider"
            )
        
        with col_cpp:
            dias_cpp = st.slider(
                "Días CPP",
                min_value=0,
                max_value=180,
                value=params['dias_cpp'],
                step=1,
                key="dias_cpp_slider"
            )
        
        st.markdown("---")
        
        # ============================================
        # NUEVO: CONTROLES DE CRECIMIENTOS DE INGRESOS
        # ============================================
        
        st.markdown("#### 📈 Crecimientos de Ingresos por Año")
        
        with st.expander("Binomio 1 - Ingresos", expanded=True):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_b1 = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params['crecimiento_ingresos_binomio1'][i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"ing_b1_a{año}"
                    )
                    nuevos_crec_b1.append(nuevo_valor / 100)
        
        with st.expander("Binomio 2 - Ingresos", expanded=False):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_b2 = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params['crecimiento_ingresos_binomio2'][i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"ing_b2_a{año}"
                    )
                    nuevos_crec_b2.append(nuevo_valor / 100)
        
        with st.expander("General - Ingresos", expanded=False):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_gen = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params['crecimiento_ingresos_general'][i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"ing_gen_a{año}"
                    )
                    nuevos_crec_gen.append(nuevo_valor / 100)
        
        st.markdown("---")
        
        # ============================================
        # NUEVO: CONTROLES DE CRECIMIENTOS DE COSTOS
        # ============================================
        
        st.markdown("#### 📉 Crecimientos de Costos por Año")
        
        with st.expander("Binomio 1 - Costos", expanded=False):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_c1 = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params.get('crecimiento_costos_binomio1', [0.10, 0.08, 0.07, 0.06, 0.05])[i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"cos_b1_a{año}"
                    )
                    nuevos_crec_c1.append(nuevo_valor / 100)
        
        with st.expander("Binomio 2 - Costos", expanded=False):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_c2 = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params.get('crecimiento_costos_binomio2', [0.08, 0.07, 0.06, 0.05, 0.04])[i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"cos_b2_a{año}"
                    )
                    nuevos_crec_c2.append(nuevo_valor / 100)
        
        with st.expander("General - Costos", expanded=False):
            st.markdown("**Tasa de crecimiento anual (%)**")
            cols = st.columns(5)
            nuevos_crec_cgen = []
            for i, col in enumerate(cols):
                with col:
                    año = i + 1
                    valor_actual = params.get('crecimiento_costos_general', [0.04, 0.03, 0.03, 0.02, 0.02])[i] * 100
                    nuevo_valor = st.number_input(
                        f"A{año}",
                        min_value=-50.0,
                        max_value=100.0,
                        value=float(valor_actual),
                        step=1.0,
                        format="%.1f",
                        key=f"cos_gen_a{año}"
                    )
                    nuevos_crec_cgen.append(nuevo_valor / 100)
        
        # Botón para actualizar todos los parámetros
        if st.button("🔄 ACTUALIZAR SIMULACIÓN COMPLETA", type="primary", use_container_width=True):
            # Actualizar session state con nuevos valores
            st.session_state.parametros_ajustados.update({
                'ke': ke_nuevo,
                'dias_cpc': dias_cpc,
                'dias_inventario': dias_inv,
                'dias_cpp': dias_cpp,
                'crecimiento_ingresos_binomio1': nuevos_crec_b1,
                'crecimiento_ingresos_binomio2': nuevos_crec_b2,
                'crecimiento_ingresos_general': nuevos_crec_gen,
                'crecimiento_costos_binomio1': nuevos_crec_c1,
                'crecimiento_costos_binomio2': nuevos_crec_c2,
                'crecimiento_costos_general': nuevos_crec_cgen
            })
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# CONTENIDO PRINCIPAL
# ============================================

if st.session_state.datos_cargados:
    data_loader = st.session_state.data_loader
    parametros = st.session_state.parametros_ajustados
    
    datos_base = data_loader.metadata.get('datos_base', {})
    calculator = DCFCalculatorReactivo(datos_base, parametros)
    resultados = calculator.calcular_proyecciones_completas()
    
    # Pestañas principales
    main_tabs = st.tabs([
        "📊 Resumen Ejecutivo", 
        "🎛️ Control Crecimientos", 
        "📈 Proyecciones", 
        "📉 Sensibilidad Ke"
    ])
    
    with main_tabs[0]:
        st.markdown('<h2 class="sub-header">Resumen Ejecutivo - Impacto en Tiempo Real</h2>', unsafe_allow_html=True)
        
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
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            equity_millones = resultados['equity_value'] / 1e6
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="Equity Value",
                value=f"${equity_millones:,.1f}M",
                delta=f"Valor para accionistas"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="WACC",
                value=f"{resultados['wacc']:.2%}",
                delta=f"Ke: {resultados['ke_actual']:.2%}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            valor_por_accion = resultados['equity_value'] / 1000000
            st.markdown('<div class="impact-card">', unsafe_allow_html=True)
            st.metric(
                label="Valor por Acción",
                value=f"${valor_por_accion:,.2f}",
                delta=f"Acciones: 1M"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico de composición
        st.markdown('<h3 class="sub-header">Composición del Enterprise Value</h3>', unsafe_allow_html=True)
        
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
            title=f'Desglose EV | WACC: {resultados["wacc"]:.2%}',
            height=450,
            showlegend=True,
            yaxis_title="Millones MXN"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with main_tabs[1]:
        st.markdown('<h2 class="sub-header">Control Detallado de Crecimientos</h2>', unsafe_allow_html=True)
        
        # Mostrar tabla de crecimientos actuales
        st.markdown("#### 📋 Crecimientos de Ingresos Actuales")
        
        años = ['Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
        
        df_crecimientos = pd.DataFrame({
            'Año': años,
            'Binomio 1': [f"{x:.1%}" for x in resultados['crecimientos_ingresos']['binomio1']],
            'Binomio 2': [f"{x:.1%}" for x in resultados['crecimientos_ingresos']['binomio2']],
            'General': [f"{x:.1%}" for x in resultados['crecimientos_ingresos']['general']]
        })
        
        st.dataframe(df_crecimientos, use_container_width=True)
        
        # Gráfico de tendencia de crecimientos
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=años,
            y=[x * 100 for x in resultados['crecimientos_ingresos']['binomio1']],
            mode='lines+markers',
            name='Binomio 1',
            line=dict(color='#3B82F6', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=años,
            y=[x * 100 for x in resultados['crecimientos_ingresos']['binomio2']],
            mode='lines+markers',
            name='Binomio 2',
            line=dict(color='#10B981', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=años,
            y=[x * 100 for x in resultados['crecimientos_ingresos']['general']],
            mode='lines+markers',
            name='General',
            line=dict(color='#F59E0B', width=3)
        ))
        
        fig.update_layout(
            title='Tendencias de Crecimiento de Ingresos',
            height=500,
            xaxis_title="Año",
            yaxis_title="Tasa de Crecimiento (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Impacto de los crecimientos en los ingresos
        st.markdown("#### 📊 Impacto de los Crecimientos en los Ingresos")
        
        col_ing1, col_ing2, col_ing3 = st.columns(3)
        
        with col_ing1:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("##### Binomio 1")
            ing_a1 = resultados['proyecciones_ingresos']['binomio1'][0] / 1e6
            ing_a5 = resultados['proyecciones_ingresos']['binomio1'][-1] / 1e6
            crecimiento_total = (ing_a5 / ing_a1 - 1) * 100
            
            st.metric(
                "Ingreso Año 1",
                f"${ing_a1:,.1f}M"
            )
            st.metric(
                "Ingreso Año 5",
                f"${ing_a5:,.1f}M",
                delta=f"{crecimiento_total:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_ing2:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("##### Binomio 2")
            ing_a1 = resultados['proyecciones_ingresos']['binomio2'][0] / 1e6
            ing_a5 = resultados['proyecciones_ingresos']['binomio2'][-1] / 1e6
            crecimiento_total = (ing_a5 / ing_a1 - 1) * 100
            
            st.metric(
                "Ingreso Año 1",
                f"${ing_a1:,.1f}M"
            )
            st.metric(
                "Ingreso Año 5",
                f"${ing_a5:,.1f}M",
                delta=f"{crecimiento_total:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_ing3:
            st.markdown('<div class="param-card">', unsafe_allow_html=True)
            st.markdown("##### General")
            ing_a1 = resultados['proyecciones_ingresos']['general'][0] / 1e6
            ing_a5 = resultados['proyecciones_ingresos']['general'][-1] / 1e6
            crecimiento_total = (ing_a5 / ing_a1 - 1) * 100
            
            st.metric(
                "Ingreso Año 1",
                f"${ing_a1:,.1f}M"
            )
            st.metric(
                "Ingreso Año 5",
                f"${ing_a5:,.1f}M",
                delta=f"{crecimiento_total:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    with main_tabs[2]:
        st.markdown('<h2 class="sub-header">Proyecciones Financieras Detalladas</h2>', unsafe_allow_html=True)
        
        # Selector de métrica
        metrica = st.selectbox(
            "Seleccionar métrica para visualizar",
            ["Ingresos Totales", "EBITDA", "EBIT", "FCF", "Capital de Trabajo", "Ingresos por Binomio"],
            key="metrica_selector"
        )
        
        if metrica == "Ingresos por Binomio":
            # Gráfico de ingresos por binomio
            fig = go.Figure()
            
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['proyecciones_ingresos']['binomio1']], 
                               name='Binomio 1', marker_color='#3B82F6'))
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['proyecciones_ingresos']['binomio2']], 
                               name='Binomio 2', marker_color='#10B981'))
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['proyecciones_ingresos']['general']], 
                               name='General', marker_color='#F59E0B'))
            
            fig.update_layout(
                barmode='stack',
                title='Ingresos por Binomio (Millones MXN)',
                height=500,
                xaxis_title="Año",
                yaxis_title="Millones MXN"
            )
            
        elif metrica == "Capital de Trabajo":
            # Gráfico de capital de trabajo
            fig = go.Figure()
            
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['capital_trabajo']['cuentas_por_cobrar']], 
                               name='Cuentas por Cobrar', marker_color='#3B82F6'))
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['capital_trabajo']['inventario']], 
                               name='Inventario', marker_color='#F59E0B'))
            fig.add_trace(go.Bar(x=años, y=[x/1e6 for x in resultados['capital_trabajo']['cuentas_por_pagar']], 
                               name='Cuentas por Pagar', marker_color='#EF4444'))
            
            fig.update_layout(
                barmode='group',
                title='Componentes del Capital de Trabajo (Millones MXN)',
                height=500,
                xaxis_title="Año",
                yaxis_title="Millones MXN"
            )
            
        else:
            # Datos según métrica seleccionada
            if metrica == "Ingresos Totales":
                datos = [x/1e6 for x in resultados['proyecciones_ingresos']['total']]
                titulo = "Ingresos Totales"
                color = '#10B981'
            elif metrica == "EBITDA":
                datos = [x/1e6 for x in resultados['ebitda']]
                titulo = "EBITDA"
                color = '#3B82F6'
            elif metrica == "EBIT":
                datos = [x/1e6 for x in resultados['ebit']]
                titulo = "EBIT"
                color = '#8B5CF6'
            else:  # FCF
                datos = [x/1e6 for x in resultados['fcf']]
                titulo = "Free Cash Flow"
                color = '#F59E0B'
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=años, y=datos,
                marker_color=color,
                name=titulo,
                text=[f"${x:,.1f}M" for x in datos],
                textposition='outside'
            ))
            
            fig.update_layout(
                title=f'{titulo} (Millones MXN)',
                height=500,
                showlegend=False,
                xaxis_title="Año",
                yaxis_title="Millones MXN"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de proyecciones completas
        st.markdown('<h3 class="sub-header">Tabla de Proyecciones Completas</h3>', unsafe_allow_html=True)
        
        df_proyecciones = pd.DataFrame({
            'Año': años,
            'Ingresos B1 (M$)': [x/1e6 for x in resultados['proyecciones_ingresos']['binomio1']],
            'Ingresos B2 (M$)': [x/1e6 for x in resultados['proyecciones_ingresos']['binomio2']],
            'Ingresos Gen (M$)': [x/1e6 for x in resultados['proyecciones_ingresos']['general']],
            'Ingresos Tot (M$)': [x/1e6 for x in resultados['proyecciones_ingresos']['total']],
            'EBITDA (M$)': [x/1e6 for x in resultados['ebitda']],
            'EBIT (M$)': [x/1e6 for x in resultados['ebit']],
            'FCF (M$)': [x/1e6 for x in resultados['fcf']]
        })
        
        st.dataframe(df_proyecciones.style.format({
            'Ingresos B1 (M$)': '${:,.1f}',
            'Ingresos B2 (M$)': '${:,.1f}',
            'Ingresos Gen (M$)': '${:,.1f}',
            'Ingresos Tot (M$)': '${:,.1f}',
            'EBITDA (M$)': '${:,.1f}',
            'EBIT (M$)': '${:,.1f}',
            'FCF (M$)': '${:,.1f}'
        }), use_container_width=True)
    
    with main_tabs[3]:
        st.markdown('<h2 class="sub-header">Análisis de Sensibilidad - Ke</h2>', unsafe_allow_html=True)
        
        sensibilidad = calculator.analisis_sensibilidad_ke(ke_min=0.08, ke_max=0.25, puntos=15)
        
        fig = go.Figure()
        
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

else:
    # Pantalla de bienvenida
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); 
                border-radius: 20px; color: white; margin: 2rem 0; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);'>
        <h1 style='font-size: 3rem; margin-bottom: 1rem;'>🚀 SIMULADOR DCF REACTIVO COMPLETO</h1>
        <p style='font-size: 1.3rem; opacity: 0.9;'>Control total sobre crecimientos por binomio y año</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ## 🎯 **Nuevas Funcionalidades:**
        
        ### **📈 Control de Crecimientos por Año**
        - **Binomio 1:** Ajuste crecimiento año 1-5
        - **Binomio 2:** Ajuste crecimiento año 1-5  
        - **General:** Ajuste crecimiento año 1-5
        - **Impacto inmediato** en proyecciones
        
        ### **📉 Control de Costos por Año**
        - Crecimientos ajustables por binomio
        - Impacto directo en márgenes
        - Proyecciones actualizadas en tiempo real
        
        ### **🏦 Variables Clave**
        - Ke ajustable (5% - 30%)
        - Días de capital de trabajo
        - WACC calculado automáticamente
        """)
    
    with col2:
        st.markdown("""
        ## 📊 **Ejemplo de Impacto:**
        
        ### **Aumentar crecimientos Binomio 1:**
        ```
        Año 1: 15% → 20% (+$625K ingresos)
        Año 2: 12% → 15% (+$450K ingresos)  
        Año 3: 10% → 12% (+$320K ingresos)
        Total impacto 5 años: +$2.5M ingresos
        ```
        
        ### **Optimizar capital trabajo:**
        ```
        CPC: 60 → 45 días (+$1.8M FCF)
        Inventario: 90 → 60 días (+$1.2M FCF)  
        CPP: 30 → 45 días (+$0.9M FCF)
        ```
        
        ## 🚀 **Cómo Empezar:**
        1. Cargue su plantilla Excel
        2. Ajuste crecimientos por binomio/año
        3. Modifique Ke y días capital trabajo
        4. Vea impacto en tiempo real
        5. Analice sensibilidad
        """)
    
    st.markdown("---")
    st.info("👈 **Suba su plantilla Excel en la barra lateral para comenzar**")

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**Metodología DCF Completa**")
    st.caption("Aswath Damodaran adaptado")
    st.caption("Para empresas mexicanas")

with footer_col2:
    st.markdown("**Control Total de Crecimientos**")
    st.caption("Por binomio y año")
    st.caption("Impacto en tiempo real")

with footer_col3:
    st.markdown("**© 2024 DCF Reactivo Pro**")
    st.caption("v4.0 - Control completo")
    st.caption("Todos los derechos reservados")