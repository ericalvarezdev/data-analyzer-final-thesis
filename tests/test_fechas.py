# pruebas de las fechas: que se detecten bien las columnas de fechas (también las de un csv
# en formato español), que los filtros de fecha den lo que tienen que dar y que los gráficos
# con fechas en el eje x salgan enteros y en orden. Se ejecutan con: pytest
import pandas as pd
import pytest

from app.services.procesamiento import inferir_tipo
from app.services.graficos import aplicar_filtros, construir_especificacion


def _filtro(tipo, valores, posicion=0):
    return {"posicion": posicion, "tipo_filtro": tipo, "valores": valores, "conector": "AND"}


def _importes(df):
    return sorted(df["Importe"].tolist())


# DETECTAR SI UNA COLUMNA ES DE FECHAS

@pytest.mark.parametrize("valores", [
    ["2025-01-15", "2025-02-20", "2025-03-05"],                # ISO
    ["2025-01-15 10:30:00", "2025-02-20 18:00:00"],            # ISO con hora
    ["13/01/2025", "02/03/2025", "25/12/2025"],                # español, primer día > 12
    ["02/03/2025", "13/01/2025", "25/12/2025"],                # español, primer día <= 12
    ["02-03-25", "13-01-25"],                                  # con guiones y año de 2 cifras
    ["2025-01-15T10:00:00Z", "2025-02-20T11:00:00+02:00"],     # con zonas horarias distintas
])
def test_columnas_de_fechas_en_texto(valores):
    assert inferir_tipo(pd.Series(valores * 4)) == "fecha"


def test_columna_de_fechas_con_muchas_celdas_vacias():
    # 2 de cada 5 celdas vacías, las vacías no tendrían que contar
    serie = pd.Series(["2025-01-15", None, "2025-02-20", None, "2025-03-05"] * 4)
    assert inferir_tipo(serie) == "fecha"


def test_fechas_de_excel():
    assert inferir_tipo(pd.Series(pd.to_datetime(["2025-01-15", "2025-02-20"]))) == "fecha"


@pytest.mark.parametrize("valores", [
    ["Madrid", "Barcelona", "Sevilla"],
    ["T1", "T2", "T3", "T4"],          # trimestres
    ["10:30", "11:45", "09:00"],       # horas sin día
    ["Jan", "Feb", "Mar"],             # meses sin año
    ["85123A", "22423", "C536379"],    # códigos de producto o de factura
])
def test_columnas_que_no_son_fechas(valores):
    assert inferir_tipo(pd.Series(valores * 4)) == "texto"


def test_numeros_no_son_fechas():
    assert inferir_tipo(pd.Series([2024, 2025, 2026])) == "numerico"


def test_formato_español_no_depende_del_orden_de_las_filas():
    # el mismo filtro con las mismas fechas en distinto orden tiene que dar lo mismo
    df = pd.DataFrame({"Fecha": ["02/03/2025", "13/01/2025"], "Importe": [1, 2]})
    al_reves = df.iloc[::-1].reset_index(drop=True)
    filtro = [_filtro("fecha_antes_de", ["2025-02-01"])]
    assert _importes(aplicar_filtros(df, filtro)) == [2]        # solo el 13 de enero
    assert _importes(aplicar_filtros(al_reves, filtro)) == [2]


def test_formato_eeuu():
    # mes/día/año: el 01/15/2025 no puede ser día/mes, así que la columna se lee como mes/día
    df = pd.DataFrame({"Fecha": ["01/02/2025", "01/15/2025", "02/20/2025"], "Importe": [1, 2, 3]})
    assert _importes(aplicar_filtros(df, [_filtro("fecha_antes_de", ["2025-02-01"])])) == [1, 2]


# FILTROS DE FECHA

@pytest.fixture
def ventas():
    # un csv "a la española": fechas en dd/mm/aaaa con hora y la primera fila con el día <= 12
    return pd.DataFrame({
        "Fecha": ["02/03/2025 09:00", "13/01/2025 10:00", "31/03/2025 18:30", "01/04/2025 08:00",
                  "15/02/2025 12:00", "30/06/2025 20:00", None],
        "Importe": [10, 20, 30, 40, 50, 60, 70],
    })


def test_fecha_antes_de(ventas):
    assert _importes(aplicar_filtros(ventas, [_filtro("fecha_antes_de", ["2025-03-01"])])) == [20, 50]


def test_fecha_despues_de_no_incluye_ese_dia(ventas):
    # el 31/03 a las 18:30 es "el día 31", no "después del 31"
    assert _importes(aplicar_filtros(ventas, [_filtro("fecha_despues_de", ["2025-03-31"])])) == [40, 60]


def test_fecha_entre_incluye_el_ultimo_dia_entero(ventas):
    assert _importes(aplicar_filtros(ventas, [_filtro("fecha_entre", ["2025-03-01", "2025-03-31"])])) == [10, 30]


def test_filtro_de_fecha_con_zona_horaria_no_da_error():
    df = pd.DataFrame({"Fecha": ["2025-01-15T10:00:00Z", "2025-02-20T11:00:00Z"], "Importe": [1, 2]})
    assert _importes(aplicar_filtros(df, [_filtro("fecha_antes_de", ["2025-02-01"])])) == [1]


def test_filtro_de_fecha_en_excel(ventas):
    # las mismas fechas pero ya como fechas de verdad, como llegan de un excel
    excel = ventas.copy()
    excel["Fecha"] = pd.to_datetime(excel["Fecha"], dayfirst=True)
    assert _importes(aplicar_filtros(excel, [_filtro("fecha_entre", ["2025-03-01", "2025-03-31"])])) == [10, 30]


# GRÁFICOS CON FECHAS EN EL EJE X

def test_lineas_por_fecha_enseñan_todos_los_dias_en_orden():
    df = pd.DataFrame({"Fecha": pd.date_range("2025-01-01", periods=60, freq="D"), "Ventas": range(60)})
    x = construir_especificacion(df, 0, 1, "suma", "lineas", "Fecha", "Ventas")["data"][0]["x"]
    assert len(x) == 60
    assert x[0] == "2025-01-01" and x[-1] == "2025-03-01"


def test_fechas_con_hora_se_agrupan_por_dia():
    df = pd.DataFrame({"Fecha": ["2025-01-01 09:00", "2025-01-01 12:00", "2025-01-02 10:00"],
                       "Ventas": [1, 2, 3]})
    trazo = construir_especificacion(df, 0, 1, "suma", "lineas", "Fecha", "Ventas")["data"][0]
    assert trazo["x"] == ["2025-01-01", "2025-01-02"]
    assert trazo["y"] == [3.0, 3.0]


def test_barras_por_fecha_van_en_orden_de_fecha():
    df = pd.DataFrame({"Fecha": ["05/01/2025", "02/01/2025", "20/01/2025", "02/01/2025"]})
    x = construir_especificacion(df, 0, None, "recuento", "barras", "Fecha", None)["data"][0]["x"]
    assert x == ["2025-01-02", "2025-01-05", "2025-01-20"]


def test_barras_por_categoria_siguen_igual():
    df = pd.DataFrame({"Ciudad": ["Lleida", "Barcelona", "Barcelona", "Girona"], "Ventas": [5, 1, 1, 9]})
    x = construir_especificacion(df, 0, 1, "suma", "barras", "Ciudad", "Ventas")["data"][0]["x"]
    assert x == ["Girona", "Lleida", "Barcelona"]  # de más a menos, como siempre