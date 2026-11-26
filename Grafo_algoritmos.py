import numpy as np
import heapq
import math

# Cada punto conserva las coordenadas geograficas y los datos descriptivos de una oficina.
class Punto:
    def __init__(self, indice, x, y, nombre, tipo=None, distrito=None, email=None,
        horario_atencion=None, telefono=None):
        self.indice = indice
        self.x = x
        self.y = y
        self.nombre = nombre
        self.tipo = tipo
        self.distrito = distrito
        self.email = email
        self.horario_atencion = horario_atencion
        self.telefono = telefono

# Una arista guarda el segmento x/y que Matplotlib utiliza para dibujar una conexion.
class Arista:
    def __init__(self, inicio, fin):
        self.segmento = np.array([[inicio.x, inicio.y], [fin.x, fin.y]])

# El grafo mantiene por separado las estructuras de busqueda, dibujo y Floyd-Warshall.
class Grafo:
    def __init__(self, num_vertices, puntos=None):
        self.V = num_vertices
        self.vertices = [[] for _ in range(num_vertices)]
        if puntos is not None:
            puntos = list(puntos)
            if len(puntos) != num_vertices:
                raise ValueError("La cantidad de puntos debe coincidir con num_vertices.")
            self.vertices = puntos

        # Estas estructuras se generan desde los puntos y se comparten con los algoritmos.
        self.aristas = []
        self.lista_aristas = []
        self.lista_adyacencia = [[] for _ in range(num_vertices)]
        self.recorrido_minimo = []
        self.recorrido_minimo_nombres = []
        self.distancia_recorrido = None
        self.pesos_en_kilometros = False
        # Las matrices se llenan solo cuando el usuario solicita el precalculo.
        self.matriz_distancias = np.empty((0, 0), dtype=float)
        self.matriz_nodos = np.empty((0, 0), dtype=int)
        self.floyd_precalculado = False
        self.tiempo_precalculo_floyd = None

        if puntos is not None:
            self._generar_aristas()

    def agregar_vertice(self, punto):
        self.vertices[punto.indice] = punto

    # Reconstruye las conexiones y descarta resultados de rutas o matrices anteriores.
    def generar_aristas(self):
        self._generar_aristas()

    def _generar_aristas(self):
        self.lista_adyacencia = [[] for _ in range(self.V)]
        self.aristas = []
        self.lista_aristas = []
        self.distancia_recorrido = None
        self.matriz_distancias = np.empty((0, 0), dtype=float)
        self.matriz_nodos = np.empty((0, 0), dtype=int)
        self.floyd_precalculado = False
        self.tiempo_precalculo_floyd = None
        # x representa longitud e y latitud
        self.pesos_en_kilometros = bool(self.vertices)

        # Se eligen los siete vecinos mas cercanos en coordenadas lon/lat.
        # El conjunto evita duplicar una conexion elegida desde ambos extremos.
        conexiones = set()
        for indice, punto in enumerate(self.vertices):
            # Se ordenan los vecinos por distancia euclidiana en coordenadas geograficas.
            vecinos = sorted(((math.hypot(punto.x - otro.x, punto.y - otro.y), otro_indice)
                              for otro_indice, otro in enumerate(self.vertices)
                              if otro_indice != indice))
            
            # Se añade una arista a los 7 vecinos más cercanos.
            for distancia, otro_indice in vecinos[:7]:
                conexiones.add((min(indice, otro_indice), max(indice, otro_indice)))

        # Se añaden las aristas no dirigidas en la lista de adyacencia y la lista de aristas para los algoritmos.
        for inicio_indice, fin_indice in sorted(conexiones):
            inicio = self.vertices[inicio_indice]
            fin = self.vertices[fin_indice]
            if self.pesos_en_kilometros:
                peso = self._distancia_geografica_km(inicio, fin)
            else:
                peso = math.hypot(inicio.x - fin.x, inicio.y - fin.y)
            self.lista_adyacencia[inicio_indice].append((fin_indice, peso))
            self.lista_adyacencia[fin_indice].append((inicio_indice, peso))
            self.lista_aristas.append((inicio_indice, fin_indice, peso))
            self.lista_aristas.append((fin_indice, inicio_indice, peso))
            self.aristas.append(Arista(inicio, fin).segmento)

    # Se calcula la distancia geográfica entre dos puntos usando la fórmula de Haversine.
    @staticmethod
    def _distancia_geografica_km(inicio, fin):
        # Haversine recibe longitud en x y latitud en y, ambas en grados.
        radio_tierra_km = 6371.0088
        latitud_inicio = math.radians(float(inicio.y))
        latitud_fin = math.radians(float(fin.y))
        diferencia_latitud = latitud_fin - latitud_inicio
        diferencia_longitud = math.radians(float(fin.x) - float(inicio.x))
        a = (math.sin(diferencia_latitud / 2) ** 2 
             + math.cos(latitud_inicio) * math.cos(latitud_fin) * math.sin(diferencia_longitud / 2) ** 2)
        return 2 * radio_tierra_km * math.asin(math.sqrt(a))

    # Algoritmo de busqueda de costo uniforme
    def UCS(self, inicio, fin):
        # Se guardan costo y predecesor solo para vertices que ya fueron alcanzados.
        costos_y_anteriores = {inicio: (0, None)}
        cola = [(0, inicio)]

        while cola:
            costo_actual, actual = heapq.heappop(cola)
            # Ignora entradas antiguas que quedaron en la cola tras mejorar un costo.
            if costo_actual != costos_y_anteriores[actual][0]:
                continue

            if actual == fin:
                break

            for vecino, peso_arista in self.lista_adyacencia[actual]:
                costo_total = costo_actual + peso_arista
                if vecino not in costos_y_anteriores or costo_total < costos_y_anteriores[vecino][0]:
                    costos_y_anteriores[vecino] = (costo_total, actual)
                    heapq.heappush(cola, (costo_total, vecino))

        if fin not in costos_y_anteriores:
            self.recorrido_minimo = []
            self.recorrido_minimo_nombres = []
            self.distancia_recorrido = None
            return self.recorrido_minimo

        # Sigue los predecesores desde el destino y luego invierte la secuencia.
        actual = fin
        recorrido_indices = []
        while actual is not None:
            recorrido_indices.append(actual)
            actual = costos_y_anteriores[actual][1]
        recorrido_indices.reverse()

        self.recorrido_minimo_nombres = [self.vertices[indice].nombre for indice in recorrido_indices]
        self.recorrido_minimo = [Arista(self.vertices[origen], self.vertices[destino]).segmento
                                 for origen, destino in zip(recorrido_indices, recorrido_indices[1:])]
        self.distancia_recorrido = costos_y_anteriores[fin][0]

        return self.recorrido_minimo

    # Algoritmo de Dijkstra
    def Dijkstra(self, inicio, fin):
        # Dijkstra fija cada nodo al extraer su menor costo de la cola de prioridad.
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
            self.distancia_recorrido = None
            return self.recorrido_minimo

        # Reconstruye primero desde el destino; invierte segmentos y nombres al final.
        recorrido = []
        recorrido_nombres = []
        actual = fin

        while actual != inicio:
            anterior = anteriores[actual]
            recorrido.append(Arista(self.vertices[anterior], self.vertices[actual]).segmento)
            recorrido_nombres.append(self.vertices[actual].nombre)
            actual = anterior
        recorrido_nombres.append(self.vertices[inicio].nombre)

        self.recorrido_minimo = recorrido[::-1]
        self.recorrido_minimo_nombres = recorrido_nombres[::-1]
        self.distancia_recorrido = distancias[fin]

        return self.recorrido_minimo

    # Algoritmo de Bellman-Ford
    def Bellman_Ford(self, inicio, fin):
        # Relaja la lista de aristas. Las distancias infinitas marcan nodos inalcanzables.
        distancias = [math.inf] * self.V
        distancias[inicio] = 0
        anteriores = [None] * self.V

        for _ in range(self.V - 1):
            actualizada = False
            for origen, destino, peso in self.lista_aristas:
                if not math.isinf(distancias[origen]) and distancias[origen] + peso < distancias[destino]:
                    distancias[destino] = distancias[origen] + peso
                    anteriores[destino] = (origen, destino, peso)
                    actualizada = True
            if not actualizada:
                break

        # No realizamos el segundo bucle de relajación de aristas,
        # ya que no hay pesos negativos y, por ende, no puede haber ciclos negativos.

        if math.isinf(distancias[fin]):
            self.recorrido_minimo = []
            self.recorrido_minimo_nombres = []
            self.distancia_recorrido = None
            return self.recorrido_minimo

        recorrido = []
        recorrido_nombres = []
        actual = fin

        while actual != inicio:
            arista_anterior = anteriores[actual]
            origen_arista, destino_arista, _ = arista_anterior
            recorrido.append(Arista(self.vertices[origen_arista], self.vertices[destino_arista]).segmento)
            recorrido_nombres.append(self.vertices[actual].nombre)
            actual = origen_arista
        recorrido_nombres.append(self.vertices[inicio].nombre)

        self.recorrido_minimo = recorrido[::-1]
        self.recorrido_minimo_nombres = recorrido_nombres[::-1]
        self.distancia_recorrido = distancias[fin]

        return self.recorrido_minimo

    # Algoritmo de Floyd-Warshall
    def Floyd_Warshall(self):
        if self.floyd_precalculado:
            return

        # Inicializa costos y primer salto para todas las parejas de vertices.
        self.matriz_distancias = np.full((self.V, self.V), math.inf)
        self.matriz_nodos = np.full((self.V, self.V), -1, dtype=int)
        np.fill_diagonal(self.matriz_distancias, 0)

        for origen, destino, peso in self.lista_aristas:
            if peso < self.matriz_distancias[origen, destino]:
                self.matriz_distancias[origen, destino] = peso
                self.matriz_nodos[origen, destino] = destino

        # Para cada intermedio, suma en bloque el costo origen-intermedio y el
        # costo intermedio-destino; los ejes de NumPy representan origen y destino.
        for intermedio in range(self.V):
            distancias_por_intermedio = (self.matriz_distancias[:, intermedio, np.newaxis]
                                         + self.matriz_distancias[np.newaxis, intermedio, :])

            # La mascara selecciona solo parejas cuyo costo mejora al pasar por el intermedio.
            mejoras = distancias_por_intermedio < self.matriz_distancias
            if np.any(mejoras):
                # Guarda los primeros saltos antes de actualizar la matriz de rutas.
                primeros_saltos = self.matriz_nodos[:, intermedio].copy()
                self.matriz_distancias[mejoras] = distancias_por_intermedio[mejoras]

                # Repite el primer salto de cada origen para todos sus destinos y
                # lo asigna solo a las parejas que mejoraron.
                siguientes = np.broadcast_to(primeros_saltos[:, np.newaxis], (self.V, self.V))
                self.matriz_nodos[mejoras] = siguientes[mejoras]

        self.floyd_precalculado = True
        self.tiempo_precalculo_floyd = None

    # Función para consultar la ruta más corta entre dos nodos usando las matrices de Floyd-Warshall.
    def consultar_floyd_warshall(self, inicio, fin):
        # Consulta las matrices ya calculadas y reconstruye la secuencia de primeros saltos.
        if not self.floyd_precalculado:
            raise RuntimeError("Precalcula las matrices de Floyd-Warshall antes de consultar una ruta.")

        if math.isinf(self.matriz_distancias[inicio, fin]):
            self.recorrido_minimo = []
            self.recorrido_minimo_nombres = []
            self.distancia_recorrido = None
            return self.recorrido_minimo

        recorrido_indices = [inicio]
        actual = inicio
        while actual != fin:
            actual = int(self.matriz_nodos[actual, fin])
            if actual < 0 or len(recorrido_indices) >= self.V:
                self.recorrido_minimo = []
                self.recorrido_minimo_nombres = []
                self.distancia_recorrido = None
                return self.recorrido_minimo
            recorrido_indices.append(actual)

        self.recorrido_minimo_nombres = [self.vertices[indice].nombre for indice in recorrido_indices]
        self.recorrido_minimo = [Arista(self.vertices[origen], self.vertices[destino]).segmento
                                 for origen, destino in zip(recorrido_indices, recorrido_indices[1:])]
        self.distancia_recorrido = self.matriz_distancias[inicio, fin]

        return self.recorrido_minimo
