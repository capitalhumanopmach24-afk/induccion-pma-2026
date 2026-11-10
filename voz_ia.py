# -*- coding: utf-8 -*-
"""Voz natural para las RESPUESTAS del asistente (las diapositivas usan audios pregenerados, ver generar_audios_presentacion.py).
Orden: 1) voz de Gemini (usa tu misma clave)  2) edge-tts (es-PE-CamilaNeural) si está instalado  3) None -> voz del navegador."""
import base64
import io
import re
import wave

import asistente
import voz

VOZ_GEMINI = "Kore"          # otras: Puck, Charon, Aoede, Leda, Zephyr...
VOZ_EDGE = "es-PE-CamilaNeural"


def texto_hablado(texto):
    t = re.sub(r"\([^)]*\)", "", texto or "")      # quita las citas «(RIT, Art. 53)»
    return voz.limpiar(t)[:900]


def _modelo_tts(clave):
    estado, datos = asistente._http("GET", f"{asistente.URL_GEMINI}/v1beta/models?pageSize=200", clave)
    if estado != 200:
        return None
    nombres = [m["name"].replace("models/", "") for m in datos.get("models", [])
               if "tts" in m.get("name", "") and "generateContent" in m.get("supportedGenerationMethods", [])]
    nombres.sort(key=lambda n: ("flash" not in n, "preview" in n))
    return nombres[0] if nombres else None


def _wav(pcm, hz=24000):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(hz), w.writeframes(pcm)
    return b.getvalue()


def _gemini(texto, clave, modelo=None):
    modelo = modelo or _modelo_tts(clave)
    if not modelo:
        return None, None
    cuerpo = {"contents": [{"parts": [{"text": "Di con voz cálida, natural y pausada, en español peruano: " + texto}]}],
              "generationConfig": {"responseModalities": ["AUDIO"],
                                   "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOZ_GEMINI}}}}}
    estado, datos = asistente._http("POST", f"{asistente.URL_GEMINI}/v1beta/models/{modelo}:generateContent", clave, cuerpo, timeout=40)
    try:
        pcm = base64.b64decode(datos["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        return _wav(pcm), "audio/wav"
    except (KeyError, IndexError, TypeError, ValueError):
        return None, None


def _edge(texto):
    try:
        import asyncio
        import edge_tts

        async def go():
            buf = b""
            async for ch in edge_tts.Communicate(texto, VOZ_EDGE).stream():
                if ch["type"] == "audio":
                    buf += ch["data"]
            return buf
        datos = asyncio.run(go())
        return (datos, "audio/mpeg") if datos else (None, None)
    except Exception:  # noqa: BLE001
        return None, None


def sintetizar(texto, clave_gemini=None, modelo_tts=None):
    """Devuelve un data-URI de audio o None (entonces el navegador usa su propia voz)."""
    t = texto_hablado(texto)
    if not t:
        return None
    datos, mime = (None, None)
    if clave_gemini:
        datos, mime = _gemini(t, clave_gemini, modelo_tts)
    if not datos:
        datos, mime = _edge(t)
    return f"data:{mime};base64," + base64.b64encode(datos).decode() if datos else None
