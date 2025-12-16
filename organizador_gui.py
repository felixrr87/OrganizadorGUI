#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORGANIZADOR AUTOMÁTICO DE CARPETAS - VERSIÓN PROFESIONAL
Versión: 2.0
Autor: Sistema de Organización Digital
"""

import os
import shutil
import json
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import platform
import subprocess
import webbrowser
from typing import Dict, List, Optional, Tuple
import traceback

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

class Configuracion:
    """Maneja la configuración del organizador"""
    
    @staticmethod
    def obtener_ruta_config():
        """Obtiene la ruta del archivo de configuración según el sistema operativo"""
        sistema = platform.system()
        
        if sistema == "Windows":
            config_dir = os.path.join(os.getenv('APPDATA'), 'OrganizadorAutomatico')
        elif sistema == "Darwin":  # macOS
            config_dir = os.path.expanduser("~/Library/Application Support/OrganizadorAutomatico")
        else:  # Linux y otros
            config_dir = os.path.expanduser("~/.config/organizadorautomatico")
        
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'config.json')
    
    @staticmethod
    def cargar():
        """Carga la configuración desde archivo o crea una por defecto"""
        config_file = Configuracion.obtener_ruta_config()
        
        config_default = {
            "version": "2.0",
            "ultima_actualizacion": datetime.now().isoformat(),
            "extensiones": {
                "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"],
                "Documentos": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub", ".mobi"],
                "Hojas de cálculo": [".xls", ".xlsx", ".csv", ".ods", ".xlsm", ".xlsb"],
                "Presentaciones": [".ppt", ".pptx", ".odp", ".key"],
                "Videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".m4v", ".webm"],
                "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".midi"],
                "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
                "Ejecutables": [".exe", ".msi", ".dmg", ".app", ".sh", ".bat", ".cmd", ".apk"],
                "Código": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php", ".json", ".xml", ".yml", ".yaml"],
                "Diseño": [".psd", ".ai", ".xd", ".sketch", ".fig", ".eps", ".indd"],
                "Sistema": [".dll", ".sys", ".ini", ".cfg", ".log", ".bak"],
                "Fuentes": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
                "Base de datos": [".db", ".sqlite", ".mdb", ".accdb", ".sql"],
                "Virtualización": [".iso", ".vhd", ".vmdk", ".ova", ".ovf"],
                "Otros": []
            },
            "configuracion": {
                "organizar_por_tipo": True,
                "organizar_por_fecha": True,
                "formato_fecha": "YYYY-MM",  # Opciones: YYYY-MM, YYYY/MM, AAAA/MM/DD
                "organizar_por_proyecto": False,
                "mover_archivos": True,
                "crear_subcarpetas": True,
                "ignorar_ocultos": True,
                "ignorar_sistemas": True,
                "tamaño_maximo_mb": 500,
                "modo_seguro": False,
                "mantener_estructura_original": False,
                "notificaciones": True,
                "sonido_exito": True
            },
            "carpetas_favoritas": [],
            "historial": [],
            "estadisticas": {
                "total_archivos": 0,
                "archivos_organizados": 0,
                "carpetas_creadas": 0,
                "ultima_organizacion": None
            },
            "preferencias_interfaz": {
                "tema": "claro",  # claro, oscuro, sistema
                "idioma": "es",
                "mostrar_avanzadas": False,
                "tamaño_fuente": 11
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Actualizar si hay nuevas configuraciones
                for key, value in config_default.items():
                    if key not in config:
                        config[key] = value
                
                return config
            else:
                return config_default
                
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return config_default
    
    @staticmethod
    def guardar(config):
        """Guarda la configuración en archivo"""
        try:
            config_file = Configuracion.obtener_ruta_config()
            config["ultima_actualizacion"] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False

# ============================================================================
# NÚCLEO DEL ORGANIZADOR
# ============================================================================

class OrganizadorAutomatico:
    """Clase principal que maneja la organización de archivos"""
    
    def __init__(self, config=None):
        self.config = config or Configuracion.cargar()
        self.estadisticas = {
            "archivos_procesados": 0,
            "archivos_movidos": 0,
            "archivos_omitidos": 0,
            "carpetas_creadas": 0,
            "errores": 0,
            "espacio_liberado": 0
        }
        self.archivos_conflictivos = []
        self.en_ejecucion = False
        
    def obtener_categoria(self, extension: str) -> str:
        """Determina la categoría basada en la extensión del archivo"""
        extension = extension.lower()
        
        for categoria, extensiones in self.config["extensiones"].items():
            if extension in extensiones:
                return categoria
        
        return "Otros"
    
    def generar_nombre_unico(self, ruta_destino: Path) -> Path:
        """Genera un nombre único si el archivo ya existe"""
        if not ruta_destino.exists():
            return ruta_destino
        
        contador = 1
        nombre_base = ruta_destino.stem
        extension = ruta_destino.suffix
        directorio = ruta_destino.parent
        
        while True:
            nuevo_nombre = directorio / f"{nombre_base} ({contador}){extension}"
            if not nuevo_nombre.exists():
                return nuevo_nombre
            contador += 1
    
    def crear_estructura_carpetas(self, ruta_base: Path, categorias: List[str]) -> Path:
        """Crea la estructura de carpetas según las reglas"""
        ruta_actual = ruta_base
        
        # 1. Por categoría
        if self.config["configuracion"]["organizar_por_tipo"]:
            ruta_actual = ruta_actual / categorias[0]
        
        # 2. Por fecha
        if self.config["configuracion"]["organizar_por_fecha"] and len(categorias) > 1:
            formato = self.config["configuracion"]["formato_fecha"]
            fecha_str = categorias[1]
            
            if formato == "YYYY/MM":
                ruta_actual = ruta_actual / fecha_str[:4] / fecha_str[5:7]
            elif formato == "AAAA/MM/DD":
                partes = fecha_str.split('-')
                ruta_actual = ruta_actual / partes[0] / partes[1] / partes[2]
            else:  # YYYY-MM
                ruta_actual = ruta_actual / fecha_str
        
        # 3. Por proyecto (si está activado y hay información)
        if (self.config["configuracion"]["organizar_por_proyecto"] and 
            len(categorias) > 2 and categorias[2]):
            ruta_actual = ruta_actual / categorias[2]
        
        # Crear la carpeta si no existe
        ruta_actual.mkdir(parents=True, exist_ok=True)
        self.estadisticas["carpetas_creadas"] += 1
        
        return ruta_actual
    
    def procesar_archivo(self, archivo_path: Path, carpeta_destino: Path = None) -> Tuple[bool, str]:
        """Procesa un archivo individual"""
        try:
            # Verificar si el archivo debe ser ignorado
            if self.debe_ignorar(archivo_path):
                self.estadisticas["archivos_omitidos"] += 1
                return False, "ignorado"
            
            # Obtener información del archivo
            stat_info = archivo_path.stat()
            fecha_modificacion = datetime.fromtimestamp(stat_info.st_mtime)
            tamaño = stat_info.st_size
            
            # Verificar tamaño máximo
            tamaño_mb = tamaño / (1024 * 1024)
            if tamaño_mb > self.config["configuracion"]["tamaño_maximo_mb"]:
                self.estadisticas["archivos_omitidos"] += 1
                return False, "tamaño_excedido"
            
            # Determinar categoría
            categoria = self.obtener_categoria(archivo_path.suffix)
            
            # Preparar categorías para estructura
            categorias = [categoria]
            
            # Agregar fecha según formato
            if self.config["configuracion"]["organizar_por_fecha"]:
                formato = self.config["configuracion"]["formato_fecha"]
                if formato == "YYYY/MM":
                    fecha_str = fecha_modificacion.strftime("%Y/%m")
                elif formato == "AAAA/MM/DD":
                    fecha_str = fecha_modificacion.strftime("%Y-%m-%d")
                else:  # YYYY-MM
                    fecha_str = fecha_modificacion.strftime("%Y-%m")
                categorias.append(fecha_str)
            
            # Agregar proyecto si está activado
            if self.config["configuracion"]["organizar_por_proyecto"]:
                proyecto = self.detectar_proyecto(archivo_path)
                categorias.append(proyecto or "Sin Proyecto")
            
            # Determinar carpeta de destino
            if carpeta_destino is None:
                if self.config["configuracion"]["mantener_estructura_original"]:
                    carpeta_destino = archivo_path.parent / "Organizados"
                else:
                    carpeta_destino = archivo_path.parent
            
            # Crear estructura y obtener ruta final
            carpeta_final = self.crear_estructura_carpetas(carpeta_destino, categorias)
            ruta_destino = carpeta_final / archivo_path.name
            
            # Verificar si ya existe y generar nombre único si es necesario
            if ruta_destino.exists():
                if self.config["configuracion"]["modo_seguro"]:
                    self.archivos_conflictivos.append(str(archivo_path))
                    return False, "conflicto"
                else:
                    ruta_destino = self.generar_nombre_unico(ruta_destino)
            
            # Mover o copiar el archivo
            if self.config["configuracion"]["mover_archivos"]:
                shutil.move(str(archivo_path), str(ruta_destino))
                accion = "movido"
            else:
                shutil.copy2(str(archivo_path), str(ruta_destino))
                accion = "copiado"
            
            # Actualizar estadísticas
            self.estadisticas["archivos_procesados"] += 1
            self.estadisticas["archivos_movidos"] += 1
            self.estadisticas["espacio_liberado"] += tamaño
            
            return True, accion
            
        except PermissionError:
            self.estadisticas["errores"] += 1
            return False, "permiso_denegado"
        except Exception as e:
            self.estadisticas["errores"] += 1
            print(f"Error procesando {archivo_path}: {e}")
            traceback.print_exc()
            return False, "error"
    
    def debe_ignorar(self, archivo_path: Path) -> bool:
        """Determina si un archivo debe ser ignorado"""
        nombre = archivo_path.name
        
        # Ignorar archivos ocultos
        if self.config["configuracion"]["ignorar_ocultos"] and nombre.startswith('.'):
            return True
        
        # Ignorar archivos de sistema
        if self.config["configuracion"]["ignorar_sistemas"]:
            archivos_sistema = ["desktop.ini", ".DS_Store", "Thumbs.db", 
                               ".localized", ".Spotlight-V100", ".fseventsd"]
            if nombre in archivos_sistema:
                return True
        
        # Ignorar extensiones temporales
        extensiones_temp = [".tmp", ".temp", ".crdownload", ".part", ".download"]
        if archivo_path.suffix.lower() in extensiones_temp:
            return True
        
        return False
    
    def detectar_proyecto(self, archivo_path: Path) -> Optional[str]:
        """Intenta detectar el proyecto basado en archivos comunes"""
        # Archivos que indican un proyecto
        indicadores = [
            "package.json", "requirements.txt", "pom.xml", "build.gradle",
            "Cargo.toml", "composer.json", ".git", ".gitignore", ".svn",
            "README.md", "Makefile", "CMakeLists.txt", "Dockerfile",
            "docker-compose.yml", "pyproject.toml", "setup.py",
            "index.html", "manifest.json", "pubspec.yaml"
        ]
        
        # Buscar en el directorio actual y padres
        for directorio in [archivo_path.parent] + list(archivo_path.parents):
            for indicador in indicadores:
                if (directorio / indicador).exists():
                    return directorio.name
        
        # Buscar por palabras clave en el nombre del archivo
        palabras_clave = ["proyecto", "project", "trabajo", "work", "cliente", "client"]
        nombre_archivo = archivo_path.stem.lower()
        
        for palabra in palabras_clave:
            if palabra in nombre_archivo:
                return palabra.capitalize()
        
        return None
    
    def organizar_carpeta(self, carpeta_path: str, callback_progreso=None) -> Dict:
        """Organiza todos los archivos en una carpeta"""
        if self.en_ejecucion:
            return {"error": "Ya hay una operación en curso"}
        
        self.en_ejecucion = True
        self.estadisticas = {
            "archivos_procesados": 0,
            "archivos_movidos": 0,
            "archivos_omitidos": 0,
            "carpetas_creadas": 0,
            "errores": 0,
            "espacio_liberado": 0
        }
        self.archivos_conflictivos = []
        
        try:
            carpeta = Path(carpeta_path)
            if not carpeta.exists() or not carpeta.is_dir():
                return {"error": "Carpeta no válida"}
            
            # Recopilar todos los archivos
            archivos = []
            for item in carpeta.rglob('*'):
                if item.is_file():
                    archivos.append(item)
            
            total_archivos = len(archivos)
            
            # Procesar archivos
            for i, archivo in enumerate(archivos):
                if not self.en_ejecucion:
                    break
                    
                exito, mensaje = self.procesar_archivo(archivo, carpeta / "Organizados")
                
                # Llamar al callback de progreso si existe
                if callback_progreso:
                    progreso = (i + 1) / total_archivos * 100
                    callback_progreso(progreso, f"Procesando: {archivo.name}")
            
            # Actualizar configuración
            self.config["estadisticas"]["total_archivos"] += self.estadisticas["archivos_procesados"]
            self.config["estadisticas"]["archivos_organizados"] += self.estadisticas["archivos_movidos"]
            self.config["estadisticas"]["carpetas_creadas"] += self.estadisticas["carpetas_creadas"]
            self.config["estadisticas"]["ultima_organizacion"] = datetime.now().isoformat()
            
            # Agregar al historial
            self.config["historial"].append({
                "fecha": datetime.now().isoformat(),
                "carpeta": carpeta_path,
                "estadisticas": self.estadisticas.copy(),
                "archivos_conflictivos": self.archivos_conflictivos.copy()
            })
            
            # Guardar configuración
            Configuracion.guardar(self.config)
            
            return {
                "exito": True,
                "estadisticas": self.estadisticas,
                "archivos_conflictivos": self.archivos_conflictivos,
                "carpeta_organizada": carpeta_path
            }
            
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}
        finally:
            self.en_ejecucion = False
    
    def cancelar_organizacion(self):
        """Cancela la operación en curso"""
        self.en_ejecucion = False

# ============================================================================
# INTERFAZ GRÁFICA MEJORADA
# ============================================================================

class InterfazOrganizador:
    """Interfaz gráfica moderna y profesional"""
    
    def __init__(self):
        self.organizador = OrganizadorAutomatico()
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica principal"""
        self.root = tk.Tk()
        self.root.title("Organizador Automático de Carpetas - Versión Pro")
        self.root.geometry("900x700")
        self.root.configure(bg='#f5f5f5')
        
        # Establecer icono (si existe)
        self.establecer_icono()
        
        # Configurar grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Crear widgets
        self.crear_cabecera()
        self.crear_panel_principal()
        self.crear_barra_estado()
        
        # Cargar tema
        self.aplicar_tema()
    
    def establecer_icono(self):
        """Establece el icono de la aplicación"""
        try:
            # Intentar cargar un icono personalizado
            if platform.system() == "Windows":
                self.root.iconbitmap(default="icono.ico")
            elif platform.system() == "Darwin":
                # macOS
                pass
        except:
            pass
    
    def crear_cabecera(self):
        """Crea la cabecera de la aplicación"""
        cabecera = tk.Frame(self.root, bg='#2c3e50', height=80)
        cabecera.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        cabecera.grid_columnconfigure(0, weight=1)
        
        # Logo y título
        frame_titulo = tk.Frame(cabecera, bg='#2c3e50')
        frame_titulo.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(
            frame_titulo,
            text="📁",
            font=("Segoe UI", 24),
            bg='#2c3e50',
            fg='white'
        ).pack(side=tk.LEFT)
        
        tk.Label(
            frame_titulo,
            text="Organizador Automático",
            font=("Segoe UI", 20, "bold"),
            bg='#2c3e50',
            fg='white'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Label(
            frame_titulo,
            text="PRO",
            font=("Segoe UI", 12, "bold"),
            bg='#e74c3c',
            fg='white',
            padx=8,
            pady=2,
            relief=tk.RAISED,
            bd=1
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de la cabecera
        frame_botones = tk.Frame(cabecera, bg='#2c3e50')
        frame_botones.pack(side=tk.RIGHT, padx=20, pady=10)
        
        botones_cabecera = [
            ("⚙️", self.mostrar_configuracion, "Configuración"),
            ("📊", self.mostrar_estadisticas, "Estadísticas"),
            ("❓", self.mostrar_ayuda, "Ayuda"),
            ("↻", self.actualizar_interfaz, "Actualizar")
        ]
        
        for texto, comando, tooltip in botones_cabecera:
            btn = tk.Button(
                frame_botones,
                text=texto,
                font=("Segoe UI", 14),
                bg='#34495e',
                fg='white',
                relief=tk.FLAT,
                cursor='hand2',
                command=comando
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.crear_tooltip(btn, tooltip)
    
    def crear_panel_principal(self):
        """Crea el panel principal de la aplicación"""
        # Frame principal con pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=20, pady=(10, 5))
        
        # Pestaña 1: Organización Rápida
        self.crear_tab_organizacion()
        
        # Pestaña 2: Configuración Avanzada
        self.crear_tab_configuracion()
        
        # Pestaña 3: Historial
        self.crear_tab_historial()
        
        # Pestaña 4: Favoritos
        self.crear_tab_favoritos()
    
    def crear_tab_organizacion(self):
        """Crea la pestaña de organización rápida"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🚀 Organización Rápida")
        
        # Configurar grid
        for i in range(3):
            tab.grid_rowconfigure(i, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        # Panel de selección de carpeta
        frame_seleccion = ttk.LabelFrame(tab, text="📂 Seleccionar Carpeta", padding=15)
        frame_seleccion.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        frame_seleccion.grid_columnconfigure(0, weight=1)
        
        # Campo de ruta
        self.ruta_var = tk.StringVar()
        self.entry_ruta = ttk.Entry(
            frame_seleccion,
            textvariable=self.ruta_var,
            font=('Segoe UI', 11)
        )
        self.entry_ruta.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        # Botón explorar
        btn_explorar = ttk.Button(
            frame_seleccion,
            text="Explorar...",
            command=self.seleccionar_carpeta,
            style='Accent.TButton'
        )
        btn_explorar.grid(row=0, column=1)
        
        # Botón carpeta actual
        btn_actual = ttk.Button(
            frame_seleccion,
            text="Carpeta Actual",
            command=self.usar_carpeta_actual
        )
        btn_actual.grid(row=0, column=2, padx=(10, 0))
        
        # Panel de opciones
        frame_opciones = ttk.LabelFrame(tab, text="⚙️ Opciones de Organización", padding=15)
        frame_opciones.grid(row=1, column=0, sticky='ew', padx=10, pady=10)
        
        # Variables de opciones
        self.var_tipo = tk.BooleanVar(value=True)
        self.var_fecha = tk.BooleanVar(value=True)
        self.var_proyecto = tk.BooleanVar(value=False)
        self.var_mover = tk.BooleanVar(value=True)
        self.var_seguro = tk.BooleanVar(value=True)
        
        # Checkboxes
        ttk.Checkbutton(
            frame_opciones,
            text="Organizar por tipo de archivo",
            variable=self.var_tipo
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        ttk.Checkbutton(
            frame_opciones,
            text="Organizar por fecha",
            variable=self.var_fecha
        ).grid(row=1, column=0, sticky='w', pady=5)
        
        ttk.Checkbutton(
            frame_opciones,
            text="Detectar proyectos automáticamente",
            variable=self.var_proyecto
        ).grid(row=2, column=0, sticky='w', pady=5)
        
        ttk.Checkbutton(
            frame_opciones,
            text="Mover archivos (en lugar de copiar)",
            variable=self.var_mover
        ).grid(row=0, column=1, sticky='w', pady=5, padx=(20, 0))
        
        ttk.Checkbutton(
            frame_opciones,
            text="Modo seguro (no sobrescribir)",
            variable=self.var_seguro
        ).grid(row=1, column=1, sticky='w', pady=5, padx=(20, 0))
        
        # Panel de acciones
        frame_acciones = ttk.Frame(tab)
        frame_acciones.grid(row=2, column=0, sticky='ew', padx=10, pady=20)
        frame_acciones.grid_columnconfigure(0, weight=1)
        
        # Botón organizar
        self.btn_organizar = ttk.Button(
            frame_acciones,
            text="🏁 ORGANIZAR AHORA",
            command=self.iniciar_organizacion,
            style='Success.TButton',
            width=25
        )
        self.btn_organizar.grid(row=0, column=0, pady=10)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            frame_acciones,
            mode='indeterminate',
            length=400
        )
        self.progress.grid(row=1, column=0, pady=10)
        
        # Etiqueta de estado
        self.etiqueta_estado = ttk.Label(
            frame_acciones,
            text="Listo para organizar archivos",
            font=('Segoe UI', 10)
        )
        self.etiqueta_estado.grid(row=2, column=0)
    
    def crear_tab_configuracion(self):
        """Crea la pestaña de configuración avanzada"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Configuración")
        
        # Aquí iría la configuración avanzada
        ttk.Label(tab, text="Configuración avanzada", font=('Segoe UI', 14)).pack(pady=20)
    
    def crear_tab_historial(self):
        """Crea la pestaña de historial"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Historial")
        
        # Aquí iría el historial
        ttk.Label(tab, text="Historial de operaciones", font=('Segoe UI', 14)).pack(pady=20)
    
    def crear_tab_favoritos(self):
        """Crea la pestaña de carpetas favoritas"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⭐ Favoritos")
        
        # Aquí irían las carpetas favoritas
        ttk.Label(tab, text="Carpetas favoritas", font=('Segoe UI', 14)).pack(pady=20)
    
    def crear_barra_estado(self):
        """Crea la barra de estado"""
        self.barra_estado = tk.Label(
            self.root,
            text="Listo | Archivos organizados: 0 | Espacio liberado: 0 MB",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg='white',
            fg='#2c3e50',
            font=('Segoe UI', 9)
        )
        self.barra_estado.grid(row=3, column=0, sticky='ew', padx=0, pady=(0, 0))
    
    def crear_tooltip(self, widget, texto):
        """Crea un tooltip para un widget"""
        def mostrar_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=texto,
                bg='yellow',
                relief='solid',
                borderwidth=1,
                font=('Segoe UI', 9)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def ocultar_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind('<Enter>', mostrar_tooltip)
        widget.bind('<Leave>', ocultar_tooltip)
    
    def aplicar_tema(self):
        """Aplica el tema visual"""
        try:
            style = ttk.Style()
            
            # Configurar tema claro por defecto
            style.theme_use('clam')
            
            # Configurar colores
            style.configure('TButton', font=('Segoe UI', 10))
            style.configure('Accent.TButton', background='#3498db', foreground='white')
            style.configure('Success.TButton', background='#27ae60', foreground='white')
            style.configure('Warning.TButton', background='#f39c12', foreground='white')
            
        except:
            pass
    
    # ============================================================================
    # MÉTODOS DE LA INTERFAZ
    # ============================================================================
    
    def seleccionar_carpeta(self):
        """Permite al usuario seleccionar una carpeta"""
        carpeta = filedialog.askdirectory(
            title="Selecciona la carpeta a organizar",
            mustexist=True
        )
        if carpeta:
            self.ruta_var.set(carpeta)
            self.etiqueta_estado.config(text=f"Carpeta seleccionada: {carpeta}")
    
    def usar_carpeta_actual(self):
        """Usa la carpeta actual del script"""
        carpeta_actual = os.getcwd()
        self.ruta_var.set(carpeta_actual)
        self.etiqueta_estado.config(text=f"Carpeta actual: {carpeta_actual}")
    
    def iniciar_organizacion(self):
        """Inicia el proceso de organización"""
        carpeta = self.ruta_var.get()
        
        if not carpeta or not os.path.exists(carpeta):
            messagebox.showerror("Error", "Por favor, selecciona una carpeta válida")
            return
        
        # Actualizar configuración con las opciones seleccionadas
        self.organizador.config["configuracion"]["organizar_por_tipo"] = self.var_tipo.get()
        self.organizador.config["configuracion"]["organizar_por_fecha"] = self.var_fecha.get()
        self.organizador.config["configuracion"]["organizar_por_proyecto"] = self.var_proyecto.get()
        self.organizador.config["configuracion"]["mover_archivos"] = self.var_mover.get()
        self.organizador.config["configuracion"]["modo_seguro"] = self.var_seguro.get()
        
        # Deshabilitar botón durante la operación
        self.btn_organizar.config(state='disabled', text="ORGANIZANDO...")
        self.progress.start()
        self.etiqueta_estado.config(text="Organizando archivos...")
        
        # Ejecutar en un hilo separado
        thread = threading.Thread(
            target=self.ejecutar_organizacion,
            args=(carpeta,),
            daemon=True
        )
        thread.start()
        
        # Monitorear progreso
        self.monitorear_progreso(thread)
    
    def ejecutar_organizacion(self, carpeta):
        """Ejecuta la organización en un hilo separado"""
        resultado = self.organizador.organizar_carpeta(
            carpeta,
            callback_progreso=self.actualizar_progreso
        )
        self.resultado_organizacion = resultado
    
    def actualizar_progreso(self, porcentaje, mensaje):
        """Actualiza la interfaz con el progreso"""
        self.root.after(0, lambda: self.etiqueta_estado.config(text=mensaje))
    
    def monitorear_progreso(self, thread):
        """Monitorea el progreso del hilo"""
        if thread.is_alive():
            self.root.after(100, lambda: self.monitorear_progreso(thread))
        else:
            self.finalizar_organizacion()
    
    def finalizar_organizacion(self):
        """Finaliza el proceso de organización"""
        self.progress.stop()
        self.btn_organizar.config(state='normal', text="🏁 ORGANIZAR AHORA")
        
        resultado = getattr(self, 'resultado_organizacion', {})
        
        if "error" in resultado:
            messagebox.showerror("Error", resultado["error"])
            self.etiqueta_estado.config(text="Error durante la organización")
        else:
            # Mostrar resultados
            estadisticas = resultado.get("estadisticas", {})
            archivos_movidos = estadisticas.get("archivos_movidos", 0)
            espacio_mb = estadisticas.get("espacio_liberado", 0) / (1024 * 1024)
            
            mensaje = f"""✅ Organización completada con éxito!

📊 Resultados:
• Archivos procesados: {estadisticas.get('archivos_procesados', 0)}
• Archivos organizados: {archivos_movidos}
• Carpetas creadas: {estadisticas.get('carpetas_creadas', 0)}
• Espacio organizado: {espacio_mb:.2f} MB
• Archivos omitidos: {estadisticas.get('archivos_omitidos', 0)}
• Errores: {estadisticas.get('errores', 0)}

La organización se ha completado correctamente."""
            
            messagebox.showinfo("Organización Completada", mensaje)
            
            # Actualizar barra de estado
            self.actualizar_barra_estado(estadisticas)
            
            self.etiqueta_estado.config(text="Organización completada con éxito!")
    
    def actualizar_barra_estado(self, estadisticas):
        """Actualiza la barra de estado con las estadísticas"""
        total_archivos = self.organizador.config["estadisticas"]["total_archivos"]
        archivos_organizados = self.organizador.config["estadisticas"]["archivos_organizados"]
        espacio_mb = estadisticas.get("espacio_liberado", 0) / (1024 * 1024)
        
        texto = f"Listo | Archivos totales: {total_archivos} | Organizados: {archivos_organizados} | Espacio: {espacio_mb:.2f} MB"
        self.barra_estado.config(text=texto)
    
    def mostrar_configuracion(self):
        """Muestra la ventana de configuración"""
        messagebox.showinfo("Configuración", "Ventana de configuración (en desarrollo)")
    
    def mostrar_estadisticas(self):
        """Muestra las estadísticas globales"""
        estadisticas = self.organizador.config["estadisticas"]
        
        mensaje = f"""📈 Estadísticas Globales

• Total de archivos procesados: {estadisticas['total_archivos']}
• Archivos organizados: {estadisticas['archivos_organizados']}
• Carpetas creadas: {estadisticas['carpetas_creadas']}
• Última organización: {estadisticas['ultima_organizacion'] or 'Nunca'}

💾 Configuración:
• Sistema operativo: {platform.system()} {platform.release()}
• Versión del organizador: {self.organizador.config['version']}
• Carpeta de configuración: {Configuracion.obtener_ruta_config()}"""
        
        messagebox.showinfo("Estadísticas", mensaje)
    
    def mostrar_ayuda(self):
        """Muestra la ventana de ayuda"""
        mensaje = """🤖 ORGANIZADOR AUTOMÁTICO - AYUDA

📋 CÓMO USAR:
1. Selecciona una carpeta usando el botón "Explorar"
2. Configura las opciones de organización
3. Haz clic en "ORGANIZAR AHORA"

⚙️ OPCIONES:
• Por tipo: Organiza en carpetas según la extensión
• Por fecha: Crea subcarpetas por mes/año
• Por proyecto: Detecta proyectos automáticamente
• Modo seguro: No sobrescribe archivos existentes

📁 CARPETAS CREADAS:
El sistema crea una estructura como:
📦 Carpeta_Organizados/
 ┣ 📸 Imágenes/2024-01/
 ┣ 📄 Documentos/2024-01/
 ┗ 🎵 Audio/2024-01/

⚠️ NOTA: Siempre haz una copia de seguridad antes de organizar archivos importantes.

Para más ayuda, visita la documentación completa."""
        
        messagebox.showinfo("Ayuda", mensaje)
    
    def actualizar_interfaz(self):
        """Actualiza la interfaz"""
        self.etiqueta_estado.config(text="Interfaz actualizada")
        messagebox.showinfo("Actualizado", "La interfaz ha sido actualizada")
    
    def run(self):
        """Ejecuta la aplicación"""
        # Centrar ventana
        self.root.update_idletasks()
        ancho = self.root.winfo_width()
        alto = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.root.winfo_screenheight() // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')
        
        self.root.mainloop()

# ============================================================================
# SCRIPT DE INSTALACIÓN
# ============================================================================

def crear_ejecutable_windows():
    """Crea un ejecutable para Windows"""
    script_instalacion = '''@echo off
echo Instalando Organizador Automático de Carpetas...
echo.

REM Crear directorio de instalación
set INSTALL_DIR=%USERPROFILE%\\OrganizadorAutomatico
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copiar archivos
copy "organizador_mejorado.py" "%INSTALL_DIR%\\OrganizadorAutomatico.py"
copy "config.json" "%INSTALL_DIR%\\" >nul 2>&1

REM Crear acceso directo en escritorio
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\\crear_acceso.vbs"
echo sLinkFile = "%USERPROFILE%\\Desktop\\Organizador Automático.lnk" >> "%TEMP%\\crear_acceso.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\\crear_acceso.vbs"
echo oLink.TargetPath = "pythonw.exe" >> "%TEMP%\\crear_acceso.vbs"
echo oLink.Arguments = "%INSTALL_DIR%\\OrganizadorAutomatico.py" >> "%TEMP%\\crear_acceso.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\\crear_acceso.vbs"
echo oLink.Save >> "%TEMP%\\crear_acceso.vbs"
cscript //nologo "%TEMP%\\crear_acceso.vbs"
del "%TEMP%\\crear_acceso.vbs"

echo.
echo ✅ Instalación completada!
echo.
echo Se ha creado un acceso directo en el escritorio.
echo.
pause
'''
    
    with open("instalar_windows.bat", "w", encoding="utf-8") as f:
        f.write(script_instalacion)
    
    print("Script de instalación para Windows creado: 'instalar_windows.bat'")

def crear_ejecutable_mac():
    """Crea un ejecutable para macOS"""
    script_instalacion = '''#!/bin/bash
echo "Instalando Organizador Automático de Carpetas..."
echo ""

# Crear directorio de instalación
INSTALL_DIR="$HOME/Applications/OrganizadorAutomatico"
mkdir -p "$INSTALL_DIR"

# Copiar archivos
cp "organizador_mejorado.py" "$INSTALL_DIR/OrganizadorAutomatico.py"
cp "config.json" "$INSTALL_DIR/" 2>/dev/null || true

# Hacer ejecutable
chmod +x "$INSTALL_DIR/OrganizadorAutomatico.py"

# Crear aplicación .app
APP_DIR="$HOME/Applications/Organizador Automático.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Crear Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Organizador Automático</string>
    <key>CFBundleExecutable</key>
    <string>organizador</string>
    <key>CFBundleIdentifier</key>
    <string>com.organizador.automatico</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

# Crear script ejecutable
cat > "$APP_DIR/Contents/MacOS/organizador" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 "OrganizadorAutomatico.py"
EOF

chmod +x "$APP_DIR/Contents/MacOS/organizador"

echo ""
echo "✅ Instalación completada!"
echo ""
echo "La aplicación se ha instalado en: $APP_DIR"
echo ""
read -p "Presiona Enter para continuar..."
'''
    
    with open("instalar_mac.command", "w", encoding="utf-8") as f:
        f.write(script_instalacion)
    
    # Hacer ejecutable
    os.chmod("instalar_mac.command", 0o755)
    
    print("Script de instalación para macOS creado: 'instalar_mac.command'")

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    # Verificar si se pasaron argumentos
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "--instalar-windows":
            crear_ejecutable_windows()
            print("Ejecuta 'instalar_windows.bat' para completar la instalación")
        
        elif comando == "--instalar-mac":
            crear_ejecutable_mac()
            print("Ejecuta 'instalar_mac.command' para completar la instalación")
        
        elif comando == "--organizar":
            # Modo línea de comandos
            if len(sys.argv) > 2:
                carpeta = sys.argv[2]
                organizador = OrganizadorAutomatico()
                resultado = organizador.organizar_carpeta(carpeta)
                
                if "error" in resultado:
                    print(f"Error: {resultado['error']}")
                else:
                    print("✅ Organización completada con éxito!")
                    for key, value in resultado.get("estadisticas", {}).items():
                        print(f"{key}: {value}")
            else:
                print("Uso: python organizador_mejorado.py --organizar <carpeta>")
        
        elif comando == "--configuracion":
            print("Mostrando configuración...")
            config = Configuracion.cargar()
            print(json.dumps(config, indent=2, ensure_ascii=False))
        
        elif comando == "--ayuda" or comando == "-h":
            print("""
ORGANIZADOR AUTOMÁTICO DE CARPETAS - AYUDA

Uso:
  python organizador_mejorado.py [opciones]

Opciones:
  --instalar-windows   Crear instalador para Windows
  --instalar-mac       Crear instalador para macOS
  --organizar <carpeta> Organizar carpeta desde línea de comandos
  --configuracion      Mostrar configuración actual
  --ayuda, -h          Mostrar esta ayuda

Sin argumentos: Iniciar interfaz gráfica
            """)
    
    else:
        # Iniciar interfaz gráfica por defecto
        try:
            app = InterfazOrganizador()
            app.run()
        except Exception as e:
            print(f"Error iniciando la interfaz: {e}")
            print("Intentando modo consola...")
            
            # Modo consola de emergencia
            print("\n=== MODO CONSOLA DE EMERGENCIA ===")
            carpeta = input("Introduce la carpeta a organizar: ").strip()
            
            if os.path.exists(carpeta):
                organizador = OrganizadorAutomatico()
                resultado = organizador.organizar_carpeta(carpeta)
                
                if "error" in resultado:
                    print(f"Error: {resultado['error']}")
                else:
                    print("✅ Organización completada!")
                    print("📊 Estadísticas:")
                    for key, value in resultado.get("estadisticas", {}).items():
                        print(f"  {key}: {value}")
            else:
                print("Error: La carpeta no existe")
