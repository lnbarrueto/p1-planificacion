from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True, slots=True)
class Tarea:
    id_tarea: str
    duracion: int
    categoria: str
    recursos_compatibles: Tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Recurso:
    id_recurso: str
    categorias: frozenset[str]


@dataclass(slots=True)
class Solucion:
    asignacion: List[int]
    tareas_por_recurso: List[List[int]]
    cargas: List[int]
    makespan: int


def leer_recursos(ruta: str) -> Tuple[List[Recurso], Dict[str, List[int]]]:
    recursos: List[Recurso] = []
    categoria_a_recursos: Dict[str, List[int]] = {}

    with open(ruta, "r", encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        for fila in lector:
            datos = [x.strip() for x in fila if x.strip()]
            if not datos:
                continue

            id_recurso = datos[0]
            categorias = frozenset(datos[1:])
            indice = len(recursos)

            recursos.append(Recurso(id_recurso=id_recurso, categorias=categorias))

            for categoria in categorias:
                categoria_a_recursos.setdefault(categoria, []).append(indice)

    return recursos, categoria_a_recursos


def leer_tareas(ruta: str, categoria_a_recursos: Dict[str, List[int]]) -> List[Tarea]:
    tareas: List[Tarea] = []

    with open(ruta, "r", encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        for fila in lector:
            datos = [x.strip() for x in fila if x.strip()]
            if not datos:
                continue

            id_tarea = datos[0]
            duracion = int(datos[1])
            categoria = datos[2]

            if categoria not in categoria_a_recursos:
                raise ValueError(
                    f"La categoría '{categoria}' de la tarea '{id_tarea}' no tiene recursos compatibles."
                )

            recursos_compatibles = tuple(categoria_a_recursos[categoria])

            tareas.append(
                Tarea(
                    id_tarea=id_tarea,
                    duracion=duracion,
                    categoria=categoria,
                    recursos_compatibles=recursos_compatibles,
                )
            )

    return tareas


def calcular_presion_por_categoria(tareas: Sequence[Tarea]) -> Dict[str, float]:
    duracion_total_por_categoria: Dict[str, int] = {}
    cantidad_recursos_por_categoria: Dict[str, int] = {}

    for tarea in tareas:
        duracion_total_por_categoria[tarea.categoria] = (
            duracion_total_por_categoria.get(tarea.categoria, 0) + tarea.duracion
        )
        if tarea.categoria not in cantidad_recursos_por_categoria:
            cantidad_recursos_por_categoria[tarea.categoria] = len(tarea.recursos_compatibles)

    presion: Dict[str, float] = {}
    for categoria, total in duracion_total_por_categoria.items():
        presion[categoria] = total / max(1, cantidad_recursos_por_categoria[categoria])

    return presion


def generar_ordenes_de_tareas(tareas: Sequence[Tarea]) -> List[List[int]]:
    indices = list(range(len(tareas)))
    presion = calcular_presion_por_categoria(tareas)

    orden_1 = sorted(
        indices,
        key=lambda i: (
            -tareas[i].duracion,
            len(tareas[i].recursos_compatibles),
            -presion[tareas[i].categoria],
            tareas[i].id_tarea,
        ),
    )

    orden_2 = sorted(
        indices,
        key=lambda i: (
            len(tareas[i].recursos_compatibles),
            -tareas[i].duracion,
            -presion[tareas[i].categoria],
            tareas[i].id_tarea,
        ),
    )

    orden_3 = sorted(
        indices,
        key=lambda i: (
            -presion[tareas[i].categoria],
            len(tareas[i].recursos_compatibles),
            -tareas[i].duracion,
            tareas[i].id_tarea,
        ),
    )

    orden_4 = sorted(
        indices,
        key=lambda i: (
            -(tareas[i].duracion / len(tareas[i].recursos_compatibles)),
            -tareas[i].duracion,
            tareas[i].id_tarea,
        ),
    )

    return [orden_1, orden_2, orden_3, orden_4]


def copiar_solucion(solucion: Solucion) -> Solucion:
    return Solucion(
        asignacion=solucion.asignacion[:],
        tareas_por_recurso=[lista[:] for lista in solucion.tareas_por_recurso],
        cargas=solucion.cargas[:],
        makespan=solucion.makespan,
    )


def calcular_makespan(cargas: Sequence[int]) -> int:
    return max(cargas) if cargas else 0


def construir_solucion_greedy(
    tareas: Sequence[Tarea],
    recursos: Sequence[Recurso],
    orden_tareas: Sequence[int],
    variante: int,
) -> Solucion:
    cantidad_recursos = len(recursos)
    asignacion = [-1] * len(tareas)
    tareas_por_recurso: List[List[int]] = [[] for _ in range(cantidad_recursos)]
    cargas = [0] * cantidad_recursos

    for posicion, indice_tarea in enumerate(orden_tareas):
        tarea = tareas[indice_tarea]
        mejor_recurso = tarea.recursos_compatibles[0]

        if variante == 0:
            mejor_clave = (
                cargas[mejor_recurso] + tarea.duracion,
                cargas[mejor_recurso],
                len(tareas_por_recurso[mejor_recurso]),
                recursos[mejor_recurso].id_recurso,
            )
            for r in tarea.recursos_compatibles[1:]:
                clave = (
                    cargas[r] + tarea.duracion,
                    cargas[r],
                    len(tareas_por_recurso[r]),
                    recursos[r].id_recurso,
                )
                if clave < mejor_clave:
                    mejor_clave = clave
                    mejor_recurso = r

        elif variante == 1:
            mejor_clave = (
                cargas[mejor_recurso] + tarea.duracion,
                len(recursos[mejor_recurso].categorias),
                cargas[mejor_recurso],
                recursos[mejor_recurso].id_recurso,
            )
            for r in tarea.recursos_compatibles[1:]:
                clave = (
                    cargas[r] + tarea.duracion,
                    len(recursos[r].categorias),
                    cargas[r],
                    recursos[r].id_recurso,
                )
                if clave < mejor_clave:
                    mejor_clave = clave
                    mejor_recurso = r

        elif variante == 2:
            mejor_clave = (
                cargas[mejor_recurso] + tarea.duracion,
                len(tareas_por_recurso[mejor_recurso]),
                cargas[mejor_recurso],
                recursos[mejor_recurso].id_recurso,
            )
            for r in tarea.recursos_compatibles[1:]:
                clave = (
                    cargas[r] + tarea.duracion,
                    len(tareas_por_recurso[r]),
                    cargas[r],
                    recursos[r].id_recurso,
                )
                if clave < mejor_clave:
                    mejor_clave = clave
                    mejor_recurso = r

        else:
            mejor_clave = (
                cargas[mejor_recurso] + tarea.duracion,
                (len(tareas_por_recurso[mejor_recurso]) + posicion) % 7,
                cargas[mejor_recurso],
                recursos[mejor_recurso].id_recurso,
            )
            for r in tarea.recursos_compatibles[1:]:
                clave = (
                    cargas[r] + tarea.duracion,
                    (len(tareas_por_recurso[r]) + posicion) % 7,
                    cargas[r],
                    recursos[r].id_recurso,
                )
                if clave < mejor_clave:
                    mejor_clave = clave
                    mejor_recurso = r

        asignacion[indice_tarea] = mejor_recurso
        tareas_por_recurso[mejor_recurso].append(indice_tarea)
        cargas[mejor_recurso] += tarea.duracion

    makespan = calcular_makespan(cargas)
    return Solucion(
        asignacion=asignacion,
        tareas_por_recurso=tareas_por_recurso,
        cargas=cargas,
        makespan=makespan,
    )


def intentar_reubicacion(
    tareas: Sequence[Tarea],
    solucion: Solucion,
    makespan_objetivo: int,
) -> bool:
    if not solucion.cargas:
        return False

    recurso_mas_cargado = max(range(len(solucion.cargas)), key=solucion.cargas.__getitem__)
    makespan_actual = solucion.cargas[recurso_mas_cargado]

    if makespan_actual <= makespan_objetivo:
        return False

    tareas_candidatas = sorted(
        solucion.tareas_por_recurso[recurso_mas_cargado],
        key=lambda i: tareas[i].duracion,
        reverse=True,
    )[:24]

    recursos_ordenados = sorted(range(len(solucion.cargas)), key=solucion.cargas.__getitem__)[:32]

    mejor_movimiento: Tuple[int, int, int] | None = None

    for indice_tarea in tareas_candidatas:
        tarea = tareas[indice_tarea]
        compatibles = set(tarea.recursos_compatibles)

        for indice_recurso in recursos_ordenados:
            if indice_recurso == recurso_mas_cargado:
                continue
            if indice_recurso not in compatibles:
                continue

            nueva_carga_origen = solucion.cargas[recurso_mas_cargado] - tarea.duracion
            nueva_carga_destino = solucion.cargas[indice_recurso] + tarea.duracion

            nuevo_makespan = 0
            for i, carga in enumerate(solucion.cargas):
                if i == recurso_mas_cargado:
                    carga = nueva_carga_origen
                elif i == indice_recurso:
                    carga = nueva_carga_destino
                if carga > nuevo_makespan:
                    nuevo_makespan = carga

            if nuevo_makespan < makespan_actual:
                movimiento = (nuevo_makespan, indice_tarea, indice_recurso)
                if mejor_movimiento is None or movimiento < mejor_movimiento:
                    mejor_movimiento = movimiento
                    if nuevo_makespan <= makespan_objetivo:
                        break

        if mejor_movimiento is not None and mejor_movimiento[0] <= makespan_objetivo:
            break

    if mejor_movimiento is None:
        return False

    _, indice_tarea, nuevo_recurso = mejor_movimiento
    recurso_anterior = solucion.asignacion[indice_tarea]
    duracion = tareas[indice_tarea].duracion

    solucion.asignacion[indice_tarea] = nuevo_recurso
    solucion.tareas_por_recurso[recurso_anterior].remove(indice_tarea)
    solucion.tareas_por_recurso[nuevo_recurso].append(indice_tarea)
    solucion.cargas[recurso_anterior] -= duracion
    solucion.cargas[nuevo_recurso] += duracion
    solucion.makespan = calcular_makespan(solucion.cargas)

    return True


def intentar_swap(
    tareas: Sequence[Tarea],
    solucion: Solucion,
    makespan_objetivo: int,
) -> bool:
    if not solucion.cargas:
        return False

    recurso_mas_cargado = max(range(len(solucion.cargas)), key=solucion.cargas.__getitem__)
    makespan_actual = solucion.cargas[recurso_mas_cargado]

    if makespan_actual <= makespan_objetivo:
        return False

    tareas_pesadas = sorted(
        solucion.tareas_por_recurso[recurso_mas_cargado],
        key=lambda i: tareas[i].duracion,
        reverse=True,
    )[:16]

    otros_recursos = sorted(
        (r for r in range(len(solucion.cargas)) if r != recurso_mas_cargado),
        key=solucion.cargas.__getitem__,
    )[:20]

    mejor_intercambio: Tuple[int, int, int, int] | None = None

    for indice_tarea_a in tareas_pesadas:
        tarea_a = tareas[indice_tarea_a]
        compatibles_a = set(tarea_a.recursos_compatibles)

        for recurso_b in otros_recursos:
            tareas_b = sorted(solucion.tareas_por_recurso[recurso_b], key=lambda i: tareas[i].duracion)[:12]

            for indice_tarea_b in tareas_b:
                tarea_b = tareas[indice_tarea_b]

                if recurso_b not in compatibles_a:
                    continue
                if recurso_mas_cargado not in set(tarea_b.recursos_compatibles):
                    continue
                if tarea_a.duracion <= tarea_b.duracion:
                    continue

                nueva_carga_a = solucion.cargas[recurso_mas_cargado] - tarea_a.duracion + tarea_b.duracion
                nueva_carga_b = solucion.cargas[recurso_b] - tarea_b.duracion + tarea_a.duracion

                nuevo_makespan = 0
                for i, carga in enumerate(solucion.cargas):
                    if i == recurso_mas_cargado:
                        carga = nueva_carga_a
                    elif i == recurso_b:
                        carga = nueva_carga_b
                    if carga > nuevo_makespan:
                        nuevo_makespan = carga

                if nuevo_makespan < makespan_actual:
                    intercambio = (nuevo_makespan, indice_tarea_a, indice_tarea_b, recurso_b)
                    if mejor_intercambio is None or intercambio < mejor_intercambio:
                        mejor_intercambio = intercambio
                        if nuevo_makespan <= makespan_objetivo:
                            break

            if mejor_intercambio is not None and mejor_intercambio[0] <= makespan_objetivo:
                break

        if mejor_intercambio is not None and mejor_intercambio[0] <= makespan_objetivo:
            break

    if mejor_intercambio is None:
        return False

    _, indice_tarea_a, indice_tarea_b, recurso_b = mejor_intercambio
    recurso_a = recurso_mas_cargado

    solucion.asignacion[indice_tarea_a] = recurso_b
    solucion.asignacion[indice_tarea_b] = recurso_a

    solucion.tareas_por_recurso[recurso_a].remove(indice_tarea_a)
    solucion.tareas_por_recurso[recurso_b].remove(indice_tarea_b)
    solucion.tareas_por_recurso[recurso_a].append(indice_tarea_b)
    solucion.tareas_por_recurso[recurso_b].append(indice_tarea_a)

    duracion_a = tareas[indice_tarea_a].duracion
    duracion_b = tareas[indice_tarea_b].duracion

    solucion.cargas[recurso_a] = solucion.cargas[recurso_a] - duracion_a + duracion_b
    solucion.cargas[recurso_b] = solucion.cargas[recurso_b] - duracion_b + duracion_a
    solucion.makespan = calcular_makespan(solucion.cargas)

    return True


def optimizar_solucion(
    tareas: Sequence[Tarea],
    solucion_inicial: Solucion,
    makespan_objetivo: int,
    tiempo_limite: float,
) -> Solucion:
    mejor = copiar_solucion(solucion_inicial)
    actual = copiar_solucion(solucion_inicial)
    sin_mejora = 0

    while time.perf_counter() < tiempo_limite:
        mejoro = False

        if intentar_reubicacion(tareas, actual, makespan_objetivo):
            mejoro = True
        elif intentar_swap(tareas, actual, makespan_objetivo):
            mejoro = True

        if mejoro:
            sin_mejora = 0
            if actual.makespan < mejor.makespan:
                mejor = copiar_solucion(actual)
                if mejor.makespan <= makespan_objetivo:
                    break
        else:
            sin_mejora += 1
            if sin_mejora >= 3:
                break

    return mejor


def validar_solucion(
    tareas: Sequence[Tarea],
    recursos: Sequence[Recurso],
    solucion: Solucion,
) -> None:
    if len(solucion.asignacion) != len(tareas):
        raise ValueError("La solución no contiene todas las tareas.")

    tareas_vistas = [False] * len(tareas)

    for indice_tarea, indice_recurso in enumerate(solucion.asignacion):
        if indice_recurso < 0 or indice_recurso >= len(recursos):
            raise ValueError("Hay una asignación a recurso inválido.")

        tarea = tareas[indice_tarea]
        recurso = recursos[indice_recurso]

        if tarea.categoria not in recurso.categorias:
            raise ValueError("Se violó la compatibilidad.")

        tareas_vistas[indice_tarea] = True

    if not all(tareas_vistas):
        raise ValueError("No están todas las tareas.")

    for indice_recurso, lista_tareas in enumerate(solucion.tareas_por_recurso):
        suma = 0
        for indice_tarea in lista_tareas:
            if solucion.asignacion[indice_tarea] != indice_recurso:
                raise ValueError("Inconsistencia interna en las asignaciones.")
            suma += tareas[indice_tarea].duracion

        if suma != solucion.cargas[indice_recurso]:
            raise ValueError("Inconsistencia interna en las cargas.")

    if solucion.makespan != calcular_makespan(solucion.cargas):
        raise ValueError("Makespan inconsistente.")


def escribir_output(
    ruta: str,
    tareas: Sequence[Tarea],
    recursos: Sequence[Recurso],
    solucion: Solucion,
) -> None:
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")

        for indice_recurso, lista_tareas in enumerate(solucion.tareas_por_recurso):
            tiempo_actual = 0

            tareas_ordenadas = sorted(
                lista_tareas,
                key=lambda i: (-tareas[i].duracion, tareas[i].id_tarea),
            )

            for indice_tarea in tareas_ordenadas:
                tarea = tareas[indice_tarea]
                tiempo_inicio = tiempo_actual
                tiempo_fin = tiempo_inicio + tarea.duracion

                escritor.writerow([
                    tarea.id_tarea,
                    recursos[indice_recurso].id_recurso,
                    tiempo_inicio,
                    tiempo_fin,
                ])

                tiempo_actual = tiempo_fin


def resolver(
    tareas: Sequence[Tarea],
    recursos: Sequence[Recurso],
    makespan_objetivo: int,
) -> Solucion:
    tiempo_limite_global = time.perf_counter() + 9.7
    mejor_solucion: Solucion | None = None

    for orden in generar_ordenes_de_tareas(tareas):
        for variante in range(4):
            if time.perf_counter() >= tiempo_limite_global:
                break

            candidata = construir_solucion_greedy(tareas, recursos, orden, variante)

            if mejor_solucion is None or candidata.makespan < mejor_solucion.makespan:
                mejor_solucion = candidata

            tiempo_restante = tiempo_limite_global - time.perf_counter()
            if tiempo_restante <= 0:
                break

            tiempo_limite_local = min(
                tiempo_limite_global,
                time.perf_counter() + min(0.60, tiempo_restante * 0.55),
            )

            mejorada = optimizar_solucion(
                tareas=tareas,
                solucion_inicial=candidata,
                makespan_objetivo=makespan_objetivo,
                tiempo_limite=tiempo_limite_local,
            )

            if mejor_solucion is None or mejorada.makespan < mejor_solucion.makespan:
                mejor_solucion = mejorada

    if mejor_solucion is None:
        raise ValueError("No se pudo construir ninguna solución.")

    return mejor_solucion


def leer_makespan_objetivo(argumentos: Sequence[str]) -> int:
    if len(argumentos) < 2:
        return 10**18

    try:
        return int(float(argumentos[1]))
    except ValueError:
        return 10**18


def main() -> None:
    makespan_objetivo = leer_makespan_objetivo(sys.argv)
    tiempo_inicio = time.perf_counter()

    recursos, categoria_a_recursos = leer_recursos("recursos.txt")
    tareas = leer_tareas("tareas.txt", categoria_a_recursos)

    solucion = resolver(
        tareas=tareas,
        recursos=recursos,
        makespan_objetivo=makespan_objetivo,
    )

    validar_solucion(tareas, recursos, solucion)
    escribir_output("output.txt", tareas, recursos, solucion)

    tiempo_total = time.perf_counter() - tiempo_inicio

    print("----- RESULTADOS -----")
    print(f"Cantidad de tareas: {len(tareas)}")
    print(f"Cantidad de recursos: {len(recursos)}")
    print("Archivo generado: output.txt")
    print(f"Makespan obtenido: {solucion.makespan}")
    print(f"Makespan objetivo: {makespan_objetivo}")

    if solucion.makespan <= makespan_objetivo:
        print("Se alcanzó o mejoró el objetivo.")
    else:
        print("No se alcanzó el objetivo.")

    print(f"Tiempo de ejecución: {tiempo_total:.4f} segundos")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
        