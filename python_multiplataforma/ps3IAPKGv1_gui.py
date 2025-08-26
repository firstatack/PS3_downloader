#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI para PS3 Descargador y Procesador en Cola
Interfaz gráfica con Tkinter para el script ps3IAPKGv1.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import sys
import os
from pathlib import Path

# Importar el script original
import ps3IAPKGv1 as logic

# Colores para la interfaz
COLORS = {
    "red": "#FF5252",
    "cyan": "#00FFFF",
    "green": "#4CAF50",
    "yellow": "#FFD600",
    "reset": "#000000"
}

class PS3DownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PS3 Descargador y Procesador")
        self.root.geometry("900x700")
        
        # Cola para comunicación entre hilos
        self.log_queue = queue.Queue()
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_widgets()
        
        # Cargar archivos PKG al iniciar
        self.load_pkg_files()
        
        # Iniciar poll de la cola de logs
        self.poll_log_queue()
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", padding=[10, 5], font=('Helvetica', 10, 'bold'))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'), foreground=COLORS["cyan"])
        style.configure("Log.TFrame", background="#f0f0f0")
    
    def create_widgets(self):
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de Archive.org
        self.archive_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.archive_frame, text="Archive.org")
        self.setup_archive_tab()
        
        # Pestaña de PKG
        self.pkg_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pkg_frame, text="PKG")
        self.setup_pkg_tab()
        
        # Pestaña de Configuración
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuración")
        self.setup_config_tab()
        
        # Pestaña de Logs
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Mensajes")
        self.setup_log_tab()
    
    def setup_archive_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.archive_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, text="Descargas desde Archive.org", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # Botón para actualizar cache
        update_btn = ttk.Button(main_frame, text="Actualizar Lista de Ítems", 
                               command=self.update_items_cache)
        update_btn.pack(pady=5)
        
        # Frame para selección de ítem
        item_frame = ttk.LabelFrame(main_frame, text="Seleccionar Ítem")
        item_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(item_frame, text="Ítem:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(item_frame, textvariable=self.item_var, state="readonly")
        self.item_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.item_combo.bind('<<ComboboxSelected>>', self.on_item_selected)
        
        # Frame para selección de archivos
        files_frame = ttk.LabelFrame(main_frame, text="Seleccionar Archivos")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Lista de archivos con scrollbar
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.files_listbox = tk.Listbox(files_list_frame, selectmode=tk.MULTIPLE, height=10)
        scrollbar = ttk.Scrollbar(files_list_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para directorios
        dirs_frame = ttk.Frame(main_frame)
        dirs_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(dirs_frame, text="Destino temporal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.temp_dir_var = tk.StringVar()
        ttk.Entry(dirs_frame, textvariable=self.temp_dir_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(dirs_frame, text="Examinar", command=self.browse_temp_dir).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(dirs_frame, text="Destino final:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.final_dir_var = tk.StringVar()
        ttk.Entry(dirs_frame, textvariable=self.final_dir_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(dirs_frame, text="Examinar", command=self.browse_final_dir).grid(row=1, column=2, padx=5, pady=5)
        
        dirs_frame.columnconfigure(1, weight=1)
        
        # Botón de descarga
        download_btn = ttk.Button(main_frame, text="Iniciar Descarga y Procesamiento", 
                                 command=self.start_archive_download)
        download_btn.pack(pady=10)
    
    def setup_pkg_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.pkg_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, text="Descargas desde PKG", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # Frame para archivos PKG
        pkg_files_frame = ttk.LabelFrame(main_frame, text="Archivos PKG Disponibles")
        pkg_files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        pkg_list_frame = ttk.Frame(pkg_files_frame)
        pkg_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.pkg_listbox = tk.Listbox(pkg_list_frame, selectmode=tk.SINGLE, height=8)
        pkg_scrollbar = ttk.Scrollbar(pkg_list_frame, orient=tk.VERTICAL, command=self.pkg_listbox.yview)
        self.pkg_listbox.configure(yscrollcommand=pkg_scrollbar.set)
        self.pkg_listbox.bind('<<ListboxSelect>>', self.on_pkg_file_selected)
        
        self.pkg_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pkg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón para cargar contenido
        btn_frame = ttk.Frame(pkg_files_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Cargar Contenido del Fichero", 
                  command=self.load_pkg_content).pack(side=tk.LEFT, padx=5)
        
        # Frame para juegos disponibles
        games_frame = ttk.LabelFrame(main_frame, text="Juegos Disponibles")
        games_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        games_list_frame = ttk.Frame(games_frame)
        games_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.games_listbox = tk.Listbox(games_list_frame, selectmode=tk.MULTIPLE, height=8)
        games_scrollbar = ttk.Scrollbar(games_list_frame, orient=tk.VERTICAL, command=self.games_listbox.yview)
        self.games_listbox.configure(yscrollcommand=games_scrollbar.set)
        
        self.games_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        games_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para directorio de destino
        dest_frame = ttk.Frame(main_frame)
        dest_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(dest_frame, text="Directorio de destino:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.pkg_dest_var = tk.StringVar(value=str(Path.home()))
        ttk.Entry(dest_frame, textvariable=self.pkg_dest_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(dest_frame, text="Examinar", command=self.browse_pkg_dest).grid(row=0, column=2, padx=5, pady=5)
        
        dest_frame.columnconfigure(1, weight=1)
        
        # Botón de descarga
        download_btn = ttk.Button(main_frame, text="Iniciar Descarga PKG", 
                                 command=self.start_pkg_download)
        download_btn.pack(pady=10)
    
    def setup_config_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.config_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, text="Configuración de Cuenta Archive.org", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # Frame para credenciales
        creds_frame = ttk.LabelFrame(main_frame, text="Credenciales")
        creds_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(creds_frame, text="Access Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.access_var = tk.StringVar()
        ttk.Entry(creds_frame, textvariable=self.access_var, show="*").grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(creds_frame, text="Secret Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.secret_var = tk.StringVar()
        ttk.Entry(creds_frame, textvariable=self.secret_var, show="*").grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        creds_frame.columnconfigure(1, weight=1)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Cargar Configuración", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar Configuración", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Probar Conexión", command=self.test_connection).pack(side=tk.LEFT, padx=5)
    
    def setup_log_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.log_frame, style="Log.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Área de texto para logs
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Botones de control de log
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Limpiar Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar Log", command=self.save_log).pack(side=tk.LEFT, padx=5)
    
    def load_pkg_files(self):
        """Carga automáticamente todos los archivos .txt del directorio pkg"""
        try:
            txt_files = sorted([p for p in logic.PKG_DIR.rglob('*.txt') if p.is_file()])
            self.pkg_listbox.delete(0, tk.END)
            
            for p in txt_files:
                self.pkg_listbox.insert(tk.END, str(p))
                
            if txt_files:
                self.log_message(f"✅ Encontrados {len(txt_files)} archivos PKG en {logic.PKG_DIR}")
            else:
                self.log_message(f"ℹ️ No se encontraron archivos PKG en {logic.PKG_DIR}")
        except Exception as e:
            self.log_message(f"❌ Error al cargar archivos PKG: {e}")
    
    def on_pkg_file_selected(self, event):
        """Cuando se selecciona un archivo PKG, mostrar información"""
        selection = self.pkg_listbox.curselection()
        if selection:
            file_path = self.pkg_listbox.get(selection[0])
            self.log_message(f"Seleccionado: {os.path.basename(file_path)}")
    
    def load_pkg_content(self):
        """Carga el contenido del archivo PKG seleccionado"""
        selection = self.pkg_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un archivo PKG primero")
            return
        
        file_path = Path(self.pkg_listbox.get(selection[0]))
        
        try:
            # Parsear el archivo PKG
            entries = logic.parse_pkg_txt(file_path)
            
            # Limpiar lista y mapping
            self.games_listbox.delete(0, tk.END)
            self.pkg_entries = {}
            
            # Agregar juegos a la lista y guardar mapping
            for name, url in entries:
                self.games_listbox.insert(tk.END, name)
                self.pkg_entries[name] = url
            
            self.log_message(f"✅ Cargados {len(entries)} juegos desde {file_path.name}")
            
        except Exception as e:
            self.log_message(f"❌ Error al cargar el contenido del archivo: {e}")
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")
    
    def update_items_cache(self):
        def worker():
            self.log_message("Actualizando lista de ítems desde archive.org...")
            success = logic.actualizar_cache_items()
            if success:
                self.load_items_list()
                self.log_message("✅ Lista de ítems actualizada correctamente")
            else:
                self.log_message("❌ Error al actualizar la lista de ítems")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def load_items_list(self):
        if logic.CACHE_FILE.exists():
            items = [line.strip() for line in logic.CACHE_FILE.read_text(encoding='utf-8').splitlines() if line.strip()]
            self.item_combo['values'] = items
            if items:
                self.item_var.set(items[0])
    
    def on_item_selected(self, event):
        selected_item = self.item_var.get()
        if not selected_item:
            return
        
        def worker():
            self.log_message(f"Obteniendo archivos para: {selected_item}")
            try:
                # Actualizar cache de archivos del item
                item_files_cache = logic.IA_PS3_DIR / f"{selected_item}_files_cache.txt"
                
                if not item_files_cache.exists():
                    self.log_message("Actualizando lista de archivos...")
                    item = logic.ia.get_item(selected_item)
                    names = [f.get('name') for f in item.files if f.get('name')]
                    names = [n for n in names if n.strip()]
                    if names:
                        item_files_cache.write_text("\n".join(names), encoding='utf-8')
                
                # Cargar archivos en la lista
                file_list = [line.strip() for line in item_files_cache.read_text(encoding='utf-8').splitlines() if line.strip()]
                
                # Actualizar UI en el hilo principal
                self.root.after(0, self.update_files_list, file_list)
                self.log_message(f"✅ {len(file_list)} archivos encontrados")
                
            except Exception as e:
                self.log_message(f"❌ Error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def update_files_list(self, file_list):
        self.files_listbox.delete(0, tk.END)
        for file in file_list:
            self.files_listbox.insert(tk.END, file)
    
    def browse_temp_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio temporal")
        if directory:
            self.temp_dir_var.set(directory)
    
    def browse_final_dir(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio final")
        if directory:
            self.final_dir_var.set(directory)
    
    def start_archive_download(self):
        # Validaciones
        selected_item = self.item_var.get()
        if not selected_item:
            messagebox.showerror("Error", "Debe seleccionar un ítem")
            return
        
        selected_files = [self.files_listbox.get(i) for i in self.files_listbox.curselection()]
        if not selected_files:
            messagebox.showerror("Error", "Debe seleccionar al menos un archivo")
            return
        
        temp_dir = self.temp_dir_var.get()
        if not temp_dir:
            messagebox.showerror("Error", "Debe especificar un directorio temporal")
            return
        
        final_dir = self.final_dir_var.get()
        if not final_dir:
            messagebox.showerror("Error", "Debe especificar un directorio final")
            return
        
        # Ejecutar en hilo separado
        def worker():
            try:
                for fname in selected_files:
                    self.log_message(f"Iniciando descarga de: {fname}")
                    ok = logic.descargar_archivo(selected_item, fname, Path(temp_dir))
                    
                    if ok:
                        pending_input = Path(temp_dir) / selected_item / fname
                        sanitized = logic.sanitize_filename(fname)
                        pending_output = Path(final_dir) / f"{sanitized}.decrypted.iso"
                        
                        if pending_input.exists():
                            self.log_message(f"Procesando: {fname}")
                            logic.procesar_archivo_con_libray(pending_input, pending_output)
                    else:
                        self.log_message(f"Error en la descarga de: {fname}")
                
                self.log_message("✅ Todos los archivos han sido procesados")
                
            except Exception as e:
                self.log_message(f"❌ Error durante el proceso: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def browse_pkg_dest(self):
        directory = filedialog.askdirectory(title="Seleccionar directorio de destino")
        if directory:
            self.pkg_dest_var.set(directory)
    
    def start_pkg_download(self):
        selected_games = [self.games_listbox.get(i) for i in self.games_listbox.curselection()]
        if not selected_games:
            messagebox.showerror("Error", "Debe seleccionar al menos un juego")
            return
        
        dest_dir = self.pkg_dest_var.get()
        if not dest_dir:
            messagebox.showerror("Error", "Debe especificar un directorio de destino")
            return
        
        # Ejecutar en hilo separado
        def worker():
            try:
                downloaded_count = 0
                
                for name in selected_games:
                    url = self.pkg_entries.get(name)
                    if url:
                        self.log_message(f"Descargando: {name}")
                        nombre_archivo = os.path.basename(url)
                        destino = Path(dest_dir) / nombre_archivo
                        if logic.descargar_pkg(url, destino):
                            downloaded_count += 1
                
                self.log_message(f"✅ Descargas completadas: {downloaded_count} de {len(selected_games)} juegos")
                
            except Exception as e:
                self.log_message(f"❌ Error durante la descarga PKG: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def load_config(self):
        config_text = logic.leer_config_ia()
        if config_text:
            access = ""
            secret = ""
            for line in config_text.split('\n'):
                if line.startswith('access ='):
                    access = line.split('=', 1)[1].strip()
                elif line.startswith('secret ='):
                    secret = line.split('=', 1)[1].strip()
            
            self.access_var.set(access)
            self.secret_var.set(secret)
            self.log_message("✅ Configuración cargada")
        else:
            self.log_message("ℹ️ No se encontró configuración existente")
    
    def save_config(self):
        access = self.access_var.get()
        secret = self.secret_var.get()
        
        if not access or not secret:
            messagebox.showerror("Error", "Debe completar ambos campos")
            return
        
        logic.escribir_config_ia(access, secret)
        self.log_message("✅ Configuración guardada correctamente")
    
    def test_connection(self):
        def worker():
            try:
                self.log_message("Probando conexión con Archive.org...")
                # Intentar una búsqueda simple para probar la conexión
                results = logic.ia.search_items("sony_playstation3", max_results=1)
                count = len(list(results))
                self.log_message(f"✅ Conexión exitosa. {count} resultados encontrados")
            except Exception as e:
                self.log_message(f"❌ Error de conexión: {e}")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def log_message(self, message):
        """Agrega un mensaje a la cola para ser mostrado en el log"""
        self.log_queue.put(message)
    
    def poll_log_queue(self):
        """Verifica periódicamente la cola de mensajes y los muestra en el log"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.append_to_log(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_log_queue)
    
    def append_to_log(self, message):
        """Agrega un mensaje al área de texto de logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Limpia el área de texto de logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def save_log(self):
        """Guarda el log en un archivo"""
        filename = filedialog.asksaveasfilename(
            title="Guardar log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"✅ Log guardado en: {filename}")
            except Exception as e:
                self.log_message(f"❌ Error al guardar el log: {e}")

def main():
    root = tk.Tk()
    app = PS3DownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
