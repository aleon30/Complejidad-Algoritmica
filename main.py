import pandas as pd
from Grafo_algoritmos import Grafo, Punto
from interfaz_visual import dibujar_grafo

# Lee el dataset y conserva longitud/latitud en los ejes geograficos x/y.
df = pd.read_csv("dataset/oficinas_lima.csv")

df["x"] = df["lon"]
df["y"] = df["lat"]

# Conserva solo las columnas que se pasan a cada vertice del grafo.
df = df[["name", "type", "district", "email", "opening_hours", "phone", "x", "y",]]

# Convierte cada fila en un vertice con sus coordenadas y datos de contacto.
puntos = []

for index, fila in enumerate(df.itertuples()):
   punto = Punto(index, fila.x, fila.y, fila.name, tipo=fila.type, distrito=fila.district,
                 email=fila.email, horario_atencion=fila.opening_hours, telefono=fila.phone)
   puntos.append(punto)

# Se inicializa la clase Grafo con los puntos para crear las conexiones
grafo = Grafo(len(puntos), puntos)
# Se abre la interfaz visual para dibujar el grafo con los puntos y sus conexiones
dibujar_grafo(grafo)