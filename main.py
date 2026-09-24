import pandas as pd
from Grafo import *

df = pd.read_csv("dataset/destinos_turisticos_lima.csv")

def escalar_a_rango(serie, nuevo_min, nuevo_max):
   min_val = serie.min()
   max_val = serie.max()
   
   if min_val == max_val:
      return serie * 0
   
   return (
      (serie - min_val) / (max_val - min_val)
  ) * (nuevo_max - nuevo_min) + nuevo_min

df["x"] = escalar_a_rango(df["lon"], -100, 100)
df["y"] = escalar_a_rango(df["lat"], -1000, 1000)

df = df[["name", "x", "y"]]

num_vertices = len(df)

grafo = Grafo(num_vertices)

for fila in df.itertuples():
    punto = Punto(fila.index, fila.x, fila.y, fila.name)
    grafo.vertices.append(punto)

grafo.dibujar_grafo()