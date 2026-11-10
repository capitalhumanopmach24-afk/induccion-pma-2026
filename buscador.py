# -*- coding: utf-8 -*-
"""Buscador simple sobre conocimiento.json (RIT, RISST, fichas, horarios). Misma interfaz que usa asistente.py:
buscar(pregunta, k, fuentes) y de_puesto(puesto). No necesita librerías externas."""
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

_PARAR = set("de la el los las un una unos unas y o a en que es por para con del al se su sus mi mis tu tus lo le les como cual cuales cuando donde me te si no mas muy ya hay son ser fue".split())


def _norm(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", (t or "").lower()) if not unicodedata.combining(c))
    return [w[:5] for w in re.findall(r"[a-z0-9]+", t) if w not in _PARAR and len(w) > 2]


class BaseLocal:
    def __init__(self, ruta=None):
        ruta = Path(ruta or Path(__file__).parent / "conocimiento.json")
        self.frags = json.loads(ruta.read_text(encoding="utf-8"))
        self._tf = [Counter(_norm(f["texto"] + " " + f.get("seccion", "") + " " + f["ref"])) for f in self.frags]
        df = Counter(w for tf in self._tf for w in tf)
        n = len(self.frags)
        self._idf = {w: math.log(1 + n / c) for w, c in df.items()}

    def buscar(self, pregunta, k=6, fuentes=None):
        q = set(_norm(pregunta))
        if not q:
            return []
        puntos = []
        for f, tf in zip(self.frags, self._tf):
            if fuentes and f["fuente"] not in fuentes:
                continue
            s = sum(self._idf.get(w, 0) * (1 + math.log(tf[w])) for w in q if w in tf)
            if s > 0:
                puntos.append((s, f))
        puntos.sort(key=lambda x: -x[0])
        return [f for _, f in puntos[:k]]

    def de_puesto(self, puesto):
        return [f for f in self.frags if f.get("puesto") == puesto]
