from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass(frozen=True)
class Tarea:
    id: str
    duracion: int
    categoria: str  # categoría de la tarea

@dataclass(frozen=True)
class Recurso:
    id: str
    categorias_compatibles: Set[str]

@dataclass(frozen=True)
class Asignacion:
    id_tarea: str
    id_recurso: str
    inicio: int
    fin: int

def leer_tareas(path: str) -> List[Tarea]:

    tareas: List[Tarea] = []

    with open(path, "r", encoding="utf-8") as archivo:   

        for linea in archivo:

            linea = linea.strip()

            if not linea:
                continue

            partes = [p.strip() for p in linea.split(",")]

            tareas.append(
                Tarea(
                    id=partes[0],
                    duracion=int(partes[1]),   
                    categoria=partes[2],
                )
            )

    return tareas

def leer_recursos(path: str) -> List[Recurso]:

    recursos: List[Recurso] = []

    with open(path, "r", encoding="utf-8") as archivo:   

        for linea in archivo:

            linea = linea.strip()

            if not linea:
                continue

            partes = [p.strip() for p in linea.split(",")]

            rid = partes[0]

            categorias = set(partes[1:])

            recursos.append(
                Recurso(
                    id=rid,
                    categorias_compatibles=categorias,
                )
            )

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
        key=lambda t: (
            len(compatibilidad[t.id]),
            -t.duracion,
            t.id,
        ),
    )


def planificar(
    tareas: List[Tarea],
    recursos: List[Recurso],
) -> List[Asignacion]:

    compatibilidad = construir_compatibilidad(tareas, recursos)

    for tarea in tareas:
        if not compatibilidad[tarea.id]:
            raise ValueError(
                f"La tarea {tarea.id} no tiene recursos compatibles"
            )

    tareas_ordenadas = ordenar_tareas(tareas, compatibilidad)

    disponible: Dict[str, int] = {
        recurso.id: 0 for recurso in recursos
    }

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

def escribir_output(path: str, asignaciones: List[Asignacion]) -> None:

    with open(path, "w", encoding="utf-8") as archivo:

        for a in asignaciones:

            archivo.write(
                f"{a.id_tarea},{a.id_recurso},{a.inicio},{a.fin}\n"
            )

def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <makespan_objetivo>")
        sys.exit(1)

    try:
        makespan_objetivo = int(sys.argv[1])
        
        tareas = leer_tareas("tareas.txt")
        recursos = leer_recursos("recursos.txt")

        asignaciones = planificar(tareas, recursos)

        escribir_output("output.txt", asignaciones)
        
        makespan = calcular_makespan(asignaciones)
        
        print(f"Makespan obtenido: {makespan}")
        
        if makespan <= makespan_objetivo:
            print("Cumple el objetivo")
        else:
            print("No cumple el objetivo")

    except Exception as e:
        print(f"Error: {e}")
    
if __name__ == "__main__":
     main()
