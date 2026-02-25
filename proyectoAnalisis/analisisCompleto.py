import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import unicodedata
import tkinter as tk
from tkinter import messagebox, ttk

# --- 1. LÓGICA DE DATOS (Concentrada en los 4 Puntos) ---
class AnalizadorAcademico:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.cal_minima = 6.0

    def _normalizar(self, texto):
        if isinstance(texto, str):
            texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
            return texto.title().strip()
        return texto

    def obtener_metricas(self):
        self.df = self.df.drop_duplicates()
        self.df['carrera'] = self.df['carrera'].apply(self._normalizar)
        self.df['materia'] = self.df['materia'].apply(self._normalizar)
        self.df['reprobado'] = self.df['calificacion'] < self.cal_minima

        # Punto 1: Reprobación
        m_repro = (self.df.groupby('materia')['reprobado'].mean() * 100).sort_values(ascending=False).reset_index()
        m_repro.columns = ['Materia', '% Reprobacion']

        # Punto 2: Promedios Carrera
        c_prom = self.df.groupby('carrera')['calificacion'].mean().sort_values(ascending=False).reset_index()
        c_prom.columns = ['Carrera', 'Promedio']

        # Punto 3: Tendencia Semestre
        s_tend = self.df.groupby('semestre')['calificacion'].mean().sort_index().reset_index()
        s_tend.columns = ['Semestre', 'Calificacion Promedio']

        # Punto 4: Riesgos (Alumnos con promedio < 6)
        est_proms = self.df.groupby('id_estudiante')['calificacion'].mean().reset_index()
        riesgos = est_proms[est_proms['calificacion'] < self.cal_minima].copy()
        riesgos.columns = ['ID Estudiante', 'Promedio General']

        return {
            "reprobacion": m_repro,
            "carreras": c_prom,
            "tendencia": s_tend,
            "riesgos": riesgos,
            "resumen": {
                "total": self.df['id_estudiante'].nunique(),
                "prom_gral": self.df['calificacion'].mean(),
                "num_riesgos": len(riesgos)
            }
        }

# --- 2. INTERFAZ RESPONSIVA Y SCROLLABLE ---
class AppConsolidada(tk.Tk):
    def __init__(self, analizador):
        super().__init__()
        self.analizador = analizador
        self.datos = self.analizador.obtener_metricas()
        
        self.title("Panel de Control Académico Universitario")
        self.geometry("1100x850")
        self.minsize(900, 700)
        self.configure(bg="#F0F2F5")

        self.setup_ui()

    def setup_ui(self):
        # Sidebar Fija
        sidebar = tk.Frame(self, bg="#DC6A00", width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="REPORTE UNIFICADO", fg="white", bg="#DC6A00", 
                 font=("Arial", 12, "bold"), pady=30).pack()

        # Botones
        estilo_btn = {"bg": "#283593", "fg": "white", "bd": 0, "pady": 12, "cursor": "hand2", "font": ("Arial", 10)}
        tk.Button(sidebar, text="Exportar Excel (Pestañas)", command=lambda: self.exportar("xlsx"), **estilo_btn).pack(fill=tk.X, padx=15, pady=5)
        tk.Button(sidebar, text="Exportar CSV (Unificado)", command=lambda: self.exportar("csv"), **estilo_btn).pack(fill=tk.X, padx=15, pady=5)
        tk.Button(sidebar, text="Exportar PDF (Visual)", command=lambda: self.exportar("pdf"), **estilo_btn).pack(fill=tk.X, padx=15, pady=5)

        # Contenedor Flexible con Scroll
        container = tk.Frame(self, bg="#F0F2F5")
        container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg="#F0F2F5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.scroll_frame = tk.Frame(self.canvas, bg="#F0F2F5")
        self.window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # Eventos para responsividad
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.renderizar_contenido()

    def on_canvas_resize(self, event):
        # Ajusta el ancho del contenido al ancho de la ventana automáticamente
        self.canvas.itemconfig(self.window_id, width=event.width)

    def crear_kpi(self, parent, titulo, valor, color, col):
        card = tk.Frame(parent, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#D1D8E0")
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        tk.Label(card, text=titulo, bg="white", fg="#7F8C8D", font=("Arial", 9, "bold")).pack()
        tk.Label(card, text=valor, bg="white", fg=color, font=("Arial", 18, "bold")).pack()

    def renderizar_contenido(self):
        # 1. KPIs
        kpi_frame = tk.Frame(self.scroll_frame, bg="#F0F2F5", pady=20)
        kpi_frame.pack(fill=tk.X, padx=40)
        kpi_frame.columnconfigure((0, 1, 2), weight=1)

        res = self.datos["resumen"]
        self.crear_kpi(kpi_frame, "ESTUDIANTES TOTALES", res["total"], "#2E86C1", 0)
        self.crear_kpi(kpi_frame, "PROMEDIO INSTITUCIONAL", f"{res['prom_gral']:.2f}", "#28B463", 1)
        self.crear_kpi(kpi_frame, "ALUMNOS EN RIESGO", res["num_riesgos"], "#CB4335", 2)

        # 2. Gráficas anchas y claras
        self.fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 18), constrained_layout=True)
        self.fig.patch.set_facecolor('#F0F2F5')

        # G1: Reprobación (Barras horizontales para lectura fácil)
        df1 = self.datos["reprobacion"].sort_values('% Reprobacion')
        ax1.barh(df1['Materia'], df1['% Reprobacion'], color="#E74C3C")
        ax1.set_title("1. MATERIAS CON MAYOR ÍNDICE DE REPROBACIÓN (%)", fontweight='bold')
        ax1.grid(axis='x', linestyle='--', alpha=0.5)

        # G2: Carreras
        df2 = self.datos["carreras"].sort_values('Promedio')
        ax2.barh(df2['Carrera'], df2['Promedio'], color="#3498DB")
        ax2.set_title("2. CARRERAS CON MAYOR PROMEDIO", fontweight='bold')
        ax2.set_xlim(0, 10)

        # G3: Tendencia
        ax3.plot(self.datos["tendencia"]['Semestre'], self.datos["tendencia"]['Calificacion Promedio'], 
                 marker='o', markersize=10, linewidth=3, color="#27AE60")
        ax3.set_title("3. TENDENCIA POR SEMESTRE", fontweight='bold')
        ax3.set_xticks(self.datos["tendencia"]['Semestre'])
        ax3.grid(True, alpha=0.3)

        canvas_plot = FigureCanvasTkAgg(self.fig, master=self.scroll_frame)
        canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

    def exportar(self, fmt):
        if not messagebox.askyesno("Confirmar", f"¿Desea exportar el reporte en formato {fmt.upper()}?"):
            return
        
        try:
            filename = f"Analisis_Rendimiento_Academico.{fmt}"
            
            if fmt == "csv":
                # EXPORTACIÓN UNIFICADA EN UN SOLO CSV
                with open(filename, "w", encoding='utf-8') as f:
                    f.write("--- REPORTE ACADEMICO CONSOLIDADO ---\n\n")
                    
                    f.write("PUNTO 1: MATERIAS CON MAYOR REPROBACION\n")
                    self.datos["reprobacion"].to_csv(f, index=False)
                    f.write("\n" + "="*40 + "\n\n")
                    
                    f.write("PUNTO 2: CARRERAS CON MEJOR PROMEDIO\n")
                    self.datos["carreras"].to_csv(f, index=False)
                    f.write("\n" + "="*40 + "\n\n")
                    
                    f.write("PUNTO 3: TENDENCIAS POR SEMESTRE\n")
                    self.datos["tendencia"].to_csv(f, index=False)
                    f.write("\n" + "="*40 + "\n\n")
                    
                    f.write("PUNTO 4: ESTUDIANTES EN RIESGO (Promedio < 6.0)\n")
                    self.datos["riesgos"].to_csv(f, index=False)
                
                messagebox.showinfo("Éxito", "CSV Unificado generado con las 4 tablas.")

            elif fmt == "xlsx":
                with pd.ExcelWriter(filename) as writer:
                    self.datos["reprobacion"].to_excel(writer, sheet_name="1_Reprobacion", index=False)
                    self.datos["carreras"].to_excel(writer, sheet_name="2_Promedios", index=False)
                    self.datos["tendencia"].to_excel(writer, sheet_name="3_Tendencia", index=False)
                    self.datos["riesgos"].to_excel(writer, sheet_name="4_Riesgos", index=False)
                messagebox.showinfo("Éxito", "Excel generado con 4 pestañas.")

            elif fmt == "pdf":
                self.fig.savefig(filename, bbox_inches='tight')
                messagebox.showinfo("Éxito", "Reporte gráfico PDF exportado.")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

if __name__ == "__main__":
    analizador = AnalizadorAcademico('datos_rendimiento_universidad.csv')
    app = AppConsolidada(analizador)
    app.mainloop()