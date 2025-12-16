import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

# Tipos de archivo
EXTENSIONS = {
    "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Comprimidos": [".zip", ".rar", ".tar", ".gz"],
    "Otros": []
}

def organizar_archivos(carpeta):
    for archivo in os.listdir(carpeta):
        ruta_archivo = os.path.join(carpeta, archivo)
        if os.path.isfile(ruta_archivo):
            movido = False
            for categoria, extensiones in EXTENSIONS.items():
                if any(archivo.lower().endswith(ext) for ext in extensiones):
                    carpeta_tipo = os.path.join(carpeta, categoria)
                    os.makedirs(carpeta_tipo, exist_ok=True)
                    fecha = datetime.fromtimestamp(os.path.getmtime(ruta_archivo))
                    carpeta_fecha = os.path.join(carpeta_tipo, str(fecha.year), f"{fecha.month:02}")
                    os.makedirs(carpeta_fecha, exist_ok=True)
                    shutil.move(ruta_archivo, os.path.join(carpeta_fecha, archivo))
                    movido = True
                    break
            if not movido:
                carpeta_destino = os.path.join(carpeta, "Otros")
                os.makedirs(carpeta_destino, exist_ok=True)
                shutil.move(ruta_archivo, os.path.join(carpeta_destino, archivo))

def seleccionar_carpeta():
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta a organizar")
    if carpeta:
        organizar_archivos(carpeta)
        messagebox.showinfo("¡Hecho!", f"Archivos organizados en:\n{carpeta}")

# GUI mínima
root = tk.Tk()
root.title("Organizador de Carpetas")
root.geometry("400x150")

tk.Label(root, text="Organizador automático de carpetas", font=("Helvetica", 14)).pack(pady=20)
tk.Button(root, text="Seleccionar carpeta y organizar", command=seleccionar_carpeta, bg="#4CAF50", fg="white", font=("Helvetica", 12)).pack(pady=10)

root.mainloop()

