#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector simples de desmatamento / solo exposto usando HSV + morfologia.
- Processa 1 imagem OU uma pasta inteira (recursivo opcional).
- Gera máscara binária, imagem com overlay e um resumo CSV com métricas.
- Permite ajustar limites HSV por argumentos ou arquivo JSON.
- Opcional: usa índice Excess Green (ExG) para separar vegetação / não-vegetação.
Requisitos: Python 3.9+, opencv-python, numpy, matplotlib (opcional para visualização)
Autor: você 😊
"""

import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np
import csv

# ---------- Utils ----------

def parse_lower_upper(s: str):
    """
    Converte string no formato 'H,S,V' para np.array([H,S,V], dtype=np.uint8).
    Ex: '10,50,50' -> array([10,50,50])
    """
    try:
        parts = [int(x.strip()) for x in s.split(",")]
        assert len(parts) == 3
        return np.array(parts, dtype=np.uint8)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Valor inválido para HSV: '{s}'. Use 'H,S,V' (ex: 10,50,50).")


def load_hsv_bounds(args):
    """
    Carrega limites HSV através de argumentos ou JSON.
    Prioridade: --config_json > args diretos > defaults
    """
    # Defaults razoáveis para solo exposto / marrom (ajuste conforme dataset)
    lower = np.array([10, 50, 50], dtype=np.uint8)
    upper = np.array([30, 255, 200], dtype=np.uint8)

    if args.config_json:
        with open(args.config_json, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if "lower_hsv" in cfg and "upper_hsv" in cfg:
            lower = np.array(cfg["lower_hsv"], dtype=np.uint8)
            upper = np.array(cfg["upper_hsv"], dtype=np.uint8)

    if args.lower_hsv is not None:
        lower = args.lower_hsv
    if args.upper_hsv is not None:
        upper = args.upper_hsv

    return lower, upper


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p


def remove_small_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    """
    Remove componentes conectados (8-conectividade) menores que min_area.
    """
    if min_area <= 0:
        return mask
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = np.zeros_like(mask)
    for i in range(1, num):  # 0 é o fundo
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            out[labels == i] = 255
    return out


def compute_exg_mask(bgr: np.ndarray, thresh: float = 0.0) -> np.ndarray:
    """
    Excess Green (ExG) = 2G - R - B.
    Valores altos ~ vegetação; valores baixos ~ não-vegetação/solo.
    Retornamos máscara binária do que NÃO É vegetação (ExG < thresh).
    """
    b, g, r = cv2.split(bgr.astype(np.float32))
    exg = 2 * g - r - b
    # Normaliza para visualização/limiarização estável
    exg_norm = (exg - exg.min()) / (exg.max() - exg.min() + 1e-6)
    non_veg = (exg_norm < thresh).astype(np.uint8) * 255
    return non_veg


def overlay_mask(bgr: np.ndarray, mask: np.ndarray, color=(0, 0, 255), alpha=0.5) -> np.ndarray:
    """
    Sobrepõe a máscara colorida semi-transparente na imagem original.
    color é BGR. alpha é a opacidade do overlay.
    """
    overlay = bgr.copy()
    overlay[mask > 0] = color
    out = cv2.addWeighted(overlay, alpha, bgr, 1 - alpha, 0)
    return out


def compute_metrics(mask: np.ndarray) -> dict:
    total = mask.size
    positive = int((mask > 0).sum())
    coverage = positive / total if total else 0.0
    return {"pixels_total": total, "pixels_desmatado": positive, "percentual": coverage * 100.0}


# ---------- Core ----------

def process_image(
    img_path: Path,
    out_dir: Path,
    lower_hsv: np.ndarray,
    upper_hsv: np.ndarray,
    kernel_open: int,
    kernel_close: int,
    min_component_area: int,
    use_exg: bool,
    exg_thresh: float,
    combine_mode: str,
    save_intermediates: bool,
) -> dict:
    """
    Processa uma única imagem.
    Retorna dict com caminhos e métricas.
    """
    img = cv2.imread(str(img_path))
    if img is None:
        return {"image": str(img_path), "error": "Falha ao carregar."}

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

    if use_exg:
        mask_nonveg = compute_exg_mask(img, thresh=exg_thresh)
        if combine_mode == "and":
            mask = cv2.bitwise_and(mask_hsv, mask_nonveg)
        elif combine_mode == "or":
            mask = cv2.bitwise_or(mask_hsv, mask_nonveg)
        else:
            mask = mask_hsv
    else:
        mask = mask_hsv

    # Morfologia
    if kernel_open > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_open, kernel_open))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    if kernel_close > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_close, kernel_close))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)

    # Remove ruídos pequenos
    mask = remove_small_components(mask, min_component_area)

    # Overlay
    overlay = overlay_mask(img, mask, color=(0, 0, 255), alpha=0.5)

    # Métricas
    metrics = compute_metrics(mask)

    # Salvamento
    rel = img_path.stem
    out_mask = out_dir / f"{rel}_mask.png"
    out_overlay = out_dir / f"{rel}_overlay.png"
    cv2.imwrite(str(out_mask), mask)
    cv2.imwrite(str(out_overlay), overlay)

    # Intermediários opcionais
    saved = {"mask_path": str(out_mask), "overlay_path": str(out_overlay)}
    if save_intermediates:
        out_hsvmask = out_dir / f"{rel}_hsvmask.png"
        cv2.imwrite(str(out_hsvmask), mask_hsv)
        saved["hsv_mask_path"] = str(out_hsvmask)
        if use_exg:
            out_exg = out_dir / f"{rel}_nonveg_exg.png"
            cv2.imwrite(str(out_exg), mask_nonveg)
            saved["nonveg_exg_path"] = str(out_exg)

    return {
        "image": str(img_path),
        **saved,
        **metrics,
        "error": "",
    }


def find_images(root: Path, recursive: bool):
    exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
    if root.is_file():
        yield root
        return
    if recursive:
        for p in root.rglob("*"):
            if p.suffix.lower() in exts:
                yield p
    else:
        for p in root.glob("*"):
            if p.suffix.lower() in exts:
                yield p


def main():
    ap = argparse.ArgumentParser(
        description="Detector simples de desmatamento/solo exposto (HSV + morfologia + ExG opcional)."
    )
    ap.add_argument("input", help="Arquivo de imagem OU pasta com imagens.")
    ap.add_argument("-o", "--output", default="resultados", help="Pasta de saída.")
    ap.add_argument("--recursive", action="store_true", help="Busca recursiva em subpastas.")
    ap.add_argument("--config_json", help="Arquivo JSON com {'lower_hsv':[H,S,V], 'upper_hsv':[H,S,V]}.")
    ap.add_argument("--lower_hsv", type=parse_lower_upper, help="Limite inferior HSV no formato 'H,S,V'.")
    ap.add_argument("--upper_hsv", type=parse_lower_upper, help="Limite superior HSV no formato 'H,S,V'.")
    ap.add_argument("--open", type=int, default=3, dest="kernel_open", help="Kernel (px) de abertura morfológica (0 desliga).")
    ap.add_argument("--close", type=int, default=5, dest="kernel_close", help="Kernel (px) de fechamento morfológico (0 desliga).")
    ap.add_argument("--min_area", type=int, default=200, help="Remove componentes menores que esta área (px). 0 desliga.")
    ap.add_argument("--use_exg", action="store_true", help="Ativa máscara por Excess Green (não-vegetação).")
    ap.add_argument("--exg_thresh", type=float, default=0.4, help="Limiar ExG normalizado para NÃO-vegetação (padrão 0.4).")
    ap.add_argument("--combine", choices=["and", "or", "hsv"], default="and",
                    help="Como combinar HSV e ExG: 'and'(padrão), 'or' ou apenas 'hsv'.")
    ap.add_argument("--save_intermediates", action="store_true", help="Salvar máscaras intermediárias (HSV/ExG).")
    ap.add_argument("--csv_name", default="resumo.csv", help="Nome do arquivo CSV de métricas.")

    args = ap.parse_args()

    in_path = Path(args.input)
    out_dir = ensure_dir(Path(args.output))

    if not in_path.exists():
        print(f"Entrada não encontrada: {in_path}", file=sys.stderr)
        sys.exit(1)

    lower_hsv, upper_hsv = load_hsv_bounds(args)

    # Cabeçalho CSV
    csv_path = out_dir / args.csv_name
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["image", "mask_path", "overlay_path", "pixels_total", "pixels_desmatado", "percentual", "error"])

        count = 0
        for img_path in find_images(in_path, recursive=args.recursive):
            res = process_image(
                img_path=img_path,
                out_dir=out_dir,
                lower_hsv=lower_hsv,
                upper_hsv=upper_hsv,
                kernel_open=args.kernel_open,
                kernel_close=args.kernel_close,
                min_component_area=args.min_area,
                use_exg=args.use_exg,
                exg_thresh=args.exg_thresh,
                combine_mode=args.combine,
                save_intermediates=args.save_intermediates,
            )
            writer.writerow([
                res.get("image", ""),
                res.get("mask_path", ""),
                res.get("overlay_path", ""),
                res.get("pixels_total", ""),
                res.get("pixels_desmatado", ""),
                f"{res.get('percentual', 0.0):.4f}".replace(".", ","),  # vírgula decimal PT-BR
                res.get("error", ""),
            ])
            count += 1

    print(f"Processamento concluído. Resultados em: {out_dir}")
    print(f"CSV resumo: {csv_path}")


if __name__ == "__main__":
    main()
