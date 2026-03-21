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
    categoria:str #Añadimos para saber que categoria es


@dataclass
class Recurso:
    id: str
    categorias_compatibles:set[str]
    disponible: int = 0
from typing import List


# Esta función lee el archivo de tareas y devuelve una lista de objetos Tarea
def leer_tareas(path: str) -> List[Tarea]:

    # lista donde guardaremos todas las tareas
    tareas = []

    # abrimos el archivo en modo lectura
    with open(path, "r") as f:

        # recorremos cada línea del archivo
        for linea in f:

            # quitamos espacios y saltos de línea al inicio y final
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea: continue

            # separamos la línea por coma
            # ejemplo: "T1,5" -> ["T1", "5"]
            partes = linea.split(",")

            # el primer elemento es el id de la tarea
            tareas.append(Tarea(partes[0], int(partes[1]), partes[2]))

    # devolvemos la lista completa de tareas
    return tareas

# Esta función lee el archivo de recursos y devuelve una lista de objetos Recurso
def leer_recursos(path: str) -> List[Recurso]:

    # lista donde guardaremos los recursos
    recursos = []

    # abrimos el archivo en modo lectura
    with open(path,"r") as f:

        # recorremos cada línea del archivo
        for linea in f:

            # quitamos espacios y saltos de línea
            linea = linea.strip()

            # si la línea está vacía, la ignoramos
            if not linea: continue
            partes = linea.split(",")

            # la línea contiene el id del recurso
            rid = partes[0]

            # creamos un objeto Recurso
            cats = set(partes[1:])

            # lo agregamos a la lista
            recursos.append(Recurso(rid, cats))

    # devolvemos la lista completa
    return recursos

def planificar(tareas: List[Tarea], recursos: List[Recurso]):
    resultado=[]
    for t in tareas:
        compatibles=[r for r in recursos if t.categoria in r.categorias_compatibles]

        if not compatibles:
            print(f"No hay recurso para {t.id}({t.categoria})")
            continue
        r_elegido=min(compatibles, key=lambda x: x.disponible)
        inicio=r_elegido.disponible
        fin=inicio+t.duracion
        #guardamos asignacion y actualiza tiempo del recurso
        resultado.append((t.id, r_elegido.id, inicio, fin))
        r_elegido.disponible=fin
    return resultado
    
if __name__ == "__main__":
    # Capturamos el makespan del comando (ej: python main.py 12)
    makespan_objetivo = sys.argv[1] if len(sys.argv) > 1 else "0"
    
    print(f"Iniciando planificación (Objetivo: {makespan_objetivo})...")
    
    try:
        # 1. Cargar datos desde TUS archivos
        mis_tareas = leer_tareas("tareas.txt")
        mis_recursos = leer_recursos("recursos.txt")
        
        #2. Ordenar tareas
        mis_tareas.sort(key=lambda x: x.duracion, reverse=True)
        # 3. Ejecutar la lógica (la función planificar que definimos antes)
        resultado_plan = planificar(mis_tareas, mis_recursos)
        
        # 4. Generar output.txt (ID_Tarea,ID_Recurso,Inicio,Fin)
        with open("output.txt", "w") as f:
            for p in resultado_plan:
                # p[0]=ID_Tarea, p[1]=ID_Recurso, p[2]=Inicio, p[3]=Fin
                f.write(f"{p[0]},{p[1]},{p[2]},{p[3]}\n")
        
        print("✅ Éxito: Se ha generado 'output.txt' correctamente.")

    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")