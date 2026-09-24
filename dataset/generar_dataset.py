import pandas as pd
import requests

# URL del servidor espejo de Kumi Systems para extraer el dataset de OpenStreetMap
url = "https://overpass.kumi.systems/api/interpreter"

# Cabecera User-Agent obligatoria para evitar el error 429
headers = {
    'User-Agent': 'LimaTourismGraphBuilder/1.0 (Educational Project; contacto@universidad.edu)'
}

# Query para obtener los lugares turísticos en Lima
query = """
[out:json][timeout:120];
area["name"="Lima"]["admin_level"="6"]->.searchArea;
(
  nwr["tourism"]["name"~"."](area.searchArea);
  nwr["historic"]["name"~"."](area.searchArea);
  nwr["leisure"="park"]["name"~"."](area.searchArea);
  nwr["amenity"~"arts_centre|theatre|cinema|marketplace"]["name"~"."](area.searchArea);
);
out center;
"""

print("Descargando destinos turísticos de Lima...")

try:
  response = requests.post(url, data={"data": query}, headers=headers, timeout=130)

  if response.status_code == 200:
    data = response.json()
    elements = data.get("elements", [])
    print(f"¡Conexión exitosa! Se obtuvieron {len(elements)} elementos brutos.")

    lista_destinos = []

    for el in elements:
      tags = el.get("tags", {})
      nombre = tags.get("name")

      if not nombre:
        continue

      lat, lon = None, None

      if "lat" in el and "lon" in el:
        lat = el["lat"]
        lon = el["lon"]
      elif "center" in el:
        lat = el["center"].get("lat")
        lon = el["center"].get("lon")

      if lat and lon:
        lista_destinos.append({"name": nombre, "lat": lat, "lon": lon})

    # Procesamiento de datos con Pandas
    df_export = pd.DataFrame(lista_destinos)
    df_export = df_export.drop_duplicates(subset=["name"]).reset_index(
        drop=True
    )

    # Limitación de 1500 datos
    if len(df_export) > 1500:
      df_export = df_export.head(1500)

    # Guardar dataset en un archivo .csv dentro de la carpeta "dataset"
    nombre_archivo = "destinos_turisticos_lima.csv"
    df_export.to_csv("dataset/destinos_turisticos_lima.csv", index=False, encoding="utf-8")

    print(
        f"¡Listo! Dataset guardado como '{nombre_archivo}' con un total exacto"
        f" de {len(df_export)} destinos."
    )

  else:
    print(
        f"El servidor respondió con el código de error {response.status_code}:"
        f" {response.text}"
    )

except requests.exceptions.Timeout:
  print("La consulta tardó demasiado. El servidor está saturado en este momento.")
except Exception as e:
  print(f"Ocurrió un error inesperado: {e}")