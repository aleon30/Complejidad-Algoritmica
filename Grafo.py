import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import heapq
import math

# Clase Punto para almacenar el índice de cada punto en la lista de adyacencia
# sus coordenadas x e y, y el nombre del lugar
class Punto:
    def __init__(self, indice, x, y, nombre):
        self.indice = indice
        self.x = x
        self.y = y
        self.nombre = nombre

# Clase Arista para manegar los segmentos desde sus coordenadas de inicio y fin
class Arista:
    def __init__(self, inicio, fin):
        self.segmento = np.array([[inicio[0], inicio[1]], [fin[0], fin[1]]])

# Clase Grafo principal
class Grafo:
    def __init__(self, num_vertices):
        self.V = num_vertices
        self.vertices = [[] for _ in range(num_vertices)]
        self.aristas = []
        self.lista_adyacencia = [[] for _ in range(num_vertices)]
        self.recorrido_minimo = []
        self.recorrido_minimo_nombres = []

    def agregar_vertice(self, punto):
        self.vertices[punto.indice] = (punto.x, punto.y, punto.nombre)

    # Se generan las aristas de cada punto a los otros 3 puntos más cercanos a su ubicación
    def generar_aristas(self):
        self.lista_adyacencia = [[] for _ in range(self.V)]
        self.aristas = []

        conexiones = set()
        for indice, punto in enumerate(self.vertices):
            vecinos = sorted(
                (
                    (math.hypot(punto[0] - otro[0], punto[1] - otro[1]), otro_indice)
                    for otro_indice, otro in enumerate(self.vertices)
                    if otro_indice != indice
                )
            )

            for distancia, otro_indice in vecinos[:6]:
                conexiones.add((min(indice, otro_indice), max(indice, otro_indice), distancia))

        for inicio_indice, fin_indice, peso in sorted(conexiones):
            inicio = self.vertices[inicio_indice]
            fin = self.vertices[fin_indice]
            self.lista_adyacencia[inicio_indice].append((fin_indice, peso))
            self.lista_adyacencia[fin_indice].append((inicio_indice, peso))
            self.aristas.append(Arista(inicio, fin).segmento)
        
    # Implementamos el algoritmo de Dijkstra para encontrar el camino mínimo entre 2 puntos
    def camino_minimo(self, inicio, fin):
        distancias = [math.inf] * self.V
        visitados = [False] * self.V
        distancias[inicio] = 0
        anteriores = [None] * self.V
        cola = [(0, inicio, -1)]

        while cola:
            distancia_actual, actual, anterior = heapq.heappop(cola)
            if visitados[actual]:
                continue

            visitados[actual] = True
            distancias[actual] = distancia_actual
            anteriores[actual] = anterior

            if actual == fin:
                break

            for vecino, peso_arista in self.lista_adyacencia[actual]:
                distancia = distancia_actual + peso_arista
                if not visitados[vecino]:
                    heapq.heappush(cola, (distancia, vecino, actual))

        if math.isinf(distancias[fin]):
            self.recorrido_minimo = []
            self.recorrido_minimo_nombres = []
            return self.recorrido_minimo

        recorrido = []
        recorrido_nombres = []
        actual = fin

        while actual != inicio:
            anterior = anteriores[actual]
            recorrido.append(Arista(self.vertices[anterior], self.vertices[actual]).segmento)
            recorrido_nombres.append(self.vertices[actual][2])
            actual = anterior
        recorrido_nombres.append(self.vertices[inicio][2])

        self.recorrido_minimo = recorrido[::-1]
        self.recorrido_minimo_nombres = recorrido_nombres[::-1]

        return self.recorrido_minimo

    # Dibujamos el grafo con matplotlib, e implementamos una interfaz para poder seleccionar 2 puntos
    # para aplicar el algoritmo de Dijkstra
    def dibujar_grafo(self):
        fig, ax = plt.subplots(figsize=(12, 6))

        x_vals = [punto[0] for punto in self.vertices]
        y_vals = [punto[1] for punto in self.vertices]
    
        segmentos = LineCollection(self.aristas, 
                                   colors="gray",
                                   linewidths=0.1,
                                   alpha=0.8)

        fig.canvas.manager.set_window_title("Puntos de interés en Lima")
        fig.subplots_adjust(bottom=0.15)
        ax.add_collection(segmentos)

        aristas_camino_minimo = LineCollection(
            self.recorrido_minimo,
            colors="red",
            linewidths=2.5,
            alpha=1,
            zorder=3,
        )
        ax.add_collection(aristas_camino_minimo)

        puntos = ax.scatter(
            x_vals,
            y_vals,
            color="purple",
            marker="o",
            s=12,
            picker=8,
            zorder=2,
        )
        seleccion = ax.scatter([], 
                               [], 
                               color="orange", 
                               marker="o", 
                               s=35, 
                               zorder=4)
        seleccionados = []
        texto_camino = fig.text(
            0.01,
            0.02,
            "Camino: selecciona dos puntos",
            fontsize=8,
            wrap=True,
            va="bottom",
        )

        ax.set_title("Haz clic en el primer punto")

        def seleccionar_punto(evento):
            if evento.artist is not puntos or not len(evento.ind):
                return

            coordenadas = puntos.get_offsets()[evento.ind]
            mouse_xy = np.array([evento.mouseevent.x, evento.mouseevent.y])
            pantalla_xy = ax.transData.transform(coordenadas)
            indice = evento.ind[np.argmin(np.linalg.norm(pantalla_xy - mouse_xy, axis=1))]

            if len(seleccionados) == 2:
                seleccionados.clear()
                aristas_camino_minimo.set_segments([])
                texto_camino.set_text("Camino: selecciona dos puntos")

            seleccionados.append(int(indice))
            seleccion.set_offsets(
                np.array([self.vertices[i][:2] for i in seleccionados])
            )

            nombre = self.vertices[indice][2]
            if len(seleccionados) == 1:
                ax.set_title(f"Origen: {nombre}. Haz clic en el destino")
                texto_camino.set_text(f"Origen: {nombre}")
            else:
                inicio, fin = seleccionados
                camino = self.camino_minimo(inicio, fin)
                aristas_camino_minimo.set_segments(camino)
                if camino or inicio == fin:
                    ax.set_title(
                        f"Camino mínimo: {self.vertices[inicio][2]} → "
                        f"{self.vertices[fin][2]}"
                    )
                    texto_camino.set_text(
                        "Camino: " + " → ".join(self.recorrido_minimo_nombres)
                    )
                else:
                    ax.set_title("No existe un camino entre los puntos seleccionados")
                    texto_camino.set_text("No existe un camino entre los puntos seleccionados")

            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("pick_event", seleccionar_punto)
    
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        
        plt.show()