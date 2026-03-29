from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Set, Tuple

@dataclass(frozen=True)
class Tarea:
    id: str
    duracion: int
    categoria: str  

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
            recursos.append(
                Recurso(
                    id=partes[0],
                    categorias_compatibles=set(partes[1:]),
                )
            )

    return recursos

def construir_compatibilidad(
    tareas: List[Tarea],
    recursos: List[Recurso],
) -> Dict[str, List[str]]:
    compatibilidad: Dict[str, List[str]] = {}

    for tarea in tareas:
        compatibles: List[str] = []
        for recurso in recursos:
            if tarea.categoria in recurso.categorias_compatibles:
                compatibles.append(recurso.id)
        compatibilidad[tarea.id] = compatibles

    return compatibilidad

def calcular_makespan(asignaciones: List[Asignacion]) -> int:
    if not asignaciones:
        return 0
    return max(a.fin for a in asignaciones)

def escribir_output(path: str, asignaciones: List[Asignacion]) -> None:
    salida = sorted(
        asignaciones,
        key=lambda a: (a.inicio, a.id_recurso, a.id_tarea),
    )

    with open(path, "w", encoding="utf-8") as archivo:
        for a in salida:
            archivo.write(f"{a.id_tarea},{a.id_recurso},{a.inicio},{a.fin}\n")

def heuristica_restrictivas_largas(
    tarea: Tarea,
    compatibilidad: Dict[str, List[str]],
) -> Tuple[int, int, str]:
    return (len(compatibilidad[tarea.id]), -tarea.duracion, tarea.id)


def heuristica_largas_restrictivas(
    tarea: Tarea,
    compatibilidad: Dict[str, List[str]],
) -> Tuple[int, int, str]:
    return (-tarea.duracion, len(compatibilidad[tarea.id]), tarea.id)


def heuristica_spt_restrictiva(
    tarea: Tarea,
    compatibilidad: Dict[str, List[str]],
) -> Tuple[int, int, str]:
    return (tarea.duracion, len(compatibilidad[tarea.id]), tarea.id)


def heuristica_ratio_duracion_compatibilidad(
    tarea: Tarea,
    compatibilidad: Dict[str, List[str]],
) -> Tuple[float, int, str]:
    return (-(tarea.duracion / len(compatibilidad[tarea.id])), -tarea.duracion, tarea.id)

def ordenar_tareas(
    tareas: List[Tarea],
    compatibilidad: Dict[str, List[str]],
    criterio: Callable[[Tarea, Dict[str, List[str]]], Tuple[object, ...]],
) -> List[Tarea]:
    return sorted(tareas, key=lambda t: criterio(t, compatibilidad))

def planificar_greedy(
    tareas: List[Tarea],
    recursos: List[Recurso],
    criterio_orden: Callable[[Tarea, Dict[str, List[str]]], Tuple[object, ...]],
) -> List[Asignacion]:
    compatibilidad = construir_compatibilidad(tareas, recursos)

    for tarea in tareas:
        if not compatibilidad[tarea.id]:
            raise ValueError(f"La tarea {tarea.id} no tiene recursos compatibles.")

    tareas_ordenadas = ordenar_tareas(tareas, compatibilidad, criterio_orden)

    disponible: Dict[str, int] = {recurso.id: 0 for recurso in recursos}
    carga: Dict[str, int] = {recurso.id: 0 for recurso in recursos}
    asignaciones: List[Asignacion] = []

    for tarea in tareas_ordenadas:
        compatibles = compatibilidad[tarea.id]

        mejor_recurso = min(
            compatibles,
            key=lambda rid: (
                disponible[rid] + tarea.duracion,  
                carga[rid],                        
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
        carga[mejor_recurso] += tarea.duracion

    return asignaciones

def reconstruir_desde_orden(
    tareas_ordenadas: List[Tarea],
    compatibilidad: Dict[str, List[str]],
) -> List[Asignacion]:
    recursos_ids = sorted({rid for lista in compatibilidad.values() for rid in lista})
    disponible: Dict[str, int] = {rid: 0 for rid in recursos_ids}
    carga: Dict[str, int] = {rid: 0 for rid in recursos_ids}
    asignaciones: List[Asignacion] = []

    for tarea in tareas_ordenadas:
        compatibles = compatibilidad[tarea.id]

        mejor_recurso = min(
            compatibles,
            key=lambda rid: (
                disponible[rid] + tarea.duracion,
                carga[rid],
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
        carga[mejor_recurso] += tarea.duracion

    return asignaciones

def mejora_local_por_swap(
    tareas: List[Tarea],
    recursos: List[Recurso],
    plan_inicial: List[Asignacion],
) -> List[Asignacion]:

    compatibilidad = construir_compatibilidad(tareas, recursos)

    tarea_por_id: Dict[str, Tarea] = {t.id: t for t in tareas}
    orden_actual: List[Tarea] = [tarea_por_id[a.id_tarea] for a in plan_inicial]
    mejor_plan = plan_inicial
    mejor_makespan = calcular_makespan(mejor_plan)

    mejoro = True
    while mejoro:
        mejoro = False
        for i in range(len(orden_actual) - 1):
            nuevo_orden = orden_actual[:]
            nuevo_orden[i], nuevo_orden[i + 1] = nuevo_orden[i + 1], nuevo_orden[i]

            candidato = reconstruir_desde_orden(nuevo_orden, compatibilidad)
            candidato_makespan = calcular_makespan(candidato)

            if candidato_makespan < mejor_makespan:
                orden_actual = nuevo_orden
                mejor_plan = candidato
                mejor_makespan = candidato_makespan
                mejoro = True
                break

    return mejor_plan

def elegir_mejor_plan(
    tareas: List[Tarea],
    recursos: List[Recurso],
) -> List[Asignacion]:
    criterios = [
        heuristica_restrictivas_largas,
        heuristica_largas_restrictivas,
        heuristica_spt_restrictiva,
        heuristica_ratio_duracion_compatibilidad,
    ]

    mejor_plan: List[Asignacion] = []
    mejor_makespan: int | None = None

    for criterio in criterios:
        plan = planificar_greedy(tareas, recursos, criterio)
        plan = mejora_local_por_swap(tareas, recursos, plan)
        makespan = calcular_makespan(plan)

        if mejor_makespan is None or makespan < mejor_makespan:
            mejor_makespan = makespan
            mejor_plan = plan

    return mejor_plan

def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python main.py <makespan_objetivo>")
        sys.exit(1)

    try:
        makespan_objetivo = int(sys.argv[1])
    except ValueError:
        print("Error: <makespan_objetivo> debe ser un entero.")
        sys.exit(1)

    tareas = leer_tareas("tareas.txt")
    recursos = leer_recursos("recursos.txt")

    asignaciones = elegir_mejor_plan(tareas, recursos)
    escribir_output("output.txt", asignaciones)

    makespan = calcular_makespan(asignaciones)

    print("✅ Se generó output.txt correctamente.")
    print(f"Makespan obtenido: {makespan}")
    print(f"Makespan objetivo: {makespan_objetivo}")

    if makespan <= makespan_objetivo:
        print("✅ Se alcanzó o mejoró el objetivo.")
    else:
        print("⚠️ La solución es válida, pero no alcanzó el objetivo.")


if __name__ == "__main__":
    main()