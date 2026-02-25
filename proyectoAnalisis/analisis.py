# Una universidad quiere analizar los datos de rendimiento académico de sus estudiantes para detectar:
# • Materias con mayor índice de reprobación
# • Carreras con mayor promedio
# • Tendencias por semestre
# • Posibles riesgos académicos
# Ustedes son el equipo directivo encargado de diseñar el análisis usando Python.

import pandas as pd
import unicodedata

def limpiar_texto(texto):
    if isinstance(texto, str):
        texto = "".join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        return texto.lower().strip()
    return texto

df = pd.read_csv('datos_rendimiento_universidad.csv')

df = df.drop_duplicates()
df['carrera'] = df['carrera'].apply(limpiar_texto)
df['materia'] = df['materia'].apply(limpiar_texto)

CAL_MINIMA = 6.0

print("="*50)
print("SISTEMA DE ANÁLISIS ACADÉMICO - RESULTADOS")
print("="*50)


df['reprobado'] = df['calificacion'] < CAL_MINIMA
reprobacion = df.groupby('materia')['reprobado'].mean() * 100
reprobacion = reprobacion.sort_values(ascending=False)



print("\n1. MATERIAS CON MAYOR ÍNDICE DE REPROBACIÓN (%):")
print(reprobacion.round(2).to_string(header=False))
promedio_carrera = df.groupby('carrera')['calificacion'].mean().sort_values(ascending=False)



print("\n2. CARRERAS CON MEJOR PROMEDIO GENERAL:")
print(promedio_carrera.round(2).to_string(header=False))
tendencia_semestre = df.groupby('semestre')['calificacion'].mean()



print("\n3. TENDENCIA DE CALIFICACIONES POR SEMESTRE:")
print(tendencia_semestre.round(2).to_string(header=False))
estudiantes_promedio = df.groupby('id_estudiante')['calificacion'].mean()
riesgos = estudiantes_promedio[estudiantes_promedio < CAL_MINIMA]




print("\n4. DETECCIÓN DE RIESGOS ACADÉMICOS:")
print(f"Total de estudiantes analizados: {df['id_estudiante'].nunique()}")
print(f"Estudiantes en situación de riesgo (Promedio < {CAL_MINIMA}): {len(riesgos)}")
if len(riesgos) > 0:
    print(f"IDs de algunos alumnos en riesgo: {list(riesgos.index[:10])}...")
    
