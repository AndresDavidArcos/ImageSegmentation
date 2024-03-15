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
        slice_data = data[:, :, int(slice_num)]
    else:
        slice_data = data_segmentated[:, :, int(slice_num)]

    img_tk = Image.fromarray(slice_data)

    canvas.delete("all")
    canvas.image = ImageTk.PhotoImage(img_tk)
    canvas.create_image(canvas.winfo_width() / 2, canvas.winfo_height() / 2, anchor="center", image=canvas.image)

def slider_changed(event):
    plot_nii_slice(slice_slider.get())

def run_threshold():
    global data, data_segmentated
    threshold = int(threshold_entry.get())

    if data is not None:
        data_segmentated = np.where(data > threshold, 255, 0)
        plot_nii_slice(slice_slider.get())

def calculate_isodata_threshold(initial_threshold):
    threshold = initial_threshold
    diff = 0.01
    while True:
        m_foreground = data[data > threshold].mean()
        m_background = data[data <= threshold].mean()
        new_threshold = (m_foreground+m_background)/2
        if abs(threshold - new_threshold) <= diff:
            break
        threshold = new_threshold
    return threshold

def threshold_clicked():
    clear_head()
    threshold_frame = ttk.Frame(head_frame)
    threshold_frame.pack(fill="x", padx=10, pady=5)

    threshold_label = ttk.Label(threshold_frame, text="Threshold:")
    threshold_label.pack(side="left")

    global threshold_entry
    threshold_entry = ttk.Entry(threshold_frame)
    threshold_entry.pack(side="left", padx=(0, 5))

    threshold_button = ttk.Button(threshold_frame, text="Run", command=run_threshold)
    threshold_button.pack(side="left")

def isodata_clicked():
    clear_head()
    threshold_frame = ttk.Frame(head_frame)
    threshold_frame.pack(fill="x", padx=10, pady=5)

    initial_threshold_label = ttk.Label(threshold_frame, text="Threshold inicial:")
    initial_threshold_label.pack(side="left")

    global initial_threshold_entry
    initial_threshold_entry = ttk.Entry(threshold_frame, width=5)
    initial_threshold_entry.insert(0, "127")
    initial_threshold_entry.pack(side="left")

    threshold_button = ttk.Button(threshold_frame, text="Calculate Isodata", command=lambda: calculate_and_show_isodata(int(initial_threshold_entry.get())))
    threshold_button.pack(side="left", padx=10)

def calculate_and_show_isodata(initial_threshold):
    threshold = calculate_isodata_threshold(initial_threshold)
    isodata_text = ttk.Label(head_frame, text="Isodata Threshold: {}".format(threshold))
    isodata_text.pack(side="left", padx=10)

def clear_head():
    for widget in head_frame.winfo_children():
        widget.destroy()

# Función para cargar un archivo .nii
def load_nii_file():
    global nii_file_path, data
    nii_file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii")])
    if nii_file_path:
        img = nib.load(nii_file_path)
        data = img.get_fdata()
        num_slices = img.shape[2]
        slice_slider.config(to=num_slices-1)
        plot_nii_slice(0)

root = tk.Tk()
root.title("Visualizador de Imagen NIfTI")

navbar_frame = ttk.Frame(root, width=200)
navbar_frame.pack(side="left", fill="y")

load_button = ttk.Button(navbar_frame, text="Cargar archivo .nii", command=load_nii_file)
load_button.pack(side="top", padx=10, pady=5)

threshold_anchor = ttk.Label(navbar_frame, text="Umbralización", cursor="hand2")
threshold_anchor.pack(side="top", pady=10)
threshold_anchor.bind("<Button-1>", lambda event: threshold_clicked())

head_frame = ttk.Frame(root)
head_frame.pack(side="top", fill="x")

canvas = tk.Canvas(root, width=400, height=400)
canvas.pack()

slice_slider = ttk.Scale(root, from_=0, to=0, orient="horizontal", command=slider_changed)
slice_slider.pack()

isodata_anchor = ttk.Label(navbar_frame, text="Isodata", cursor="hand2")
isodata_anchor.pack(side="top", pady=10)
isodata_anchor.bind("<Button-1>", lambda event: isodata_clicked())

root.mainloop()
