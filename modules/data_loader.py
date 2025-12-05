# modules/data_loader.py
import pandas as pd
import numpy as np

class ExcelDataLoader:
    def __init__(self):
        self.data_frames = {}
        self.metadata = {}
    
    def load_excel(self, uploaded_file):
        """Carga el archivo Excel"""
        try:
            xls = pd.ExcelFile(uploaded_file)
            self.metadata['sheet_names'] = xls.sheet_names
            self.metadata['file_name'] = uploaded_file.name
            
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                self.data_frames[sheet_name] = df
            
            # Extraer datos básicos
            self._extraer_datos_basicos()
            return True, "✅ Archivo cargado exitosamente"
            
        except Exception as e:
            return False, f"❌ Error al cargar: {str(e)}"
    
    def _extraer_datos_basicos(self):
        """Extrae datos básicos del Excel"""
        # Por ahora, usamos valores por defecto
        # En una versión completa, extraeríamos del Excel real
        self.metadata['datos_base'] = {
            'efectivo': 5000000,
            'deuda_total': 12000000,
            'capital_trabajo_base': 10000000
        }
    
    def get_summary(self):
        """Retorna un resumen"""
        return {
            'empresa': self.metadata.get('file_name', 'Desconocida'),
            'hojas_cargadas': len(self.data_frames)
        }