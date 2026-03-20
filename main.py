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
from typing import List


# Esta función lee el archivo de tareas y devuelve una lista de objetos Tarea
def leer_tareas(path: str) -> List[Tarea]:

    # lista donde guardaremos todas las tareas
    tareas = []

    # abrimos el archivo en modo lectura
    with open(path) as f:

        # recorremos cada línea del archivo
        for linea in f:

            # quitamos espacios y saltos de línea al inicio y final
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if linea == "":
                continue

            # separamos la línea por coma
            # ejemplo: "T1,5" -> ["T1", "5"]
            partes = linea.split(",")

            # el primer elemento es el id de la tarea
            tid = partes[0]

            # el segundo elemento es la duración (lo convertimos a int)
            dur = int(partes[1])

            # creamos un objeto Tarea con esos datos
            tarea = Tarea(tid, dur)

            # agregamos la tarea a la lista
            tareas.append(tarea)

    # devolvemos la lista completa de tareas
    return tareas