# desmate_vs_code.py
import sys
import os
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt

# ---------- leitura robusta ----------


def safe_imread(path: str):
    p = Path(path)
    if not p.exists():
        print(f"[ERRO] Caminho não existe: {p}")
        return None
    # tenta normal
    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None:
        try:
            data = np.fromfile(str(p), dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
        except Exception as e:
            print(f"[ERRO] imdecode falhou: {e}")
            return None
    # BGRA->BGR
    if img is not None and img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

# ---------- seleção de arquivo (3 modos) ----------


def ask_path_cli_or_gui():
    # 1) argumento CLI
    if len(sys.argv) > 1:
        return sys.argv[1]

    # 2) tentativa de diálogo Tkinter
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        # traz pra frente
        root.attributes("-topmost", True)
        root.update_idletasks()
        root.lift()
        root.focus_force()

        path = filedialog.askopenfilename(
            parent=root,
            title="Selecione uma imagem",
            filetypes=[
                ("Imagens", ("*.png", "*.jpg", "*.jpeg",
                 "*.tif", "*.tiff", "*.bmp", "*.webp")),
                ("Todos os arquivos", "*.*"),
            ]
        )
        # libera o topmost pra não atrapalhar depois
        try:
            root.after(100, lambda: root.attributes("-topmost", False))
        except Exception:
            pass
        root.destroy()
        if path:
            return path
    except Exception as e:
        print(
            f"[AVISO] Diálogo Tkinter indisponível ({e}). Usando fallback sem GUI.")

    # 3) fallback: pedir no terminal (aceita arrastar/soltar)
    print("\n[SEM GUI] Cole o caminho completo da imagem abaixo")
    print("Dica: você pode ARRASTAR o arquivo para este terminal e pressionar Enter.")
    path = input("Arquivo: ").strip().strip('"')
    return path

# ---------- processamento ----------


def processar_imagem(img_bgr: np.ndarray):
    # limites iniciais (ajuste conforme o dataset)
    lower = np.array([10, 50, 50], dtype=np.uint8)
    upper = np.array([30, 255, 200], dtype=np.uint8)

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

    positivos = int((mask > 0).sum())
    total = mask.size
    perc = (positivos / total * 100.0) if total else 0.0
    print(f"[INFO] Pixels positivos: {positivos}/{total}  ({perc:.4f}%)")
    if perc == 0.0:
        print("[ALERTA] A máscara deu 0%. Tente relaxar limites: H(0–40), S/V mais baixos (ex.: [0,20,20]–[40,255,255]).")

    out = img_bgr.copy()
    out[mask > 0] = [0, 0, 255]  # vermelho BGR
    return mask, out


def main():
    caminho = ask_path_cli_or_gui()
    if not caminho:
        print("[INFO] Nenhum arquivo informado.")
        return

    caminho = os.path.expanduser(caminho)
    print(f"[INFO] Selecionado: {caminho}")

    img = safe_imread(caminho)
    if img is None:
        print("[ERRO] Não foi possível ler a imagem. Verifique o caminho/perm/formato.")
        return
    if img.ndim != 3 or img.shape[2] < 3:
        print(
            f"[ERRO] Formato inesperado (shape={img.shape}). Precisa ser RGB/BGR.")
        return

    print(f"[INFO] Dimensões: {img.shape} (H, W, C)")
    mask, overlay = processar_imagem(img)

    # visualização
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Original")
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.subplot(1, 2, 2)
    plt.title("Detectado (vermelho)")
    plt.imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
