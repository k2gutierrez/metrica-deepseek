# modules/dcf_calculator.py
import numpy as np

class DCFCalculator:
    def __init__(self, datos_base, parametros):
        self.datos_base = datos_base
        self.parametros = parametros
        self.resultados = {}
    
    def calcular_proyecciones(self):
        """Calcula todas las proyecciones (versión simplificada)"""
        años = 5
        
        # Proyecciones de ingresos
        ingresos = self._proyectar_ingresos()
        
        # Proyecciones de costos
        costos = self._proyectar_costos(ingresos)
        
        # Calcular EBIT
        ebit = []
        for i in range(años):
            margen_bruto = ingresos['total'][i] - costos['total'][i]
            gastos_op = 6000000 * (1.03 ** i)  # Gastos crecientes 3% anual
            ebit_i = margen_bruto - gastos_op
            ebit.append(ebit_i)
        
        # Calcular FCF
        fcf = []
        for i in range(años):
            nopat = ebit[i] * (1 - self.parametros['tax_rate'])
            depreciacion = 1200000
            amortizacion = 450000
            capex = 925000
            delta_ct = 100000 * (1.05 ** i)  # Delta creciente
            fcf_i = nopat + depreciacion + amortizacion - capex - delta_ct
            fcf.append(fcf_i)
        
        # Calcular WACC
        wacc = self._calcular_wacc()
        
        # Calcular valor terminal
        crecimiento_perpetuo = self.parametros['crecimiento_perpetuo']
        valor_terminal = (fcf[-1] * (1 + crecimiento_perpetuo)) / (wacc - crecimiento_perpetuo)
        
        # Calcular Enterprise Value
        enterprise_value = self._calcular_enterprise_value(fcf, valor_terminal, wacc)
        
        # Calcular Equity Value
        equity_value = self._calcular_equity_value(enterprise_value)
        
        self.resultados = {
            'proyecciones_ingresos': ingresos,
            'proyecciones_costos': costos,
            'ebit': ebit,
            'fcf': fcf,
            'wacc': wacc,
            'valor_terminal': valor_terminal,
            'enterprise_value': enterprise_value,
            'equity_value': equity_value
        }
        
        return self.resultados
    
    def _proyectar_ingresos(self):
        """Proyecciones simplificadas"""
        años = 5
        base = 25000000  # 25M base
        
        ingresos = {'total': []}
        for i in range(años):
            crecimiento = 0.10  # 10% anual
            ingresos['total'].append(base * (1 + crecimiento) ** (i+1))
        
        return ingresos
    
    def _proyectar_costos(self, ingresos):
        """Costos simplificados"""
        años = 5
        costos = {'total': []}
        
        for i in range(años):
            # Costos = 60% de ingresos
            costos['total'].append(ingresos['total'][i] * 0.60)
        
        return costos
    
    def _calcular_wacc(self):
        """WACC simplificado"""
        ke = self.parametros['ke']
        kd = 0.12
        tax_rate = self.parametros['tax_rate']
        d_v = self.parametros['proporcion_deuda']
        e_v = self.parametros['proporcion_patrimonio']
        
        return (e_v * ke) + (d_v * kd * (1 - tax_rate))
    
    def _calcular_enterprise_value(self, fcf, valor_terminal, wacc):
        """Enterprise Value simplificado"""
        pv_fcf = 0
        for i, fcf_i in enumerate(fcf):
            pv_fcf += fcf_i / ((1 + wacc) ** (i + 1))
        
        pv_terminal = valor_terminal / ((1 + wacc) ** len(fcf))
        return pv_fcf + pv_terminal
    
    def _calcular_equity_value(self, enterprise_value):
        """Equity Value simplificado"""
        efectivo = self.datos_base.get('efectivo', 5000000)
        deuda_total = self.datos_base.get('deuda_total', 12000000)
        
        deuda_neta = deuda_total - efectivo
        equity_value = enterprise_value - deuda_neta
        
        return max(equity_value, 0)