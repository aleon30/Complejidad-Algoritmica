import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch
from matplotlib.widgets import Button
import numpy as np
import math
import textwrap
import time

# Función para dibujar el grafo y manejar la interacción con el usuario.
def dibujar_grafo(grafo):
    # El area principal muestra las ubicaciones y las conexiones del grafo.
    fig, ax = plt.subplots(figsize=(12, 6))

    x_vals = [punto.x for punto in grafo.vertices]
    y_vals = [punto.y for punto in grafo.vertices]

    segmentos = LineCollection(grafo.aristas, colors="gray", linewidths=0.1, alpha=0.8)

    fig.canvas.manager.set_window_title("Grafo de oficinas en Lima")
    fig.subplots_adjust(bottom=0.22, right=0.51)
    ax.add_collection(segmentos)

    aristas_camino_minimo = LineCollection(grafo.recorrido_minimo, colors="red",
                                           linewidths=2.5, alpha=1, zorder=3)
    ax.add_collection(aristas_camino_minimo)

    puntos = ax.scatter(x_vals, y_vals, color="skyblue", marker="o",
                        s=12, picker=8, zorder=2)
    seleccion = ax.scatter([], [], color="orange", marker="o", s=35, zorder=4)
    seleccionados = []

    # La columna derecha contiene los datos de origen/destino y el resumen de ruta.
    panel_contacto = fig.add_axes([0.53, 0.24, 0.45, 0.68])
    panel_contacto.set_axis_off()

    estilo_contacto = {
        "boxstyle": "round,pad=0.5",
        "facecolor": "white",
        "edgecolor": "gray",
        "alpha": 0.95,
    }
    fuentes_texto = ["DejaVu Sans", "Microsoft YaHei"]
    texto_origen = panel_contacto.text(0.02, 0.94, "Origen\nSelecciona un punto",
                                       transform=panel_contacto.transAxes, va="top",
                                       fontsize=8, wrap=True, fontfamily=fuentes_texto,
                                       bbox=estilo_contacto)
    texto_destino = panel_contacto.text(0.52, 0.94, "Destino\nSelecciona un punto",
                                        transform=panel_contacto.transAxes, va="top",
                                        fontsize=8, wrap=True, fontfamily=fuentes_texto,
                                        bbox=estilo_contacto)
    texto_tiempo = ax.text(0.02, 0.98, "Tiempo de ejecución: —", transform=ax.transAxes,
                           va="top", fontsize=9, bbox={
                               "boxstyle": "round,pad=0.35",
                               "facecolor": "white",
                               "edgecolor": "gray",
                               "alpha": 0.9}, zorder=5)
    # Floyd-Warshall se precalcula al presionar el botón para no demorar el inicio del programa.
    boton_precalculo_ax = fig.add_axes([0.53, 0.94, 0.22, 0.045])
    boton_precalculo_floyd = Button(
        boton_precalculo_ax,
        "Precalcular Floyd-Warshall",
        color="0.85",
        hovercolor="0.95",
    )
    boton_precalculo_floyd.label.set_fontsize(9)
    grafo._boton_precalculo_floyd = boton_precalculo_floyd
    if grafo.floyd_precalculado:
        boton_precalculo_floyd.set_active(False)
        boton_precalculo_floyd.color = "0.75"
        boton_precalculo_floyd.label.set_color("0.45")
        boton_precalculo_ax.set_facecolor("0.75")
    texto_tiempo_precalculo = fig.text(0.77, 0.962, "Tiempo de precálculo: pendiente\n"
                                       "Espera aproximadamente 16 segundos", va="top", fontsize=9,
                                       bbox={"boxstyle": "round,pad=0.35",
                                             "facecolor": "white",
                                             "edgecolor": "gray",
                                             "alpha": 0.9})

    def formatear_informacion_contacto(etiqueta, punto):
        # Los campos vacios del CSV se presentan uniformemente como no disponibles.
        def valor_o_disponible(valor):
            if valor is None or (isinstance(valor, (float, np.floating)) and math.isnan(valor)):
                return "No disponible"

            texto = str(valor).strip()
            return texto or "No disponible"

        return "\n".join(
            [
                etiqueta,
                f"Nombre: {valor_o_disponible(punto.nombre)}",
                f"Tipo: {valor_o_disponible(punto.tipo)}",
                f"Distrito: {valor_o_disponible(punto.distrito)}",
                f"Correo: {valor_o_disponible(punto.email)}",
                "Horario: "
                f"{valor_o_disponible(punto.horario_atencion)}",
                f"Teléfono: {valor_o_disponible(punto.telefono)}",
            ]
        )

    # El panel de ruta ocupa un espacio fijo para no cubrir las tarjetas de contacto.
    panel_camino = fig.add_axes([0.53, 0.17, 0.45, 0.48])
    panel_camino.set_axis_off()
    panel_camino.add_patch(
        FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", transform=panel_camino.transAxes,
                       facecolor="white", edgecolor="gray", alpha=0.95, clip_on=True))
    texto_camino = panel_camino.text(0.04, 0.96, "Algoritmo: Dijkstra\nCamino: selecciona dos puntos",
                                     transform=panel_camino.transAxes, va="top", fontsize=10, wrap=True,
                                     fontfamily=fuentes_texto, clip_on=True)

    def actualizar_texto_camino(mensaje, cantidad_nodos=0, color="black"):
        # Ajusta la fuente al tamano renderizado para que rutas largas quepan en el panel.
        texto_camino.set_text(mensaje)
        texto_camino.set_color(color)
        cantidad_lineas = len(mensaje.splitlines())
        reduccion_por_nodos = max(0, cantidad_nodos - 20) * 0.035
        reduccion_por_lineas = max(0, cantidad_lineas - 12) * 0.18
        tamano_fuente = max(5.5, 10 - max(reduccion_por_nodos, reduccion_por_lineas))
        renderer = fig.canvas.get_renderer()
        caja_panel = panel_camino.get_window_extent(renderer)
        ancho_disponible = caja_panel.width * 0.97
        alto_disponible = caja_panel.height * 0.96

        for _ in range(3):
            texto_camino.set_fontsize(tamano_fuente)
            caja_texto = texto_camino.get_window_extent(renderer)
            if (caja_texto.width <= ancho_disponible and caja_texto.height <= alto_disponible) or tamano_fuente <= 5.5:
                break
            escala = min(ancho_disponible / caja_texto.width, alto_disponible / caja_texto.height)
            nuevo_tamano = max(5.5, tamano_fuente * escala * 0.98)
            if nuevo_tamano >= tamano_fuente:
                break
            tamano_fuente = nuevo_tamano

    # Los botones seleccionan una funcion con la misma interfaz inicio/destino.
    algoritmos = {
        "UCS": grafo.UCS,
        "Dijkstra": grafo.Dijkstra,
        "Bellman-Ford": grafo.Bellman_Ford,
        "Floyd-Warshall": grafo.consultar_floyd_warshall,
    }
    algoritmo_actual = {"nombre": "Dijkstra"}
    botones_algoritmo = {}

    def mostrar_advertencia_floyd():
        # Evita una consulta a matrices que aun no han sido precalculadas.
        grafo.recorrido_minimo = []
        grafo.recorrido_minimo_nombres = []
        aristas_camino_minimo.set_segments([])
        texto_tiempo.set_text("Tiempo de ejecución: —")
        actualizar_texto_camino(
            "Advertencia: precalcula las matrices de Floyd-Warshall "
            "con el botón superior derecho antes de usar este algoritmo.",
            color="darkred",
        )
        ax.set_title("Floyd-Warshall requiere precálculo", fontsize=11)

    def calcular_camino(inicio, fin):
        # Mide el calculo elegido y actualiza el texto y las aristas resaltadas.
        nombre_algoritmo = algoritmo_actual["nombre"]
        if nombre_algoritmo == "Floyd-Warshall" and not grafo.floyd_precalculado:
            mostrar_advertencia_floyd()
            return

        tiempo_inicio = time.perf_counter()
        camino = algoritmos[nombre_algoritmo](inicio, fin)
        duracion = time.perf_counter() - tiempo_inicio
        texto_tiempo.set_text(f"Tiempo de ejecución: {duracion:.6f} s")
        aristas_camino_minimo.set_segments(camino)

        if camino or inicio == fin:
            ax.set_title(f"Camino mínimo con {nombre_algoritmo}", fontsize=11)
            unidad_distancia = "km" if grafo.pesos_en_kilometros else "u"
            distancia_formateada = (f"{grafo.distancia_recorrido:.3f}".replace(".", ","))
            recorrido_formateado = textwrap.fill(" → ".join(grafo.recorrido_minimo_nombres),
                                                 width=120, break_long_words=True,
                                                 break_on_hyphens=False)
            actualizar_texto_camino(
                f"Camino mínimo con {nombre_algoritmo} "
                f"({len(grafo.recorrido_minimo_nombres)} puntos, "
                f"{distancia_formateada} {unidad_distancia}):\n"
                + recorrido_formateado,
                cantidad_nodos=len(grafo.recorrido_minimo_nombres),
            )
        else:
            ax.set_title(f"Sin ruta ({nombre_algoritmo})", fontsize=11)
            actualizar_texto_camino(f"Algoritmo: {nombre_algoritmo} | "
                                    "No existe un camino entre los puntos seleccionados")

    def seleccionar_algoritmo(nombre_algoritmo, evento):
        # Cambia el algoritmo activo y recalcula si ambos puntos ya estan seleccionados.
        algoritmo_actual["nombre"] = nombre_algoritmo
        if len(seleccionados) < 2:
            texto_tiempo.set_text("Tiempo de ejecución: —")
        for nombre, boton in botones_algoritmo.items():
            color = "lightblue" if nombre == nombre_algoritmo else "0.85"
            boton.color = color
            boton.ax.set_facecolor(color)

        if nombre_algoritmo == "Floyd-Warshall" and not grafo.floyd_precalculado:
            mostrar_advertencia_floyd()
            evento.canvas.draw_idle()
            return

        if len(seleccionados) == 2:
            calcular_camino(*seleccionados)
        elif seleccionados:
            ax.set_title(f"Selecciona el destino ({nombre_algoritmo})", fontsize=11)
            actualizar_texto_camino(f"Algoritmo: {nombre_algoritmo} | "
                                    f"Origen: {grafo.vertices[seleccionados[0]].nombre}")
        else:
            ax.set_title(f"{nombre_algoritmo}: selecciona el origen", fontsize=11)
            actualizar_texto_camino(f"Algoritmo: {nombre_algoritmo} | "
                                    "Camino: selecciona dos puntos")

        evento.canvas.draw_idle()

    def precalcular_floyd(evento):
        # Muestra el estado, mide el precalculo y desactiva el boton al terminar.
        if grafo.floyd_precalculado:
            if grafo.tiempo_precalculo_floyd is None:
                texto_tiempo_precalculo.set_text("Precálculo completo; tiempo no medido")
            else:
                texto_tiempo_precalculo.set_text("Tiempo de precálculo: "
                                                 f"{grafo.tiempo_precalculo_floyd:.2f} s")
            boton_precalculo_floyd.set_active(False)
            boton_precalculo_floyd.color = "0.75"
            boton_precalculo_ax.set_facecolor("0.75")
            boton_precalculo_floyd.label.set_color("0.45")
            evento.canvas.draw_idle()
            return

        texto_tiempo_precalculo.set_text("Precálculo en curso...\nEspera aproximadamente 16 segundos")
        evento.canvas.draw()
        tiempo_inicio = time.perf_counter()
        grafo.Floyd_Warshall()
        grafo.tiempo_precalculo_floyd = time.perf_counter() - tiempo_inicio
        texto_tiempo_precalculo.set_text(f"Tiempo de precálculo: {grafo.tiempo_precalculo_floyd:.2f} s")
        boton_precalculo_floyd.set_active(False)
        boton_precalculo_floyd.color = "0.75"
        boton_precalculo_ax.set_facecolor("0.75")
        boton_precalculo_floyd.label.set_color("0.45")
        if algoritmo_actual["nombre"] == "Floyd-Warshall":
            if len(seleccionados) == 2:
                calcular_camino(*seleccionados)
            elif seleccionados:
                actualizar_texto_camino("Floyd-Warshall precalculado. Selecciona el destino.")
            else:
                actualizar_texto_camino("Floyd-Warshall precalculado. Selecciona origen y destino.")

        evento.canvas.draw_idle()

    boton_precalculo_floyd.on_clicked(precalcular_floyd)

    for indice, nombre_algoritmo in enumerate(algoritmos):
        boton_ax = fig.add_axes([0.03 + indice * 0.24, 0.08, 0.21, 0.07])
        color = "lightblue" if nombre_algoritmo == "Dijkstra" else "0.85"
        boton = Button(boton_ax, nombre_algoritmo, color=color, hovercolor="0.95")
        boton.on_clicked(lambda evento, 
                         nombre=nombre_algoritmo: seleccionar_algoritmo(nombre, evento))
        botones_algoritmo[nombre_algoritmo] = boton

    ax.set_title("Dijkstra: selecciona el origen", fontsize=11)

    def seleccionar_punto(evento):
        if evento.artist is not puntos or not len(evento.ind):
            return

        # Si varios puntos caen dentro del area clickeada, elige el mas cercano al cursor.
        coordenadas = puntos.get_offsets()[evento.ind]
        mouse_xy = np.array([evento.mouseevent.x, evento.mouseevent.y])
        pantalla_xy = ax.transData.transform(coordenadas)
        indice = evento.ind[np.argmin(np.linalg.norm(pantalla_xy - mouse_xy, axis=1))]

        if len(seleccionados) == 2:
            seleccionados.clear()
            aristas_camino_minimo.set_segments([])
            texto_tiempo.set_text("Tiempo de ejecución: —")
            actualizar_texto_camino(f"Algoritmo: {algoritmo_actual['nombre']} | "
                                    "Camino: selecciona dos puntos")

        seleccionados.append(int(indice))
        seleccion.set_offsets(np.array([[grafo.vertices[i].x, grafo.vertices[i].y] for i in seleccionados]))

        nombre = grafo.vertices[indice].nombre
        if len(seleccionados) == 1:
            texto_origen.set_text(
                formatear_informacion_contacto("Origen", grafo.vertices[indice]))
            texto_destino.set_text("Destino\nSelecciona un punto")
            ax.set_title(f"Selecciona el destino ({algoritmo_actual['nombre']})", fontsize=11)
            actualizar_texto_camino(f"Algoritmo: {algoritmo_actual['nombre']} | Origen: {nombre}")
        else:
            inicio, fin = seleccionados
            texto_destino.set_text(formatear_informacion_contacto("Destino", grafo.vertices[indice]))
            calcular_camino(inicio, fin)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", seleccionar_punto)

    # Corrige el aspecto de grados de longitud segun la latitud media del mapa.
    if y_vals:
        latitud_media = math.radians(float(np.mean(y_vals)))
        ax.set_aspect(1 / math.cos(latitud_media), adjustable="box")

    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    plt.show()