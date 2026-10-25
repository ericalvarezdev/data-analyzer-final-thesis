import io
import tempfile
import os

import plotly.graph_objects as go
import plotly.io as pio
from pypdf import PdfWriter

from app.models.informe_generado import InformeGenerado


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
        figura.update_layout(title=grafico.nombre or f"Gráfico #{grafico.id}")
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
