from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


# Tarea guarda el identificador, duración y categoría
# Recurso guarda el identificador y categorías compatibles
# Asignacion guarda el resultado final
# frozen=True hace que los objetos sean inmutables

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


# Esta función lee el archivo de tareas y devuelve una lista de objetos Tarea
def leer_tareas(path: str) -> List[Tarea]:

    # lista donde guardaremos todas las tareas
    tareas: List[Tarea] = []

    # abrimos el archivo en modo lectura
    with open(path, "r", encoding="utf-8") as archivo:   # ← corregido utf-8

        # recorremos cada línea del archivo
        for linea in archivo:

            # quitamos espacios y saltos de línea al inicio y final
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea:
                continue

            # separamos la línea por coma
            partes = [p.strip() for p in linea.split(",")]

            # creamos la tarea con id, duración y categoría
            tareas.append(
                Tarea(
                    id=partes[0],
                    duracion=int(partes[1]),   # ← corregido (sin tilde)
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
    with open(path, "r", encoding="utf-8") as archivo:   # ← corregido utf-8

        # recorremos cada línea del archivo
        for linea in archivo:

            # quitamos espacios y saltos de línea
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea:
                continue

            partes = [p.strip() for p in linea.split(",")]

            # el primer elemento es el id del recurso
            rid = partes[0]

            # el resto son categorías compatibles
            categorias = set(partes[1:])

            # creamos el objeto recurso
            recursos.append(
                Recurso(
                    id=rid,
                    categorias_compatibles=categorias,
                )
            )

    # devolvemos la lista completa
    return recursos


# Construye un diccionario que dice qué recursos sirven para cada tarea
def construir_compatibilidad(
    tareas: List[Tarea], recursos: List[Recurso]
) -> Dict[str, List[str]]:

    compatibilidad: Dict[str, List[str]] = {}

    for tarea in tareas:

        compatibles: List[str] = []

        for recurso in recursos:

            # si la categoría de la tarea está en las compatibles del recurso
            if tarea.categoria in recurso.categorias_compatibles:
                compatibles.append(recurso.id)

        compatibilidad[tarea.id] = compatibles

    return compatibilidad


# Ordena tareas:
# primero las que tienen menos recursos compatibles
# luego las más largas
# luego por id para estabilidad
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


# Algoritmo principal de planificación
def planificar(
    tareas: List[Tarea],
    recursos: List[Recurso],
) -> List[Asignacion]:

    # construimos compatibilidad tarea → recursos posibles
    compatibilidad = construir_compatibilidad(tareas, recursos)

    # verificamos que cada tarea tenga al menos un recurso compatible
    for tarea in tareas:
        if not compatibilidad[tarea.id]:
            raise ValueError(
                f"La tarea {tarea.id} no tiene recursos compatibles"
            )

    # ordenamos tareas con la heurística
    tareas_ordenadas = ordenar_tareas(tareas, compatibilidad)

    # diccionario con disponibilidad de cada recurso
    disponible: Dict[str, int] = {
        recurso.id: 0 for recurso in recursos
    }

    asignaciones: List[Asignacion] = []

    # asignamos tarea por tarea
    for tarea in tareas_ordenadas:

        compatibles = compatibilidad[tarea.id]

        # elegimos el recurso que termina antes
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

        # guardamos asignación
        asignaciones.append(
            Asignacion(
                id_tarea=tarea.id,
                id_recurso=mejor_recurso,
                inicio=inicio,
                fin=fin,
            )
        )

        # actualizamos disponibilidad
        disponible[mejor_recurso] = fin

    return asignaciones


# Calcula el makespan = máximo tiempo de término
def calcular_makespan(asignaciones: List[Asignacion]) -> int:

    if not asignaciones:
        return 0

    return max(a.fin for a in asignaciones)

# Escribe el resultado en output.txt
def escribir_output(path: str, asignaciones: List[Asignacion]) -> None:

    with open(path, "w", encoding="utf-8") as archivo:

        for a in asignaciones:

            archivo.write(
                f"{a.id_tarea},{a.id_recurso},{a.inicio},{a.fin}\n"
            )
def main():

    # Verificamos que se haya pasado el makespan objetivo
    if len(sys.argv) != 2:
        print("Uso: python main.py <makespan_objetivo>")
        sys.exit(1)

    # Convertimos el argumento a entero
    try:
        makespan_objetivo = int(sys.argv[1])
    except ValueError:
        print("Error: el makespan objetivo debe ser un numero")
        sys.exit(1)

    # Leer archivos
    tareas = leer_tareas("tareas.txt")
    recursos = leer_recursos("recursos.txt")

    # Planificar
    asignaciones = planificar(tareas, recursos)

    # Escribir salida
    escribir_output("output.txt", asignaciones)

    # Calcular makespan
    makespan = calcular_makespan(asignaciones)

    print("Makespan obtenido:", makespan)
    print("Makespan objetivo:", makespan_objetivo)


if __name__ == "__main__":
    main()