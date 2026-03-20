from __future__ import annotations
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

#Tarea guarda el identificador y la duración
#Recurso guarda el identificador y cuándo queda libre
#@dataclass hace más fácil crear objetos sin escribir tanto código

@dataclass
class Tarea:
    id: str
    duracion: int


@dataclass
class Recurso:
    id: str
    disponible: int = 0