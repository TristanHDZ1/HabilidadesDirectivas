import pandas as pd
import unicodedata

class AnalizadorAcademico:
    def __init__(self, archivo):
        self.df = pd.read_csv(archivo)
        self.cal_minima = 6.0
        self._preprocesar()

    def _limpiar_texto(self, texto):
        if isinstance(texto, str):
            texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
            return texto.lower().strip()
        return texto

    def _preprocesar(self):
        self.df = self.df.drop_duplicates()
        self.df['carrera'] = self.df['carrera'].apply(self._limpiar_texto)
        self.df['materia'] = self.df['materia'].apply(self._limpiar_texto)
        self.df['reprobado'] = self.df['calificacion'] < self.cal_minima

    def obtener_analisis(self):
        # Punto 1: Reprobación
        repro = (self.df.groupby('materia')['reprobado'].mean() * 100).round(2).sort_values(ascending=False).to_dict()
        
        # Punto 2: Promedio Carreras
        prom_carr = self.df.groupby('carrera')['calificacion'].mean().round(2).sort_values(ascending=False).to_dict()
        
        # Punto 3: Tendencia Semestre
        tendencia = self.df.groupby('semestre')['calificacion'].mean().round(2).to_dict()
        
        # Punto 4: Riesgos
        est_prom = self.df.groupby('id_estudiante')['calificacion'].mean()
        riesgos = est_prom[est_prom < self.cal_minima].index.tolist()
        
        return {
            "reprobacion": repro,
            "promedios_carrera": prom_carr,
            "tendencia_semestre": tendencia,
            "estudiantes_riesgo": riesgos,
            "total_estudiantes": self.df['id_estudiante'].nunique()
        }