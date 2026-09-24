import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import heapq
import sys

INF = sys.maxsize

class Punto:
    def __init__(self, indice, x, y, nombre):
        self.indice = indice
        self.x = x
        self.y = y
        self.nombre = nombre

class Arista:
    def __init__(self, inicio, fin):
        self.segmento = np.array([[inicio.x, inicio.y], [fin.x2, fin.y2]])

class Grafo:
    def __init__(self, num_vertices):
        self.V = num_vertices
        self.vertices = []
        self.aristas = []
        self.lista_adyacencia = [[] for _ in range(num_vertices)]

    def agregar_arista(self, vertice1, vertice2, peso):
        self.lista_adyacencia[vertice1].append((vertice2, peso))
        self.lista_adyacencia[vertice2].append((vertice1, peso))
    
    def camino_minimo(self, inicio, fin):
        visitados = [False] * self.V
        distancias = [INF] * self.V
        cola = []
        heapq.heappush(cola, (0, -1, inicio))
        # Algoritmo de Dijkstra
        while len(cola) > 0:
            peso, anterior, actual = heapq.heappop(cola)
            if visitados[actual]:
                continue
            visitados[actual] = True
            distancias[actual] = (peso, anterior, actual)
            if actual == fin:
                break
            for vecino, peso_vecino in self.lista_adyacencia[actual]:
                if not visitados[vecino]:
                    heapq.heappush(cola, (peso + peso_vecino, actual, vecino))
        # Si no hay un camino entre los 2 nodos, se retorna una lista con -1
        if distancias[fin] == INF:
            self.recorrido_minimo = [-1]
            return
        # Reconstruimos el recorrido mínimo desde el nodo de incio hasta el final
        recorrido = []
        actual = fin
        while actual != inicio:
            recorrido.append(actual)
            for elemento in distancias:
                if elemento == INF:
                    continue
                if elemento[2] == actual:
                    actual = elemento[1]
                    break
        recorrido.append(inicio)
        self.recorrido_minimo = recorrido[::-1]

    def dibujar_grafo(self):
        fig, ax = plt.subplots(figsize=(12, 6))

        x_vals, y_vals = [], []
    
        for punto in self.vertices:
            x_vals.append(punto.x)
            y_vals.append(punto.y)
            """ax.annotate(punto.nombre,
                        (punto.x, punto.y),
                        textcoords="offset points",
                        xytext=(0, 8),
                        ha='center',
                        fontsize=9,
                        color='red')"""
    
        # segmentos = LineCollection(self.aristas, colors="blue")
    
        fig.canvas.manager.set_window_title("Puntos")
        # ax.add_collection(segmentos)
    
        plt.scatter(x_vals, y_vals, color='red', marker='o', s=1)
    
        # ax.axhline(0, color='black', linewidth=1)
        # ax.axvline(0, color='black', linewidth=1)
        plt.xlabel("Eje X")
        plt.ylabel("Eje Y")
        
        plt.show()