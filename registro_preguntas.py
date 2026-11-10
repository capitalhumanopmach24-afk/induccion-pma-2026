# -*- coding: utf-8 -*-
"""Guarda cada pregunta y respuesta del asistente en la hoja de Google (pestaña «preguntas», vía Apps Script de envio.py)
y, como respaldo, en data/preguntas.csv. No guarda el nombre del trabajador. Si la pregunta tocó un tema sensible
(hostigamiento, violencia, daño personal) NO se guarda el texto de la pregunta."""
import csv
from datetime import datetime
from pathlib import Path

import envio

ENCABEZADO = ["fecha", "sede", "puesto", "bloque", "diapositiva", "pregunta", "respuesta", "fuentes", "tipo", "modelo"]
CSV = Path(__file__).parent / "data" / "preguntas.csv"


def guardar(url, token, sede, puesto, bloque, diapositiva, pregunta, res):
    """Devuelve (ok_hoja, mensaje). El respaldo local se intenta siempre."""
    sensible = res.get("tipo") == "fija"
    fila = [
        datetime.now().isoformat(timespec="seconds"), sede or "", puesto or "", bloque or "", diapositiva or "",
        "[tema sensible: texto no guardado]" if sensible else pregunta,
        "[respuesta fija de orientación]" if sensible else res.get("texto", ""),
        "; ".join(res.get("fuentes", [])), res.get("tipo", ""), res.get("modelo", ""),
    ]
    try:
        CSV.parent.mkdir(exist_ok=True)
        nuevo = not CSV.exists()
        with CSV.open("a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if nuevo:
                w.writerow(ENCABEZADO)
            w.writerow(fila)
    except OSError:
        pass
    if not url:
        return False, "Sin HOJA_URL: solo se guardó el respaldo local."
    return envio.enviar_apps_script(url, token, [{"hoja": "preguntas", "encabezado": ENCABEZADO, "filas": [fila]}])
