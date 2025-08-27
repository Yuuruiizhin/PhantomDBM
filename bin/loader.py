import tkinter as tk
from tkinter import ttk
import webbrowser
import os
import subprocess
import sys
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import socket

# --- Función para obtener la ruta correcta de los recursos ---
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta de un recurso.
    
    Esta función es necesaria para que PyInstaller encuentre los archivos
    en la carpeta temporal creada al ejecutar el .exe.
    """
    try:
        # PyInstaller crea una ruta temporal y la guarda en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En el entorno de desarrollo, usamos la ruta del archivo actual
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Función para obtener la IP local de la máquina ---
def get_local_ip():
    """
    Detecta automáticamente la dirección IP de la máquina en la red local.
    
    Se crea un socket temporal para conectarse a una dirección externa
    (8.8.8.8) y obtener la dirección IP local utilizada para esa conexión.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # En caso de error (sin conexión a Internet), se usa la IP de localhost
        print("Advertencia: No se pudo detectar la IP de red. Usando localhost.")
        return '127.0.0.1'

# --- Configuración de la aplicación ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inicializador del sistema")
        self.geometry("400x300")
        self.configure(bg="#333")
        self.resizable(False, False)

        self.app_process = None
        self.tray_icon = None
        
        self.set_window_icon()
        
        self.bind("<Unmap>", self.on_minimize)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.main_frame = tk.Frame(self, bg="#333")
        self.main_frame.pack(expand=True, padx=20, pady=20)

        self.image_label = None
        self.progress_bar = None
        self.load_image()
        self.start_loading()
        # Inicia el servidor Flask en segundo plano después de que la carga haya terminado
        self.run_app_in_background()

    def set_window_icon(self):
        icon_path = resource_path(os.path.join("static", "img", "phantomw.png"))
        try:
            pil_icon = Image.open(icon_path)
            self.tk_icon = ImageTk.PhotoImage(pil_icon.resize((32, 32), Image.Resampling.LANCZOS))
            self.iconphoto(False, self.tk_icon)
            self.tray_icon_image = Image.open(icon_path)
        except FileNotFoundError:
            print("Advertencia: No se encontró la imagen para el ícono.")
        except Exception as e:
            print(f"Error al cargar el ícono de la ventana: {e}")
            
    def run_app_in_background(self):
        """Inicia el ejecutable 'phantomsv.exe' como un subproceso sin ventana de consola."""
        try:
            self.app_process = subprocess.Popen(
                ["phantomsv.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("El ejecutable 'phantomsv.exe' se ha iniciado en segundo plano.")
        except FileNotFoundError:
            print("Error: El archivo 'phantomsv.exe' no se encontró.")
        except Exception as e:
            print(f"Error al intentar ejecutar el script 'phantomsv.exe': {e}")

    def on_minimize(self, event=None):
        """
        Se ejecuta cuando la ventana se minimiza. Oculta la ventana y
        crea un ícono en la bandeja del sistema.
        """
        self.withdraw()
        
        if not self.tray_icon:
            menu = (
                item('Mostrar', self.show_window),
                item('Salir', self.on_close)
            )
            self.tray_icon = pystray.Icon("PhantomDBM Launcher", self.tray_icon_image, "PhantomDBM Launcher", menu)
            self.tray_icon.run()

    def show_window(self, icon, item):
        self.tray_icon.stop()
        self.tray_icon = None
        self.deiconify()

    def on_close(self, icon=None, item=None):
        """
        Maneja el cierre de la ventana, terminando el subproceso de 'app.exe'
        y cerrando la aplicación principal.
        """
        if self.app_process and self.app_process.poll() is None:
            print("Terminando el proceso de app.exe...")
            self.app_process.terminate()
            self.app_process.wait(timeout=5)
            if self.app_process.poll() is None:
                self.app_process.kill()
                print("El proceso de app.exe ha sido forzado a cerrar.")
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.destroy()

    def load_image(self):
        image_path = resource_path(os.path.join("static", "img", "phantomw.png"))
        try:
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(pil_image)
            self.image_label = tk.Label(self.main_frame, image=self.tk_image, bg="#333")
            self.image_label.pack(pady=(0, 20))
        except FileNotFoundError:
            self.image_label = tk.Label(self.main_frame, text="Error: No se encontró la imagen.\nAsegúrate de tener la imagen 'static/img/phantomw.png'",
                                        fg="red", bg="#333", font=("Helvetica", 10))
            self.image_label.pack(pady=(0, 20))
        except Exception as e:
            self.image_label = tk.Label(self.main_frame, text=f"Error al cargar la imagen: {e}",
                                        fg="red", bg="#333", font=("Helvetica", 10))
            self.image_label.pack(pady=(0, 20))

    def start_loading(self):
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            orient="horizontal",
            length=250,
            mode="determinate"
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar["maximum"] = 100
        self.progress_bar["value"] = 0
        self.after(30, self.update_progress_bar, 0)

    def update_progress_bar(self, current_value):
        if current_value < 100:
            new_value = current_value + 1
            self.progress_bar["value"] = new_value
            self.after(30, self.update_progress_bar, new_value)
        else:
            self.finalize_ui()

    def finalize_ui(self):
        if self.progress_bar:
            self.progress_bar.destroy()

        completion_label = tk.Label(
            self.main_frame,
            text="Sistema inicializado",
            font=("Helvetica", 14, "bold"),
            bg="#333",
            fg="white"
        )
        completion_label.pack(pady=(10, 15))

        open_button = tk.Button(
            self.main_frame,
            text="Abrir",
            command=self.open_browser,
            bg="#DA9CFF",
            fg="black",
            font=("Helvetica", 12, "bold"),
            relief="raised",
            bd=3,
            activebackground="#C287E8",
            padx=15,
            pady=5
        )
        open_button.pack()

    def open_browser(self):
        local_ip = get_local_ip()
        url = f"http://{local_ip}:4861/"
        webbrowser.open_new_tab(url)

if __name__ == "__main__":
    app = App()
    app.mainloop()