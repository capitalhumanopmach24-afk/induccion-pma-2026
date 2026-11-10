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
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import voz
from bloques import BLOQUES, COMITE

RAIZ = Path(__file__).parent
ASSETS = RAIZ / "assets"
COMP = RAIZ / "componente_presentador"
MEDIA = COMP / "media"
_componente = components.declare_component("presentador_pma", path=str(COMP))



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


def armar_diapositivas(puesto, sede_horario=False, sede_comite=False, bloques=None):
    """Diapositivas = las mismas tarjetas de la app, con la misma narración (y los mismos audios pregenerados)."""
    from organigrama import jefes_de
    out = []
    for bi, b in enumerate(BLOQUES):
        if bloques is not None and bi not in bloques:
            continue
        n = len(b["tarjetas"])
        for ci, t in enumerate(b["tarjetas"]):
            tipo, fotos, clave = t.get("tipo"), [], None
            puntos, titulo, icono = list(t.get("puntos", [])), t["titulo"], t.get("icono", "")
            if tipo == "ficha":
                texto = voz.texto_ficha(puesto)
                clave = voz.con_hash(voz.clave_ficha(puesto["nombre"]), texto)
                titulo, icono = puesto["nombre"], "🪪"
                reporta = ", ".join(puesto["reporta_a"]) if puesto["reporta_a"] else "Dirección de la empresa"
                puntos = [f"Área: {puesto['area']}", puesto["mision"], f"⬆️ **Reportas a:** {reporta}"]
            elif tipo == "marcacion":
                texto = voz.texto_marcacion(puesto.get("marcacion"))
                clave = voz.con_hash(voz.clave_marcacion(puesto.get("marcacion")), texto)
                puntos = list(voz.MARCACION[puesto.get("marcacion")])
            elif tipo == "horario":
                from horarios import grupos_de
                gs = grupos_de(puesto["nombre"]) if sede_horario else []
                texto = voz.texto_horario(gs)
                if not sede_horario:
                    puntos = ["El cuadro de horarios 2026 es de la sede Chimbote. Confirma tu horario con Capital Humano de tu sede."]
                for g in gs:
                    if g["fiscalizado"]:
                        puntos += [f"**{x['turno']}:** lunes a viernes {x['lv']}" + (f", sábado {x['sab']}" if x["sab"] else "") for x in g["turnos"]]
                        puntos.append(g["horas"])
                    else:
                        puntos += ([f"**Hora de ingreso:** {g['ingreso']}"] if g.get("ingreso") else []) + [g["nota"]]
                if not gs and sede_horario and puesto.get("horario") and not puesto.get("provisional_creada"):
                    puntos = list(puesto["horario"])
                titulo, icono = "Tu horario", "🕘"
            elif tipo == "comite":
                texto = voz.texto_comite(t, COMITE)
                clave = voz.con_hash(voz.clave_generica(bi, ci), texto)
                if not sede_comite:
                    puntos.append("Este es el Sub Comité de la sede Chimbote. Pregunta a Capital Humano de tu sede quién integra el comité que te corresponde.")
                fotos = [{"src": _media(ASSETS / "comite" / m["foto"]), "n": m["nombre"], "c": m["cargo"]} for m in COMITE]
            else:
                texto = voz.texto_tarjeta(t)
                clave = voz.con_hash(voz.clave_generica(bi, ci), texto)
                if tipo == "organigrama":
                    jefes = jefes_de(puesto["nombre"])
                    if jefes:
                        puntos.append("⬆️ **Tu línea de mando:** " + " → ".join(jefes))
            audio = voz.ruta_audio(clave) if clave else None
            img = t.get("imagen")
            out.append({
                "bn": bi + 1, "bt": len(BLOQUES), "cn": ci + 1, "ct": n,
                "bloque": f"{b['icono']} {b['titulo']}", "icono": icono, "titulo": html.escape(titulo),
                "puntos": [_negrita(p) for p in puntos], "fotos": fotos, "texto": voz.limpiar(texto),
                "img": _media(ASSETS / "slides" / img) if img else None,
                "audio": _media(audio) if audio else None,
            })
    return out


def mostrar_presentacion(puesto, procesar, sede_horario=False, sede_comite=False, bloques=None, preguntas=True):
    """Dibuja el reproductor y devuelve True cuando la persona llegó a la última tarjeta. `procesar(pregunta, bloque, diapositiva)` es la función de app.py que consulta a Gemini,
    aplica los límites, genera la voz natural y guarda la pregunta en la hoja de Google; devuelve el dict de respuesta."""
    diapos = armar_diapositivas(puesto, sede_horario, sede_comite, bloques)
    ss = st.session_state
    ss.setdefault("pres_ultima", None)
    valor = _componente(slides=diapos, preguntas=bool(preguntas), respuesta=ss.get("pres_resp"), key="presentador", default=None)
    if valor and valor.get("id") != ss.pres_ultima:
        ss.pres_ultima = valor["id"]
        if valor.get("fin"):  # el reproductor llegó a la última tarjeta: se activa el botón de la prueba
            ss["pres_fin"] = True
            st.rerun()
        res = procesar(valor.get("pregunta", ""), valor.get("bloque", ""), valor.get("diapositiva", ""))
        res = dict(res, id=valor["id"], texto=re.sub(r"\*\*(.+?)\*\*", r"\1", res["texto"]))
        ss["pres_resp"] = res
        st.rerun()
    return bool(ss.get("pres_fin"))
