import pandas as pd
import os

# Crear datos simples de ejemplo
def crear_plantilla_simple():
    """Crea una plantilla simple pero funcional"""
    
    # 1. Balance Base
    balance = pd.DataFrame({
        'CODIGO': ['AC01', 'AC02', 'AC03', 'AC04', 'ANC01', 'ANC02', 'PC01', 'PC02', 'PNC01', 'PAT01', 'PAT02'],
        'DESCRIPCION': ['Efectivo', 'Cuentas por Cobrar', 'Inventarios', 'Otros Activos',
                       'Propiedad Planta Equipo', 'Intangibles', 'Cuentas por Pagar',
                       'Deuda Corto Plazo', 'Deuda Largo Plazo', 'Capital Social', 'Utilidades Retenidas'],
        'AÑO_0_MXN': [5000000, 3200000, 2800000, 800000, 18500000, 6500000,
                      2100000, 3500000, 8500000, 12000000, 7800000]
    })
    
    # 2. Estado de Resultados
    estado = pd.DataFrame({
        'CONCEPTO': ['INGRESOS BINOMIO 1', 'COSTOS BINOMIO 1', 'INGRESOS BINOMIO 2', 
                    'COSTOS BINOMIO 2', 'INGRESOS GENERAL', 'COSTOS GENERAL',
                    'GASTOS ADMINISTRATIVOS', 'DEPRECIACION', 'AMORTIZACION',
                    'INTERESES', 'UTILIDAD NETA'],
        'AÑO_1': [12500000, 5000000, 8500000, 4250000, 4000000, 2400000,
                  2800000, 1200000, 450000, 1420000, 2820000],
        'AÑO_2': [14375000, 5750000, 9775000, 4887500, 4320000, 2592000,
                  2884000, 1200000, 450000, 1349000, 3244000],
        'AÑO_3': [16100000, 6440000, 10742500, 5371250, 4579200, 2747520,
                  2970520, 1200000, 450000, 1281550, 3653920],
        'AÑO_4': [17600000, 7040000, 11594700, 5797350, 4808160, 2884896,
                  3059636, 1200000, 450000, 1217473, 4034455],
        'AÑO_5': [18980000, 7592000, 12314280, 6157140, 5000486, 3000292,
                  3151425, 1200000, 450000, 1156600, 4380159]
    })
    
    # 3. Capital de Trabajo
    capital = pd.DataFrame({
        'PARAMETRO': ['DIAS_CUENTAS_POR_COBRAR', 'DIAS_INVENTARIO', 'DIAS_CUENTAS_POR_PAGAR',
                      'VENTAS_ANUAL', 'COSTOS_ANUAL', 'NECESIDAD_CPC', 'NECESIDAD_INV',
                      'NECESIDAD_CPP', 'CAPITAL_TRABAJO_NETO', 'DELTA_CAPITAL_TRABAJO'],
        'AÑO_1': [45, 60, 30, 25000000, 11650000, 3082192, 1915068, 957534, 4039726, 4039726],
        'AÑO_2': [45, 60, 30, 28470000, 13229500, 3509589, 2174823, 1087411, 4597001, 557275],
        'AÑO_3': [45, 60, 30, 31421700, 14568770, 3873612, 2394866, 1197433, 5071045, 474044],
        'AÑO_4': [45, 60, 30, 34002860, 15722246, 4192068, 2584575, 1292287, 5484356, 413311],
        'AÑO_5': [45, 60, 30, 36294766, 16749432, 4475640, 2751950, 1375975, 5851615, 367259]
    })
    
    # 4. Financiamiento
    financiamiento = pd.DataFrame({
        'CONCEPTO': ['TASA_LIBRE_RIESGO', 'PRIMA_RIESGO_MERCADO', 'BETA', 
                    'COSTO_DEUDA_ANTES_IMP', 'TASA_IMPOSITIVA', 'PROPORCION_DEUDA',
                    'PROPORCION_PATRIMONIO', 'WACC', 'CRECIMIENTO_PERPETUO'],
        'VALOR': [0.075, 0.065, 1.20, 0.12, 0.30, 0.35, 0.65, 0.1245, 0.02]
    })
    
    # 5. Flujos FCF
    flujos = pd.DataFrame({
        'CONCEPTO': ['EBIT', 'IMPUESTOS', 'NOPAT', 'DEPRECIACION_AMORTIZACION',
                    'CAPEX', 'DELTA_CAPITAL_TRABAJO', 'FCF', 'FCF_DESCONTADO'],
        'AÑO_1': [6060000, 1818000, 4242000, 1650000, 925000, 4039726, -970726, -866720],
        'AÑO_2': [6921000, 2076300, 4844700, 1650000, 925000, 557275, 4994425, 3982321],
        'AÑO_3': [7639900, 2291970, 5347930, 1650000, 925000, 474044, 5602886, 3982321],
        'AÑO_4': [8223268, 2466980, 5756288, 1650000, 925000, 413311, 6065977, 3837603],
        'AÑO_5': [8691768, 2607530, 6084238, 1650000, 925000, 367259, 6443979, 3617653]
    })
    
    # Guardar en Excel
    with pd.ExcelWriter('Plantilla_Valuacion_Simple.xlsx', engine='openpyxl') as writer:
        balance.to_excel(writer, sheet_name='Balance_Base', index=False)
        estado.to_excel(writer, sheet_name='Estado_Resultados', index=False)
        capital.to_excel(writer, sheet_name='Capital_Trabajo', index=False)
        financiamiento.to_excel(writer, sheet_name='Financiamiento', index=False)
        flujos.to_excel(writer, sheet_name='Flujos_FCF', index=False)
    
    print("✅ Archivo simple creado: Plantilla_Valuacion_Simple.xlsx")
    print("📏 Tamaño:", os.path.getsize('Plantilla_Valuacion_Simple.xlsx'), "bytes")

# Ejecutar
crear_plantilla_simple()