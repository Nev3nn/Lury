"""Imagens dos flashcards: copiadas para a pasta Imagens (ao lado do .exe)."""
import os, shutil, uuid
from tkinter import filedialog, messagebox
import customtkinter as ctk
from storage import BASE

IMG_DIR = os.path.join(BASE, "Imagens")
try:
    from PIL import Image
except ImportError:
    Image = None

def pick():
    """Escolhe uma imagem, copia para Imagens/ e devolve o nome do arquivo (ou None)."""
    if Image is None:
        messagebox.showerror("Imagens", "Instale o Pillow para usar imagens:  pip install pillow"); return None
    p = filedialog.askopenfilename(title="Escolher imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")])
    if not p: return None
    os.makedirs(IMG_DIR, exist_ok=True)
    name = uuid.uuid4().hex[:10] + os.path.splitext(p)[1].lower()
    shutil.copy(p, os.path.join(IMG_DIR, name))
    return name

def load(name, box=(460, 230)):
    if not name or Image is None: return None
    try:
        im = Image.open(os.path.join(IMG_DIR, name)); im.load()
    except Exception:
        return None
    k = min(box[0] / im.width, box[1] / im.height, 1)
    return ctk.CTkImage(light_image=im, dark_image=im, size=(max(1, int(im.width * k)), max(1, int(im.height * k))))

def remove(name):
    try: os.remove(os.path.join(IMG_DIR, name))
    except (OSError, TypeError): pass
