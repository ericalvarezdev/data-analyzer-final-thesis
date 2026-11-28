import html
import io
import tempfile
import os
import textwrap

import plotly.graph_objects as go
import plotly.io as pio
from pypdf import PdfWriter

from app.models.informe_generado import InformeGenerado
from app.models.grafico_generado import GraficoGenerado


# a partir de cuántas letras parto el texto de los filtros en otra línea, para que no se
# salga por el lado derecho del PDF (cada gráfico mide 700 px de ancho)
LETRAS_POR_LINEA_FILTROS = 80


# título del gráfico en el PDF: el nombre y debajo, más pequeños y en gris, los filtros.
# Devuelve el título y cuántas líneas de filtros tiene.
# Plotly entiende algunas etiquetas de HTML en los textos (<br> para saltar de línea,
# <span> para cambiar el tamaño o el color), por eso paso los textos por html.escape: si
# un nombre de columna o un valor llevase un "<" o un "&", Plotly lo leería como una
# etiqueta y el título saldría roto. quote=False porque las comillas no hace falta tocarlas
def _titulo_con_filtros(grafico: GraficoGenerado) -> tuple[str, int]:
    titulo = html.escape(grafico.nombre or f"Gráfico #{grafico.id}", quote=False)

    # el mismo texto que enseña la web (filtros normales y agregados)
    filtros = grafico.filtros_texto
    if not filtros:
        return titulo, 0

    lineas = textwrap.wrap(f"Filtros: {filtros}", width=LETRAS_POR_LINEA_FILTROS)
    for linea in lineas:
        titulo += f"<br><span style='font-size:12px;color:#666'>{html.escape(linea, quote=False)}</span>"

    return titulo, len(lineas)


# junta todos los gráficos de un informe en un único PDF.
# cada gráfico ya tiene guardada su especificacion (data+layout) de cuando se generó,
# así que aquí no recalculo nada, solo la convierto en figuras de Plotly y las exporto
def generar_pdf_informe(informe: InformeGenerado) -> bytes:

    if not informe.graficos:
        raise ValueError("El informe no tiene gráficos para exportar")

    figuras = []
    for grafico in informe.graficos:
        especificacion = grafico.especificacion
        figura = go.Figure(data=especificacion["data"], layout=especificacion["layout"])

        titulo, lineas_filtros = _titulo_con_filtros(grafico)
        if lineas_filtros == 0:
            figura.update_layout(title=titulo)
        else:
            # con filtros el título tiene varias líneas. Lo pongo arriba del todo (y=0.98 y
            # anclado por arriba) para que las líneas vayan bajando, y por cada línea dejo
            # 22 px más de margen arriba (más o menos lo que Plotly separa una línea de otra)
            # para que no se monten encima del gráfico
            figura.update_layout(title=dict(text=titulo, y=0.98, yanchor="top"),
                                 margin=dict(t=80 + 22 * lineas_filtros))
        figuras.append(figura)

    # pio.write_images (en vez de llamar a write_image gráfico por gráfico) manda
    # todas las figuras de golpe al mismo proceso de Kaleido, así que exportar un
    # informe con varios gráficos tarda lo mismo que exportar uno solo
    with tempfile.TemporaryDirectory() as carpeta_temporal:
        rutas = [os.path.join(carpeta_temporal, f"grafico_{i}.pdf") for i in range(len(figuras))]
        pio.write_images(fig=figuras, file=rutas, format="pdf")

        # cada ruta es un PDF de una sola página (un gráfico), los junto todos en
        # un único PDF con pypdf para que el usuario solo tenga que descargar un archivo
        escritor = PdfWriter()
        for ruta in rutas:
            escritor.append(ruta)

        buffer = io.BytesIO()
        escritor.write(buffer)

    return buffer.getvalue()