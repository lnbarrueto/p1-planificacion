from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

#Tarea guarda el identificador y la duración
#Recurso guarda el identificador y cuándo queda libre
#@dataclass hace más fácil crear objetos sin escribir tanto código
#frozen=True hace que los objetos sean inmutables

@dataclass(frozen=True)
class Tarea:
    id: str
    duracion: int
    categoria:str #Añadimos para saber que categoria es


@dataclass(frozen=True)
class Recurso:
    id: str
    categorias_compatibles:Set[str]
    

@dataclass(frozen=True)
class Asignacion:
    id_tarea: str
    id_recurso: str
    inicio: int
    fin: int

# Esta función lee el archivo de tareas y devuelve una lista de objetos Tarea
def leer_tareas(path: str) -> List[Tarea]:

    # lista donde guardaremos todas las tareas
    tareas: List[Tarea] = []

    # abrimos el archivo en modo lectura
    with open(path, "r",encoding="uft-8") as archivo:

        # recorremos cada línea del archivo
        for linea in archivo:

            # quitamos espacios y saltos de línea al inicio y final
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea: 
                continue

            # separamos la línea por coma
            # ejemplo: "T1,5" -> ["T1", "5"]
            partes = [p.strip() for p in linea.split(",")]

            # el primer elemento es el id de la tarea
            tareas.append(
                Tarea(
                    id=partes[0], 
                    duración=int(partes[1]), 
                    categoria=partes[2],
                )
            )

    # devolvemos la lista completa de tareas
    return tareas

# Esta función lee el archivo de recursos y devuelve una lista de objetos Recurso
def leer_recursos(path: str) -> List[Recurso]:

    # lista donde guardaremos los recursos
    recursos: List[Recurso] = []

    # abrimos el archivo en modo lectura
    with open(path,"r", encoding="uft-8") as archivo:

        # recorremos cada línea del archivo
        for linea in archivo:

            # quitamos espacios y saltos de línea
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea: 
                continue

            partes = [p.strip() for p in linea.split(",")]

            # la línea contiene el id del recurso
            rid = partes[0]

            # creamos un objeto Recurso
            categorias = set(partes[1:])

            # lo agregamos a la lista
            recursos.append(
                Recurso(
                    id=rid,
                    categorias_compatibles=categorias,
                )
            )

    # devolvemos la lista completa
    return recursos


def construir_compatibilidad(
    tareas: List[Tarea], recursos: List[Recurso]
) -> Dict[str, List[str]]:
    compatibilidad: Dict[str, List[str]] = {}

    for tarea in tareas: 
        compatibles: List[str] = []
        for recurso in recursos: 
            if tarea.categoria in recurso.categorias_compatibles:
                compatibles.append(recurso.id)

        compatibilidad[tarea.id] = compatibles

    return compatibilidad
    

def ordenar_tareas(
        tareas: List[Tarea],
        compatibilidad: Dict[str, List[str]],
) -> List[Tarea]:
    
    return sorted(
        tareas,
        key=lambda t: (len(compatibilidad[t.id]), -t.duracion, t.id),                   
    )



def planificar(tareas: List[Tarea], recursos: List[Recurso]) -> List[Asignacion]:
    compatibilidad = construir_compatibilidad(tareas, recursos)

    for tarea in tareas:
        if not compatibilidad[tarea.id]:
            raise ValueError(
                f"La tarea {tarea.id} no tiene recursos compatibles"
            )

    tareas_ordenadas = ordenar_tareas(tareas, compatibilidad)
    disponible: Dict[str, int] = {recurso.id: 0 for recurso in recursos}

    asignaciones: List[Asignacion] = []

    for tarea in tareas_ordenadas:
        compatibles = compatibilidad[tarea.id]

       
        mejor_recurso = min(
            compatibles,
            key=lambda rid: (
                disponible[rid] + tarea.duracion,
                disponible[rid],
                rid,
            ),
        )

        inicio = disponible[mejor_recurso]
        fin = inicio + tarea.duracion

        asignaciones.append(
            Asignacion(
                id_tarea=tarea.id,
                id_recurso=mejor_recurso,
                inicio=inicio,
                fin=fin,
            )
        )

        disponible[mejor_recurso] = fin

    return asignaciones

    
def calcular_makespan(asignaciones: List[Asignacion]) -> int:
    if not asignaciones:
        return 0
    return max(a.fin for a in asignaciones)
