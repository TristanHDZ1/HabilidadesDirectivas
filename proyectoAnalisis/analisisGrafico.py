import pandas as pd
import matplotlib.pyplot as plt
import unicodedata

class AnalizadorAcademico:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.cal_minima = 6.0

    def _limpiar_texto(self, texto):
        if isinstance(texto, str):
            texto = "".join(
                c for c in unicodedata.normalize('NFD', texto)
                if unicodedata.category(c) != 'Mn'
            )
            return texto.lower().strip()
        return texto

    def normalizar_datos(self):
        self.df = self.df.drop_duplicates()
        self.df['carrera'] = self.df['carrera'].apply(self._limpiar_texto)
        self.df['materia'] = self.df['materia'].apply(self._limpiar_texto)
        return self.df

    def analizar_reprobacion(self):
        self.df['reprobado'] = self.df['calificacion'] < self.cal_minima
        return (self.df.groupby('materia')['reprobado'].mean() * 100).sort_values(ascending=False)

    def analizar_promedios_carrera(self):
        return self.df.groupby('carrera')['calificacion'].mean().sort_values(ascending=False)

    def analizar_tendencia_semestre(self):
        return self.df.groupby('semestre')['calificacion'].mean()

    def detectar_riesgos(self):
        estudiantes_promedio = self.df.groupby('id_estudiante')['calificacion'].mean()
        return estudiantes_promedio[estudiantes_promedio < self.cal_minima]


class VisualizadorAcademico:
    def __init__(self):
        plt.style.use('ggplot')

    def graficar_reprobacion(self, data):
        data.plot(kind='bar', color='salmon', figsize=(8, 5))
        plt.title('Índice de Reprobación por Materia (%)')
        plt.ylabel('Porcentaje')
        plt.xlabel('Materia')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def graficar_promedios(self, data):
        data.plot(kind='barh', color='skyblue', figsize=(8, 5))
        plt.title('Promedio General por Carrera')
        plt.xlabel('Calificación')
        plt.ylabel('Carrera')
        plt.tight_layout()
        plt.show()

    def graficar_tendencia(self, data):
        data.plot(kind='line', marker='o', color='green', figsize=(8, 5))
        plt.title('Tendencia de Calificaciones por Semestre')
        plt.ylabel('Promedio')
        plt.xlabel('Semestre')
        plt.grid(True)
        plt.tight_layout()
        plt.show()



if __name__ == "__main__":
    archivo = 'datos_rendimiento_universidad.csv'
    
    # 1. Instanciar el analizador y procesar
    analizador = AnalizadorAcademico(archivo)
    analizador.normalizar_datos()

    # 2. Obtener resultados del análisis
    reprobacion = analizador.analizar_reprobacion()
    promedios = analizador.analizar_promedios_carrera()
    tendencia = analizador.analizar_tendencia_semestre()
    riesgos = analizador.detectar_riesgos()

    # 3. Mostrar resultados en consola
    print("="*50)
    print("SISTEMA DE ANÁLISIS ACADÉMICO - RESULTADOS")
    print("="*50)
    print("\n1. MATERIAS CON MAYOR ÍNDICE DE REPROBACIÓN (%):")
    print(reprobacion.round(2).to_string(header=False))
    print("\n2. CARRERAS CON MEJOR PROMEDIO GENERAL:")
    print(promedios.round(2).to_string(header=False))
    print("\n3. TENDENCIA DE CALIFICACIONES POR SEMESTRE:")
    print(tendencia.round(2).to_string(header=False))
    print("\n4. DETECCIÓN DE RIESGOS ACADÉMICOS:")
    print(f"Total de estudiantes en riesgo: {len(riesgos)}")

    # 4. Generar la parte visual
    visualizador = VisualizadorAcademico()
    visualizador.graficar_reprobacion(reprobacion)
    visualizador.graficar_promedios(promedios)
    visualizador.graficar_tendencia(tendencia)