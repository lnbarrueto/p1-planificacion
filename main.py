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

    presion = calcular_presion_por_categoria(tareas)

    orden_maestro = sorted(
        range(len(tareas)),
        key=lambda i: (
            presion[tareas[i].categoria],
            tareas[i].duracion,  # Agregamos coma
            tareas[i].id_tarea   # Quitamos el paréntesis de arriba y lo ponemos aquí
        ), 
        reverse=True
    )
    return [orden_maestro]#Con uno bueno basta, ahorrar CPU


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
) -> Solucion:
    cantidad_recursos = len(recursos)
    asignacion = [-1] * len(tareas)
    tareas_por_recurso = [[] for _ in range(cantidad_recursos)]
    cargas = [0] * cantidad_recursos

    # Recorremos las tareas en el orden de alta calidad que ya calculamos
    for indice_tarea in orden_tareas:
        tarea = tareas[indice_tarea]
        
        # Estrategia de Mínima Carga: 
        # Buscamos el recurso compatible que esté más libre actualmente
        mejor_recurso = tarea.recursos_compatibles[0]
        min_carga = cargas[mejor_recurso]
        
        for r in tarea.recursos_compatibles[1:]:
            if cargas[r] < min_carga:
                min_carga = cargas[r]
                mejor_recurso = r
            # Desempate opcional por ID de recurso para que sea determinista
            elif cargas[r] == min_carga:
                if r < mejor_recurso:
                    mejor_recurso = r
        
        # Asignación definitiva
        asignacion[indice_tarea] = mejor_recurso
        tareas_por_recurso[mejor_recurso].append(indice_tarea)
        cargas[mejor_recurso] += tarea.duracion

    return Solucion(
        asignacion=asignacion,
        tareas_por_recurso=tareas_por_recurso,
        cargas=cargas,
        makespan=max(cargas)
    )

def intentar_reubicacion(
    tareas: Sequence[Tarea],
    solucion: Solucion,
    makespan_objetivo: int,
) -> bool:
    if not solucion.cargas:
        return False

    # 1. Identificar el recurso que dicta el makespan
    recurso_max = -1
    max_carga = -1
    # Buscamos también el segundo máximo para saber si el movimiento realmente baja el makespan global
    segundo_max_carga = -1
    
    for i, c in enumerate(solucion.cargas):
        if c > max_carga:
            segundo_max_carga = max_carga
            max_carga = c
            recurso_max = i
        elif c > segundo_max_carga:
            segundo_max_carga = c

    if max_carga <= makespan_objetivo:
        return False

    # 2. Solo probamos mover tareas del recurso crítico (el más cargado)
    # Aumentamos el rango a 100 para encontrar más oportunidades
    tareas_candidatas = sorted(
        solucion.tareas_por_recurso[recurso_max],
        key=lambda i: tareas[i].duracion,
        reverse=True
    )[:100]

    for idx_t in tareas_candidatas:
        t = tareas[idx_t]
        dur = t.duracion
        
        # Nueva carga potencial del recurso que suelta la tarea
        carga_origen_post = max_carga - dur
        
        for r_dest in t.recursos_compatibles:
            if r_dest == recurso_max:
                continue
            
            carga_dest_post = solucion.cargas[r_dest] + dur
            
            # EL TRUCO DE VELOCIDAD:
            # Un movimiento es bueno si la nueva carga del destino Y la nueva carga del origen
            # son menores que el makespan actual.
            if carga_dest_post < max_carga:
                # Calculamos el nuevo makespan potencial de forma instantánea O(1)
                # Es el máximo entre: la nueva carga origen, la nueva carga destino y el segundo máximo anterior
                nuevo_ms = max(carga_origen_post, carga_dest_post, segundo_max_carga)
                
                if nuevo_ms < max_carga:
                    # ¡Éxito! Aplicamos el movimiento
                    solucion.asignacion[idx_t] = r_dest
                    solucion.tareas_por_recurso[recurso_max].remove(idx_t)
                    solucion.tareas_por_recurso[r_dest].append(idx_t)
                    solucion.cargas[recurso_max] -= dur
                    solucion.cargas[r_dest] += dur
                    solucion.makespan = nuevo_ms
                    return True
                    
    return False

def intentar_swap(
    tareas: Sequence[Tarea],
    solucion: Solucion,
    makespan_objetivo: int,
) -> bool:
    if not solucion.cargas:
        return False

    # 1. Identificar el recurso crítico y el segundo máximo
    max_idx = -1
    max_v = -1
    segundo_max = -1
    for i, c in enumerate(solucion.cargas):
        if c > max_v:
            segundo_max = max_v
            max_v = c
            max_idx = i
        elif c > segundo_max:
            segundo_max = c

    if max_v <= makespan_objetivo:
        return False

    # 2. Seleccionar candidatos (límites pequeños para no perder tiempo)
    tareas_a = sorted(solucion.tareas_por_recurso[max_idx], 
                     key=lambda i: tareas[i].duracion, reverse=True)[:20]
    
    # Solo probamos intercambiar con recursos que tengan poca carga
    recursos_b = sorted(range(len(solucion.cargas)), 
                       key=lambda i: solucion.cargas[i])[:15]

    for idx_a in tareas_a:
        t_a = tareas[idx_a]
        dur_a = t_a.duracion
        
        for rb in recursos_b:
            if rb == max_idx: continue
            
            # Solo probamos algunas tareas del recurso destino
            for idx_b in solucion.tareas_por_recurso[rb][:15]:
                t_b = tareas[idx_b]
                dur_b = t_b.duracion
                
                # El swap solo sirve si la tarea que sacamos es más grande que la que entra
                if dur_a <= dur_b: continue
                
                # Verificar compatibilidad (Uso de 'in' sobre la tupla es rápido)
                if rb not in t_a.recursos_compatibles: continue
                if max_idx not in t_b.recursos_compatibles: continue
                
                nueva_carga_a = max_v - dur_a + dur_b
                nueva_carga_b = solucion.cargas[rb] - dur_b + dur_a
                
                # El nuevo makespan sería el máximo entre estas dos y lo que ya era el segundo máximo
                nuevo_ms = max(nueva_carga_a, nueva_carga_b, segundo_max)
                
                if nuevo_ms < max_v:
                    # Aplicar Swap
                    solucion.asignacion[idx_a], solucion.asignacion[idx_b] = rb, max_idx
                    solucion.tareas_por_recurso[max_idx].remove(idx_a)
                    solucion.tareas_por_recurso[rb].remove(idx_b)
                    solucion.tareas_por_recurso[max_idx].append(idx_b)
                    solucion.tareas_por_recurso[rb].append(idx_a)
                    solucion.cargas[max_idx] = nueva_carga_a
                    solucion.cargas[rb] = nueva_carga_b
                    solucion.makespan = nuevo_ms
                    return True
    return False

def optimizar_solucion(
    tareas: Sequence[Tarea],
    solucion_inicial: Solucion,
    makespan_objetivo: int,
    tiempo_limite: float,
) -> Solucion:
    # Usamos la misma solución (sin copiar al principio) para ahorrar memoria
    # ya que intentar_reubicacion ya modifica 'actual'
    actual = copiar_solucion(solucion_inicial)
    
    # Bucle infinito hasta que se agote el tiempo de CPU
    while time.perf_counter() < tiempo_limite:
        # Intentamos mover tareas. Si no hay éxito con reubicación, 
        # opcionalmente podrías probar swap, pero reubicación es más rápida.
        if intentar_reubicacion(tareas, actual, makespan_objetivo):
            # Si alcanzamos la meta, salimos de inmediato
            if actual.makespan <= makespan_objetivo:
                break
        else:
            # Si no hay movimientos de reubicación, intentamos swap
            if not intentar_swap(tareas, actual, makespan_objetivo):
                # Si ni reubicación ni swap encuentran nada, 
                # esperamos un milisegundo o probamos con una tarea aleatoria
                # para no saturar la CPU en un bucle vacío, 
                # o simplemente salimos si ya estamos satisfechos.
                break 

    return actual

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
    # 1. Definimos el tiempo límite global (9.5s para dejar margen de guardado)
    tiempo_inicio = time.perf_counter()
    tiempo_limite_global = tiempo_inicio + 9.5
    
    # 2. Generamos el orden maestro (ahora devuelve una lista con un solo orden)
    ordenes = generar_ordenes_de_tareas(tareas)
    orden_maestro = ordenes[0]
    
    # 3. Construimos la solución inicial con el greedy rápido
    # Nota: Ya no pasamos el parámetro 'variante'
    mejor_solucion = construir_solucion_greedy(tareas, recursos, orden_maestro)
    
    # Si por casualidad la inicial ya cumple el objetivo, terminamos
    if mejor_solucion.makespan <= makespan_objetivo:
        return mejor_solucion

    # 4. Optimizamos hasta que se agote el tiempo
    # Aquí es donde el programa pasará el 98% del tiempo bajando el makespan
    mejor_solucion = optimizar_solucion(
        tareas=tareas,
        solucion_inicial=mejor_solucion,
        makespan_objetivo=makespan_objetivo,
        tiempo_limite=tiempo_limite_global,
    )

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
        