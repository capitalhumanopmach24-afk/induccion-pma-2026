# -*- coding: utf-8 -*-
"""
Presentación guiada de la inducción con preguntas al asistente.

  - Cada diapositiva se narra sola (audio natural pregenerado en assets/audio, o voz del dispositivo) y pasa a la siguiente.
  - Se puede pausar, retroceder, avanzar, reiniciar y PREGUNTAR: la presentación se pausa, Gemini responde con el RIT/RISST/fichas
    (asistente.py), la respuesta se lee con voz natural (voz_ia.py) y se guarda en la hoja de Google (registro_preguntas.py).
"""
import html
import re
import shutil
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import asistente
import registro_preguntas
import voz
import voz_ia
from bloques import BLOQUES, COMITE
from buscador import BaseLocal

RAIZ = Path(__file__).parent
ASSETS = RAIZ / "assets"
COMP = RAIZ / "componente_presentador"
MEDIA = COMP / "media"
_componente = components.declare_component("presentador_pma", path=str(COMP))
MAX_PREGUNTAS, ESPERA_S = 8, 4


@st.cache_resource
def base_conocimiento():
    return BaseLocal()


def _media(ruta):
    """Copia el archivo a la carpeta del componente (que es la que sirve Streamlit) y devuelve su URL relativa."""
    ruta = Path(ruta)
    if not ruta.exists():
        return None
    MEDIA.mkdir(exist_ok=True)
    destino = MEDIA / f"{ruta.parent.name}_{ruta.name}"
    if not destino.exists() or destino.stat().st_size != ruta.stat().st_size:
        shutil.copyfile(ruta, destino)
    return f"media/{destino.name}"


def _negrita(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))


def armar_diapositivas(puesto=None, bloques=None):
    out = []
    for bi, b in enumerate(BLOQUES):
        if bloques is not None and bi not in bloques:
            continue
        for ci, t in enumerate(b["tarjetas"]):
            tipo, fotos = t.get("tipo"), []
            puntos, clave = list(t.get("puntos", [])), voz.clave_generica(bi, ci)
            if tipo == "horario":
                continue  # depende del puesto y del cuadro de horarios: se ve en la app
            if tipo == "ficha":
                if not puesto:
                    continue
                texto, clave = voz.texto_ficha(puesto), voz.clave_ficha(puesto["nombre"])
                puntos = [f"Puesto: {puesto['nombre']} · Área: {puesto['area']}"] + (
                    ["Reportas a " + " y ".join(puesto["reporta_a"])] if puesto.get("reporta_a") else [])
            elif tipo == "marcacion":
                texto, clave, puntos = voz.texto_marcacion(None), voz.clave_marcacion(None), voz.MARCACION[None]
            elif tipo == "comite":
                texto = voz.texto_comite(t, COMITE)
                fotos = [{"src": _media(ASSETS / "comite" / m["foto"]), "n": m["nombre"], "c": m["cargo"]} for m in COMITE]
            else:
                texto = voz.texto_tarjeta(t)
            audio = voz.ruta_audio(voz.con_hash(clave, texto))
            img = t.get("imagen")
            out.append({
                "bloque": f"{b['icono']} {b['titulo']}", "icono": t.get("icono", ""), "titulo": html.escape(t["titulo"]),
                "puntos": [_negrita(p) for p in puntos], "fotos": fotos, "texto": texto,
                "img": _media(ASSETS / "slides" / img) if img else None,
                "audio": _media(audio) if audio else None,
            })
    return out


def _secreto(nombre, defecto=""):
    try:
        return str(st.secrets.get(nombre, defecto))
    except Exception:  # noqa: BLE001
        return defecto


def mostrar_presentacion(puesto=None, bloques=None, sede="Chimbote"):
    """Dibuja el reproductor y atiende las preguntas. `puesto` es el dict de puestos.json (o None)."""
    clave = _secreto("GEMINI_API_KEY")
    diapos = armar_diapositivas(puesto, bloques)
    ss = st.session_state
    ss.setdefault("pres_n", 0)
    ss.setdefault("pres_ultimo_t", 0.0)
    ss.setdefault("pres_ultima", None)
    valor = _componente(slides=diapos, preguntas=bool(clave), respuesta=ss.get("pres_resp"), key="presentador", default=None)
    if not clave:
        st.caption("Las preguntas están desactivadas: falta GEMINI_API_KEY en los Secrets.")
    if valor and valor.get("id") != ss.pres_ultima:
        ss.pres_ultima = valor["id"]
        nombre_puesto = puesto["nombre"] if puesto else None
        pregunta = asistente.limpiar_pregunta(valor.get("pregunta", ""))
        if ss.pres_n >= MAX_PREGUNTAS:
            res = {"tipo": "limite", "texto": f"Ya hiciste {MAX_PREGUNTAS} preguntas en esta sesión. Consulta lo demás con Capital Humano.", "fuentes": []}
        elif time.time() - ss.pres_ultimo_t < ESPERA_S:
            res = {"tipo": "error", "texto": "Espera unos segundos antes de hacer otra pregunta.", "fuentes": []}
        else:
            ss.pres_n += 1
            ss.pres_ultimo_t = time.time()
            res = asistente.preguntar(
                pregunta, nombre_puesto, sede, base_conocimiento(), clave, modelo=_secreto("GEMINI_MODELO") or None,
                tope_dia=int(_secreto("PREGUNTAS_POR_DIA", "300")))
            if res["tipo"] in ("ia", "fija") and _secreto("VOZ_RESPUESTAS", "si").lower() != "no":
                res["audio"] = voz_ia.sintetizar(res["texto"], clave)
            res["hablado"] = voz_ia.texto_hablado(res["texto"])
            registro_preguntas.guardar(_secreto("HOJA_URL"), _secreto("HOJA_TOKEN"), sede, nombre_puesto,
                                       valor.get("bloque"), valor.get("diapositiva"), pregunta, res)
        res["id"] = valor["id"]
        res["texto"] = re.sub(r"\*\*(.+?)\*\*", r"\1", res["texto"])
        ss["pres_resp"] = res
        st.rerun()
    return len(diapos)
