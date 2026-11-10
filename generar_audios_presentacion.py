# -*- coding: utf-8 -*-
"""Genera UNA vez los audios naturales de todas las diapositivas (voz neuronal es-PE-CamilaNeural, gratis, con edge-tts).
Uso (en tu laptop, dentro de esta carpeta):
    pip install -r requirements_audio.txt
    python generar_audios_presentacion.py            (genera los que faltan; si falla, repítelo y continúa)
    python generar_audios_presentacion.py --voz es-MX-DaliaNeural
    python generar_audios_presentacion.py --listar
Luego sube assets/audio a GitHub. Si cambias un texto, solo se vuelve a generar ese audio."""
import argparse
import asyncio
import json
import time
from pathlib import Path

import edge_tts

import voz
from bloques import BLOQUES, COMITE


async def main(a):
    if a.listar:
        for v in await edge_tts.list_voices():
            if v["Locale"].startswith("es-"):
                print(v["ShortName"], v["Gender"])
        return
    puestos = json.loads((Path(__file__).parent / "puestos.json").read_text(encoding="utf-8"))
    voz.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    items = voz.elementos_audio(BLOQUES, puestos, COMITE)
    for n, (clave, texto) in enumerate(items, 1):
        destino = voz.AUDIO_DIR / f"{clave}.mp3"
        if destino.exists():
            continue
        try:
            await edge_tts.Communicate(voz.limpiar(texto), a.voz, rate=a.velocidad).save(str(destino))
            print(f"[{n}/{len(items)}] {clave}")
        except Exception as e:  # noqa: BLE001
            print(f"[{n}/{len(items)}] FALLÓ {clave}: {e}. Espera un poco o cambia de red y repite.")
            destino.unlink(missing_ok=True)
            return
        time.sleep(1.2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--voz", default="es-PE-CamilaNeural")
    p.add_argument("--velocidad", default="-5%")
    p.add_argument("--listar", action="store_true")
    asyncio.run(main(p.parse_args()))
