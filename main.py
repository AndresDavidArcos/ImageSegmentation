import uuid
from tkinter.colorchooser import askcolor
import nibabel as nib
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

nii_file_path = ""
data = None
data_segmentated = None
seed = None
canvas_image_id = None
img_width = None
img_height = None
threshold_entry = None
intensity_tolerance_entry = None
draw_color_button = None

def plot_nii_slice(slice_num):
    global data, data_segmentated, canvas_image_id, img_width, img_height

    if data_segmentated is None:
        slice_data = data[int(slice_num), :, :]
    else:
        slice_data = data_segmentated[int(slice_num), :, :]

    img_tk = Image.fromarray(slice_data)

    canvas.delete("all")
    canvas.image = ImageTk.PhotoImage(img_tk)
    canvas_image_id = canvas.create_image(canvas.winfo_width() / 2, canvas.winfo_height() / 2, anchor="center",
                                          image=canvas.image)
    img_width = img_tk.width
    img_height = img_tk.height


def slider_changed(event):
    plot_nii_slice(int(slice_slider.get()))


def run_threshold():
    global data, data_segmentated
    threshold = int(threshold_entry.get())

    if data is not None:
        data_segmentated = np.where(data > threshold, 255, 0)
        plot_nii_slice(int(slice_slider.get()))


def calculate_isodata_threshold(initial_threshold):
    threshold = initial_threshold
    diff = 0.01
    while True:
        m_foreground = data[data > threshold].mean()
        m_background = data[data <= threshold].mean()
        new_threshold = (m_foreground + m_background) / 2
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

    threshold_button = ttk.Button(threshold_frame, text="Calculate Isodata",
                                  command=lambda: calculate_and_show_isodata(int(initial_threshold_entry.get())))
    threshold_button.pack(side="left", padx=10)


def calculate_and_show_isodata(initial_threshold):
    threshold = calculate_isodata_threshold(initial_threshold)
    isodata_text = ttk.Label(head_frame, text="Isodata Threshold: {}".format(threshold))
    isodata_text.pack(side="left", padx=10)


def region_growing_clicked():
    clear_head()
    threshold_frame = ttk.Frame(head_frame)
    threshold_frame.pack(fill="x", padx=10, pady=5)

    intensity_tolerance_label = ttk.Label(threshold_frame, text="Intensity Tolerance:")
    intensity_tolerance_label.pack(side="left")

    global intensity_tolerance_entry
    intensity_tolerance_entry = ttk.Entry(threshold_frame)
    intensity_tolerance_entry.pack(side="left", padx=(0, 5))

    region_growing_button = ttk.Button(threshold_frame, text="Run Region Growing", command=start_seed_selection)
    region_growing_button.pack(side="left")


def start_seed_selection():
    root.config(cursor="crosshair")
    canvas.bind("<Button-1>", mark_seed)


def mark_seed(event):
    global seed, data

    x_canvas = event.x
    y_canvas = event.y

    img_coords = canvas.coords(canvas_image_id)
    img_x0, img_y0 = img_coords[0], img_coords[1]

    x_image = int((x_canvas - img_x0 + img_width / 2) * (data.shape[2] / img_width))
    y_image = int((y_canvas - img_y0 + img_height / 2) * (data.shape[1] / img_height))

    slice_num = int(slice_slider.get())

    seed = (slice_num, y_image, x_image)
    print("Seed marked at:", seed, "matrix # rows, cols: ", data.shape[1], data.shape[2])

    root.config(cursor="")
    canvas.unbind("<Button-1>")
    run_region_growing()


def paint_seed_area(data, seed):
    z_seed, y_seed, x_seed = seed
    data[z_seed, y_seed, x_seed] = 255
    print("Pintar el seed")
    plot_nii_slice(z_seed)


def run_region_growing():
    global data, data_segmentated, seed

    if data is not None and seed is not None:
        try:
            intensity_tolerance = int(intensity_tolerance_entry.get())
        except ValueError:
            intensity_tolerance = 10

        data_segmentated = region_growing(data, seed, intensity_tolerance)
        plot_nii_slice(int(slice_slider.get()))



def region_growing(data, seed, intensity_tolerance):
    segmented = np.zeros_like(data)
    stack = [seed]
    region_mean = data[seed]
    region_size = 1

    while stack:
        z, y, x = stack.pop()

        if segmented[z, y, x] == 0:
            if abs(data[z, y, x] - region_mean) <= intensity_tolerance:
                segmented[z, y, x] = 255

                region_size += 1
                region_mean = (region_mean * (region_size - 1) + data[z, y, x]) / region_size

                for i in range(-1, 2):
                    for j in range(-1, 2):
                        for k in range(-1, 2):
                            if 0 <= z + i < data.shape[0] and 0 <= y + j < data.shape[1] and 0 <= x + k < data.shape[2]:
                                stack.append((z + i, y + j, x + k))

    return segmented

def initialize_centers(data, k):
    centers_indices = np.random.choice(data.shape[0], size=k, replace=False)
    centers = data[centers_indices]
    return centers

def assign_clusters(data, centers):

    distances = np.abs(data - centers[:, np.newaxis])
    clusters = np.argmin(distances, axis=0)
    return clusters

def update_centers(data, clusters, k):
    centers = []
    for i in range(k):
        if np.sum(clusters == i) > 0:
            centers.append(np.mean(data[clusters == i]))
        else:
            centers.append(np.random.choice(data))
    return np.array(centers)

def k_means(data, k, max_iterations=100, tol=1e-4):
    centers = initialize_centers(data, k)
    for _ in range(max_iterations):
        old_centers = centers.copy()
        clusters = assign_clusters(data, centers)
        centers = update_centers(data, clusters, k)
        if np.linalg.norm(centers - old_centers) < tol:
            break
    return clusters, centers

def run_k_means():
    global data, data_segmentated
    k_value = int(k_entry.get())

    clusters, centers = k_means(data.flatten(), k_value)
    print("centers: ",centers)
    print("clusters: ",clusters)

    segmented_data = centers[clusters]

    data_segmentated = segmented_data.reshape(data.shape)
    plot_nii_slice(int(slice_slider.get()))

def k_means_clicked(event):
    clear_head()
    k_frame = ttk.Frame(head_frame)
    k_frame.pack(fill="x", padx=10, pady=5)

    k_label = ttk.Label(k_frame, text="K:")
    k_label.pack(side="left")

    global k_entry
    k_entry = ttk.Entry(k_frame)
    k_entry.pack(side="left", padx=(0, 5))

    run_button = ttk.Button(k_frame, text="Run", command=run_k_means)
    run_button.pack(side="left")

def anotar_clicked():
    global draw_color_button

    clear_head()

    color_label = ttk.Label(head_frame, text="Seleccione un color para los trazos:")
    color_label.pack(side="left", padx=10)

    def select_color():
        color = askcolor()[1]
        if color:
            draw_color_button.config(bg=color)

    draw_color_button = tk.Button(head_frame, text="Seleccionar Color", command=select_color)
    draw_color_button.pack(side="left", padx=10)

    export_button = ttk.Button(head_frame, text="Exportar", command=export_image_with_annotations)
    export_button.pack(side="left", padx=10)

    canvas.bind("<B1-Motion>", draw_on_canvas)



def draw_on_canvas(event):
    global canvas_image_id

    x = event.x
    y = event.y

    oval_id = canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=draw_color_button.cget("bg"), outline="")
    canvas.itemconfig(oval_id, tags=("oval",))

def export_image_with_annotations():
    annotated_img = Image.new("RGB", (img_width, img_height), color="white")
    annotated_draw = ImageDraw.Draw(annotated_img)

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    x_offset = (img_width - canvas_width) // 2
    y_offset = (img_height - canvas_height) // 2

    for oval_id in canvas.find_withtag("oval"):
        x0, y0, x1, y1 = canvas.coords(oval_id)
        x0 += x_offset
        y0 += y_offset
        x1 += x_offset
        y1 += y_offset
        color = canvas.itemcget(oval_id, "fill")
        annotated_draw.ellipse([x0, y0, x1, y1], fill=color)

    filename = f"annotated_image_{str(uuid.uuid4())}.png"
    annotated_img.save(filename)

def export_segmentation():
    global data_segmentated

    if data_segmentated is not None:
        filename = filedialog.asksaveasfilename(defaultextension=".nii", filetypes=[("NIfTI files", "*.nii")])
        if filename:
            img = nib.Nifti1Image(data_segmentated, np.eye(4))  # Crear objeto NIfTI
            nib.save(img, filename)
            messagebox.showinfo("Exportación Exitosa", f"Segmentación exportada como {filename}")
        else:
            messagebox.showwarning("Exportación Cancelada", "La exportación fue cancelada.")
    else:
        messagebox.showwarning("No hay Segmentación", "No se ha realizado ninguna segmentación.")




def clear_head():
    for widget in head_frame.winfo_children():
        widget.destroy()


def load_nii_file():
    global nii_file_path, data
    nii_file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii")])
    if nii_file_path:
        img = nib.load(nii_file_path)
        data = img.get_fdata()
        num_slices = img.shape[0]
        slice_slider.config(to=num_slices - 1)
        plot_nii_slice(0)


def restore_original_image():
    global data_segmentated
    data_segmentated = None
    plot_nii_slice(int(slice_slider.get()))


root = tk.Tk()
root.title("Visualizador de Imagen NIfTI")

navbar_frame = ttk.Frame(root, width=200)
navbar_frame.pack(side="left", fill="y")

load_button = ttk.Button(navbar_frame, text="Cargar archivo .nii", command=load_nii_file)
load_button.pack(side="top", padx=10, pady=5)

restore_button = ttk.Button(navbar_frame, text="Recuperar imagen original", command=restore_original_image)
restore_button.pack(side="top", pady=10)

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

region_growing_anchor = ttk.Label(navbar_frame, text="Region Growing", cursor="hand2")
region_growing_anchor.pack(side="top", pady=10)
region_growing_anchor.bind("<Button-1>", lambda event: clear_head() or region_growing_clicked())

k_means_anchor = ttk.Label(navbar_frame, text="K-Means", cursor="hand2")
k_means_anchor.pack(side="top", pady=10)
k_means_anchor.bind("<Button-1>", k_means_clicked)

anotar_anchor = ttk.Label(navbar_frame, text="Anotar", cursor="hand2")
anotar_anchor.pack(side="top", pady=10)
anotar_anchor.bind("<Button-1>", lambda event: anotar_clicked())

export_segmentation_button = ttk.Button(navbar_frame, text="Exportar Segmentación", command=export_segmentation)
export_segmentation_button.pack(side="top", pady=10)

root.mainloop()
