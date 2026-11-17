# Utilidades para crear la carpeta de salida y pausar entre consultas a los mirrors.
import os
import time

# Librerías para convertir los resultados a CSV y consultar Overpass.
import pandas as pd
import requests

# Servidores alternativos de Overpass, usados si uno no responde o está ocupado.
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Identifica el cliente ante los servidores de OpenStreetMap.
headers = {
    "User-Agent": "LimaOfficeGraphBuilder/1.0 (Educational Project; contacto@universidad.edu)"
}

# La consulta limita los resultados a oficinas con nombre dentro del recuadro de Lima.
# "out center" devuelve coordenadas centrales para vías y relaciones; "qt" optimiza el orden.
query = """
[out:json][timeout:45];
nwr["office"]["name"](-12.35,-77.20,-11.70,-76.65);
out center qt;
"""


def fetch_overpass(query_str: str, mirrors: list[str]) -> dict:
    """Consulta los mirrors en orden y devuelve la primera respuesta con elementos."""
    for base_url in mirrors:
        print(f"Probando mirror: {base_url} ...")
        try:
            # Envía la consulta y espera como máximo 55 segundos por respuesta.
            resp = requests.post(
                base_url,
                data={"data": query_str},
                headers=headers,
                timeout=55,
            )
            # Si el servidor está saturado, intenta con el siguiente mirror.
            if resp.status_code in (429, 502, 503, 504):
                print(f"  -> Servidor ocupado ({resp.status_code}), probando siguiente.")
                continue

            resp.raise_for_status()
            payload = resp.json()

            # Overpass puede incluir detalles de avisos junto a los resultados.
            if "remark" in payload:
                print(f"  -> Aviso del servidor: {payload['remark']}")

            if payload.get("elements"):
                print(f"  -> Respuesta válida con {len(payload['elements'])} elementos.")
                return payload
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # La falta de respuesta de un mirror no impide probar los siguientes.
            print("  -> Sin respuesta en este mirror, probando siguiente.")
        # Da un breve respiro al servicio antes del próximo intento.
        time.sleep(1)

    raise RuntimeError("Ningún mirror de Overpass respondió con datos.")


def has_essentials(record: dict) -> bool:
    """Descarta registros sin los campos necesarios para identificar y ubicar la oficina."""
    for key in ("name", "type", "lat", "lon"):
        val = record.get(key)
        if val is None or str(val).strip() == "":
            return False
    return True

try:
    # Descarga los datos y obtiene los elementos devueltos por Overpass.
    data = fetch_overpass(query, MIRRORS)
    elements = data.get("elements", [])

    lista_destinos = []
    for el in elements:
        # Las etiquetas contienen los atributos asignados a cada elemento en OpenStreetMap.
        tags = el.get("tags", {})
        nombre = tags.get("name")
        tipo = tags.get("office")

        # Nodos tienen lat/lon propios; vías y relaciones usan el centro calculado por Overpass.
        lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
        lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")

        # Usa la primera etiqueta de dirección disponible como distrito.
        distrito = (
            tags.get("addr:district")
            or tags.get("addr:suburb")
            or tags.get("addr:city")
        )

        # Normaliza las etiquetas OSM en las columnas que se guardarán en el CSV.
        candidato = {
            "name": nombre,
            "type": tipo,
            "district": distrito,
            "email": tags.get("email") or tags.get("contact:email"),
            "opening_hours": tags.get("opening_hours") or tags.get("contact:opening_hours"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "lat": lat,
            "lon": lon,
        }

        # Conserva solo registros con los campos mínimos definidos en has_essentials.
        if has_essentials(candidato):
            lista_destinos.append(candidato)

    # Convierte los registros en tabla; elimina nombres duplicados y limita a 1500 filas.
    df_export = pd.DataFrame(lista_destinos)
    if not df_export.empty:
        df_export = df_export.drop_duplicates(subset=["name"]).reset_index(drop=True)
        df_export = df_export.head(1500)

    # Crea la carpeta si aún no existe y exporta el CSV en UTF-8.
    os.makedirs("dataset", exist_ok=True)
    ruta_salida = os.path.join("dataset", "oficinas_lima.csv")
    df_export.to_csv(ruta_salida, index=False, encoding="utf-8")

    print(
        f"¡Listo! Guardadas {len(df_export)} oficinas en '{ruta_salida}' "
        f"(de {len(elements)} elementos brutos)."
    )

except Exception as e:
    # Informa fallos de consulta, procesamiento o escritura del archivo.
    print(f"Error final: {e}")