# pasa los filtros de un gráfico a texto, por ejemplo "Región es Norte Y NO (Producto es Portátil)".
# Antes estaba dentro de pdf.py, pero ahora también lo enseña la web debajo de cada gráfico,
# así que lo saco a su propio archivo para que el PDF y la web usen exactamente el mismo texto.
# Aquí no importo los modelos a propósito: el modelo GraficoGenerado importa este archivo, y si
# este archivo importase los modelos se importarían el uno al otro en bucle (import circular)


NOMBRES_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MESES_DE_CADA_TRIMESTRE = {1: "enero - marzo", 2: "abril - junio", 3: "julio - septiembre",
                           4: "octubre - diciembre"}


# paso una fecha de como se guarda (aaaa-mm-dd) a como se lee en España (dd/mm/aaaa)
def _fecha_legible(valor) -> str:
    partes = str(valor).split("-")
    if len(partes) != 3:
        return str(valor)
    año, mes, dia = partes
    return f"{dia}/{mes}/{año}"


# paso un filtro a una frase corta, por ejemplo "Región es Norte" o
# "Fecha entre el 01/03/2025 y el 31/03/2025"
def _describir_filtro(filtro) -> str:
    # si por lo que sea la columna ya no existe pongo su id, igual que hace el frontend
    columna = filtro.columna.nombre_columna if filtro.columna else f"Columna {filtro.columna_id}"
    tipo = filtro.tipo_filtro
    valores = filtro.valores

    if tipo == "valor_exacto":
        texto = f"{columna} es {valores[0]}"
    elif tipo == "diferente_de":
        texto = f"{columna} es diferente de {valores[0]}"
    elif tipo == "lista_valores":
        texto = f"{columna} es uno de: {', '.join(str(valor) for valor in valores)}"
    elif tipo == "rango":
        texto = f"{columna} entre {valores[0]} y {valores[1]}"
    elif tipo == "mayor_que":
        texto = f"{columna} mayor que {valores[0]}"
    elif tipo == "menor_que":
        texto = f"{columna} menor que {valores[0]}"
    elif tipo == "contiene_texto":
        texto = f'{columna} contiene "{valores[0]}"'
    elif tipo == "fecha_antes_de":
        texto = f"{columna} antes del {_fecha_legible(valores[0])}"
    elif tipo == "fecha_despues_de":
        texto = f"{columna} después del {_fecha_legible(valores[0])}"
    elif tipo == "fecha_entre":
        texto = f"{columna} entre el {_fecha_legible(valores[0])} y el {_fecha_legible(valores[1])}"
    elif tipo == "fecha_dia":
        texto = f"{columna} el día {_fecha_legible(valores[0])}"
    elif tipo == "fecha_mes":
        # "2025-03" -> "marzo de 2025"
        año, mes = str(valores[0]).split("-")
        texto = f"{columna} en {NOMBRES_MESES[int(mes) - 1]} de {año}"
    elif tipo == "fecha_trimestre":
        trimestre = int(valores[1])
        texto = f"{columna} en el T{trimestre} de {valores[0]} ({MESES_DE_CADA_TRIMESTRE[trimestre]})"
    elif tipo == "fecha_ultimos_dias":
        dias = int(valores[0])
        if dias == 1:
            texto = f"{columna} en el último día del archivo"
        else:
            texto = f"{columna} en los últimos {dias} días del archivo"
    else:
        # por si algún día añado un tipo de filtro nuevo y me olvido de ponerlo aquí, así
        # el texto sale igual aunque no quede tan bonito
        texto = f"{columna} {tipo} {valores}"

    if filtro.negado:
        texto = f"NO ({texto})"

    return texto


# junta los filtros de un gráfico en una sola frase con sus Y/O, por ejemplo
# "Región es Norte Y NO (Producto es Portátil)". Si no hay filtros devuelve "".
# Los ordeno por id para que salgan en el mismo orden en el que se aplicaron, y el
# conector del primero no lo pongo porque no se usa para nada
def describir_filtros(filtros: list) -> str:
    texto = ""
    conector_anterior = None

    for i, filtro in enumerate(sorted(filtros, key=lambda f: f.id)):
        # pasa este filtro a una frase. Ej: "Category es Furniture"
        frase = _describir_filtro(filtro)
        
        # el primer filtro va solo sin conector delante y continue salta a la siguiente vuelta
        if i == 0:
            texto = frase
            continue
        # paso el conector a español ("OR" -> "O", "AND" -> "Y")
        conector = "O" if filtro.conector == "OR" else "Y"

        # si el conector cambia (de O a Y o al revés), todo lo de antes ya se ha calculado
        # como un bloque, así que lo meto entre paréntesis. Ej: "A O B" + Y C -> "(A O B) Y C"
        # (is not None porque en el 2º filtro aún no hay conector anterior con el que comparar)
        if conector_anterior is not None and conector != conector_anterior:
            # envuelvo entre paréntesis todo lo que llevo hasta ahora. Ej: "A O B" -> "(A O B)"
            texto = f"({texto})"

        # añado al final el conector y la frase del filtro nuevo. Ej: "A" -> "A O B"
        texto = f"{texto} {conector} {frase}"
        
        # me guardo este conector para compararlo con el del siguiente filtro
        conector_anterior = conector

    return texto




# paso un filtro agregado a una frase corta, por ejemplo "las 5 categorías con el valor más alto"
def _describir_filtro_agregado(filtro) -> str:
    if filtro.tipo in ("mayores", "menores"):
        cantidad = int(filtro.valor)
        extremo = "más alto" if filtro.tipo == "mayores" else "más bajo"
        if cantidad == 1:
            return f"la categoría con el valor {extremo}"
        return f"las {cantidad} categorías con el valor {extremo}"

    if filtro.tipo == "porcentaje_minimo":
        # :g quita los decimales que sobran (1.0 sale como 1, pero 0.5 se queda 0.5)
        return f"sin las categorías de menos del {filtro.valor:g}% del total"

    return f"{filtro.tipo} {filtro.valor}"


# junta los filtros agregados de un gráfico en un texto, en el orden en que se aplican.
# Ej: "sin las categorías de menos del 1% del total, las 5 categorías con el valor más alto"
def describir_filtros_agregados(filtros_agregados: list) -> str:
    return ", ".join(_describir_filtro_agregado(filtro)
                     for filtro in sorted(filtros_agregados, key=lambda f: f.id))