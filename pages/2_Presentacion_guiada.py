# -*- coding: utf-8 -*-
"""Página extra: presentación guiada y automática de la inducción (aparece sola en la barra lateral)."""
import json
from pathlib import Path

import streamlit as st

from bloques import BLOQUES
from presentador import mostrar_presentacion

st.title("🎬 Inducción guiada")
puestos = json.loads((Path(__file__).parent.parent / "puestos.json").read_text(encoding="utf-8"))
nombres = ["(sin puesto: omitir la ficha)"] + [p["nombre"] for p in puestos]
elegido = st.selectbox("Tu puesto", nombres)
puesto = next((p for p in puestos if p["nombre"] == elegido), None)
sel = st.multiselect("Bloques a presentar", range(len(BLOQUES)), default=list(range(len(BLOQUES))),
                     format_func=lambda i: f"{BLOQUES[i]['icono']} {BLOQUES[i]['titulo']}")
if sel:
    mostrar_presentacion(puesto, sel)
