from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import unicodedata
from io import BytesIO
import base64

app = Flask(__name__)

def limpiar_texto(texto):
    if isinstance(texto, str):
        texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto.lower().strip()
    return texto

def procesar_datos(filtro_carrera=None, filtro_anio=None):
    df = pd.read_csv('datos_rendimiento_universidad.csv')
    df = df.drop_duplicates()
    df['carrera'] = df['carrera'].apply(limpiar_texto)
    df['materia'] = df['materia'].apply(limpiar_texto)
    
    # Aplicar Filtros
    if filtro_carrera and filtro_carrera != 'todas las carreras':
        df = df[df['carrera'] == filtro_carrera]
    if filtro_anio:
        df = df[df['año'] == int(filtro_anio)]

    CAL_MINIMA = 6.0
    df['reprobado'] = df['calificacion'] < CAL_MINIMA

    # 1. Materias con mayor reprobación
    reprobacion = df.groupby('materia')['reprobado'].mean() * 100
    reprobacion = reprobacion.sort_values(ascending=False).round(2)
    
    # 2. Carreras con mayor promedio
    promedio_carrera = df.groupby('carrera')['calificacion'].mean().sort_values(ascending=False).round(2)
    
    # 3. Tendencia por semestre
    tendencia_semestre = df.groupby('semestre')['calificacion'].mean().round(2)
    
    # 4. Riesgos
    estudiantes_promedio = df.groupby('id_estudiante')['calificacion'].mean()
    riesgos = estudiantes_promedio[estudiantes_promedio < CAL_MINIMA]
    
    # Tabla de riesgos con detalles
    df_riesgos = df[df['id_estudiante'].isin(riesgos.index)]
    tabla_riesgos = df_riesgos.groupby(['id_estudiante', 'carrera', 'materia'])['calificacion'].mean().reset_index()
    tabla_riesgos = tabla_riesgos[tabla_riesgos['calificacion'] < CAL_MINIMA].round(1).head(5)
    
    return {
        "kpis": {
            "avg_grade": round(df['calificacion'].mean(), 2),
            "fail_rate": round(df['reprobado'].mean() * 100, 1),
            "risk_count": len(riesgos),
            "total_students": df['id_estudiante'].nunique()
        },
        "reprobacion": reprobacion.to_dict(),
        "prom_carreras": promedio_carrera.to_dict(),
        "tendencia": tendencia_semestre.to_dict(),
        "tabla_riesgos": tabla_riesgos.to_dict(orient='records')
    }

def analisis_completo():
    df = pd.read_csv('datos_rendimiento_universidad.csv')
    df = df.drop_duplicates()
    df['carrera'] = df['carrera'].apply(limpiar_texto)
    df['materia'] = df['materia'].apply(limpiar_texto)
    
    CAL_MINIMA = 6.0
    df['reprobado'] = df['calificacion'] < CAL_MINIMA
    
    resultados = {}
    carreras = df['carrera'].unique()
    
    for carrera in carreras:
        df_carrera = df[df['carrera'] == carrera]
        
        # 1. Materias con mayor reprobación por carrera
        reprobacion = df_carrera.groupby('materia')['reprobado'].mean() * 100
        reprobacion = reprobacion.sort_values(ascending=False).round(2)
        
        # 2. Promedio general de la carrera
        promedio = df_carrera['calificacion'].mean().round(2)
        
        # 3. Tendencia por semestre de la carrera
        tendencia = df_carrera.groupby('semestre')['calificacion'].mean().round(2)
        
        # 4. Estudiantes en riesgo de la carrera
        estudiantes_promedio = df_carrera.groupby('id_estudiante')['calificacion'].mean()
        riesgos = estudiantes_promedio[estudiantes_promedio < CAL_MINIMA]
        
        # Porcentaje de estudiantes en riesgo
        total_estudiantes = df_carrera['id_estudiante'].nunique()
        porcentaje_riesgo = (len(riesgos) / total_estudiantes * 100).round(2) if total_estudiantes > 0 else 0
        
        resultados[carrera] = {
            "promedio_general": promedio,
            "total_estudiantes": total_estudiantes,
            "estudiantes_riesgo": len(riesgos),
            "porcentaje_riesgo": porcentaje_riesgo,
            "tasa_reprobacion": round(df_carrera['reprobado'].mean() * 100, 2),
            "materias_criticas": reprobacion.head(3).to_dict(),
            "tendencia_semestral": tendencia.to_dict()
        }
    
    return resultados

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    carrera = request.args.get('carrera')
    anio = request.args.get('anio')
    return jsonify(procesar_datos(carrera, anio))

@app.route('/api/print')
def print_data():
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
    
    return jsonify({"message": "Resultados impresos en la terminal"})

@app.route('/api/analisis-completo')
def get_analisis_completo():
    resultados = analisis_completo()
    
    print("\n" + "="*70)
    print("ANÁLISIS COMPLETO POR CARRERA")
    print("="*70)
    
    for carrera, datos in resultados.items():
        print(f"\n{'='*70}")
        print(f"CARRERA: {carrera.upper()}")
        print(f"{'='*70}")
        print(f"Promedio General: {datos['promedio_general']}")
        print(f"Total Estudiantes: {datos['total_estudiantes']}")
        print(f"Estudiantes en Riesgo: {datos['estudiantes_riesgo']} ({datos['porcentaje_riesgo']}%)")
        print(f"Tasa de Reprobación: {datos['tasa_reprobacion']}%")
        
        print(f"\nMaterias Críticas (Mayor Reprobación):")
        for materia, porcentaje in datos['materias_criticas'].items():
            print(f"  - {materia}: {porcentaje}%")
        
        print(f"\nTendencia por Semestre:")
        for semestre, promedio in datos['tendencia_semestral'].items():
            print(f"  - Semestre {semestre}: {promedio}")
    
    return jsonify(resultados)

@app.route('/api/export')
def export_data():
    carrera = request.args.get('carrera')
    anio = request.args.get('anio')
    formato = request.args.get('formato', 'csv')
    
    data = procesar_datos(carrera, anio)
    
    # Crear DataFrames con los resultados
    df_reprobacion = pd.DataFrame(list(data['reprobacion'].items()), columns=['Materia', 'Porcentaje_Reprobacion'])
    df_carreras = pd.DataFrame(list(data['prom_carreras'].items()), columns=['Carrera', 'Promedio'])
    df_tendencia = pd.DataFrame(list(data['tendencia'].items()), columns=['Semestre', 'Promedio'])
    df_riesgos = pd.DataFrame(data['tabla_riesgos'])
    
    output = BytesIO()
    filename = f"reporte_academico_{carrera if carrera and carrera != 'todas las carreras' else 'todos'}_{anio if anio else 'todos'}"
    
    if formato == 'csv':
        # Combinar todos los DataFrames en uno solo con separadores
        csv_content = "REPORTE ACADEMICO\n\n"
        csv_content += "MATERIAS CON MAYOR REPROBACION\n"
        csv_content += df_reprobacion.to_csv(index=False)
        csv_content += "\nCARRERAS CON MAYOR PROMEDIO\n"
        csv_content += df_carreras.to_csv(index=False)
        csv_content += "\nTENDENCIA POR SEMESTRE\n"
        csv_content += df_tendencia.to_csv(index=False)
        csv_content += "\nALUMNOS EN RIESGO\n"
        csv_content += df_riesgos.to_csv(index=False)
        
        output.write(csv_content.encode('utf-8-sig'))
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"{filename}.csv")
    
    elif formato == 'xlsx':
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_reprobacion.to_excel(writer, sheet_name='Reprobacion', index=False)
            df_carreras.to_excel(writer, sheet_name='Carreras', index=False)
            df_tendencia.to_excel(writer, sheet_name='Tendencia', index=False)
            df_riesgos.to_excel(writer, sheet_name='Riesgos', index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{filename}.xlsx")

@app.route('/api/export/pdf')
def export_pdf():
    return render_template('export.html')

if __name__ == '__main__':
    app.run(debug=True)