import nibabel as nib
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

nii_file_path = ""
data = None
data_segmentated = None

def plot_nii_slice(slice_num):
    global data, data_segmentated

    if data_segmentated is None:
        # Si data_segmentated es None, usar data original
        slice_data = data[:, :, int(slice_num)]
    else:
        # Usar data_segmentated si está definido
        slice_data = data_segmentated[:, :, int(slice_num)]

    # Convertir la matriz NumPy en una imagen tkinter
    img_tk = Image.fromarray(slice_data)

    # Mostrar la imagen en el canvas
    canvas.delete("all")
    canvas.image = ImageTk.PhotoImage(img_tk)  # Mantener una referencia para evitar que la imagen sea recolectada por el recolector de basura
    canvas.create_image(canvas.winfo_width() / 2, canvas.winfo_height() / 2, anchor="center", image=canvas.image)

# Función para manejar el cambio en el slider
def slider_changed(event):
    plot_nii_slice(slice_slider.get())

# Función para manejar la umbralización
def run_threshold():
    global data, data_segmentated
    threshold = int(threshold_entry.get())

    if data is not None:
        # Umbralizar la imagen
        data_segmentated = np.where(data > threshold, 255, 0)

        # Actualizar la visualización al umbralizar
        plot_nii_slice(slice_slider.get())

# Función para manejar la umbralización
def threshold_clicked():
    global threshold_frame
    threshold_frame = ttk.Frame(head_frame)
    threshold_frame.pack(fill="x", padx=10, pady=5)

    threshold_label = ttk.Label(threshold_frame, text="Threshold:")
    threshold_label.pack(side="left")

    global threshold_entry
    threshold_entry = ttk.Entry(threshold_frame)
    threshold_entry.pack(side="left", padx=(0, 5))

    threshold_button = ttk.Button(threshold_frame, text="Run", command=run_threshold)
    threshold_button.pack(side="left")


# Función para cargar un archivo .nii
def load_nii_file():
    global nii_file_path, data
    nii_file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii")])
    if nii_file_path:
        # Cargar el archivo .nii
        img = nib.load(nii_file_path)
        data = img.get_fdata()

        # Obtener el número de slices del archivo .nii
        num_slices = img.shape[2]
        slice_slider.config(to=num_slices-1)  # Configurar el rango del slider

        # Mostrar el primer slice inicialmente
        plot_nii_slice(0)

# Crear la ventana principal
root = tk.Tk()
root.title("Visualizador de Imagen NIfTI")

# Crear el marco para la barra de navegación
navbar_frame = ttk.Frame(root, width=200)
navbar_frame.pack(side="left", fill="y")

# Crear el botón para cargar el archivo .nii
load_button = ttk.Button(navbar_frame, text="Cargar archivo .nii", command=load_nii_file)
load_button.pack(side="top", padx=10, pady=5)

# Crear el anchor para la umbralización en la barra de navegación
threshold_anchor = ttk.Label(navbar_frame, text="Umbralización", cursor="hand2")
threshold_anchor.pack(side="top", pady=10)
threshold_anchor.bind("<Button-1>", lambda event: threshold_clicked())



# Crear el marco para la headbar
head_frame = ttk.Frame(root)
head_frame.pack(side="top", fill="x")

# Crear el canvas para mostrar la imagen
canvas = tk.Canvas(root, width=400, height=400)
canvas.pack()

# Crear el slider para navegar por las slices
slice_slider = ttk.Scale(root, from_=0, to=0, orient="horizontal", command=slider_changed)
slice_slider.pack()

# Iniciar el bucle de la interfaz gráfica
root.mainloop()
