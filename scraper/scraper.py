import argparse
import time
import logging
import sqlite3
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

BASE_URL = "https://resultadospreccongreso2026.registraduria.gov.co"

MUNICIPIOS = {
    "TUNJA": "0700001",
    "PAIPA": "0700181",
    "SOGAMOSO": "0700277",
    "DUITAMA": "0700079",
}

def obtener_puestos_por_municipio(municipios):
    """
    Descarga el nomenclador y navega el árbol territorial para obtener,
    por cada municipio, la lista de códigos de 'local' (puesto de votación).
    Retorna: {"TUNJA": ["0700001010001", "0700001010002", ...], ...}
    """
    logging.info("Descargando nomenclador para mapear puestos de votación...")
    nomenclator_url = f"{BASE_URL}/json/nomenclator.json"
    data = fetch_con_retry(nomenclator_url)
    if not data:
        logging.error("No se pudo descargar el nomenclador. Abortando.")
        return {}

    ambitos = data["amb"][0]["ambitos"]
    por_indice = {a["i"]: a for a in ambitos}

    resultado = {}
    for municipio in municipios:
        codigo_municipio = MUNICIPIOS[municipio]
        nodo_municipio = next(
            (a for a in ambitos if a.get("l") == 3 and a.get("c") == codigo_municipio),
            None
        )
        if not nodo_municipio:
            logging.warning(f"No se encontró el municipio {municipio} en el nomenclador")
            continue

        puestos = []
        indices_zonas = nodo_municipio["h"][0]["p"]
        for idx_zona in indices_zonas:
            zona = por_indice[idx_zona]
            indices_locales = zona["h"][0]["p"]
            for idx_local in indices_locales:
                local = por_indice[idx_local]
                puestos.append(local["c"])

        resultado[municipio] = puestos
        logging.info(f"{municipio}: {len(puestos)} puestos encontrados")

    return resultado

def fetch_con_retry(url, intentos=3):
    """
    Intenta descargar la URL hasta 'intentos' veces.
    Si falla, espera un poco más cada vez antes de reintentar (backoff).
    """
    for intento in range(1, intentos + 1):
        try:
            respuesta = requests.get(url, timeout=10)
            respuesta.raise_for_status()  # lanza error si el status no es 200
            return respuesta.json()
        except requests.RequestException as error:
            espera = 2 ** intento  # 2s, 4s, 8s...
            logging.warning(f"Intento {intento} falló para {url}: {error}")
            if intento < intentos:
                logging.info(f"Reintentando en {espera}s...")
                time.sleep(espera)
    logging.error(f"No se pudo obtener {url} después de {intentos} intentos")
    return None

def construir_url_puesto(codigo_puesto, corporacion):
    """
    Arma la URL para un puesto de votación específico (código de 13 dígitos):
    /json/ACT/{corporacion}/{codigo_puesto}.json
    """
    return f"{BASE_URL}/json/ACT/{corporacion}/{codigo_puesto}.json"


def parsear_resultados(data, municipio, corporacion, codigo_puesto):
    """
    Recibe el JSON crudo de UN puesto específico (con camaras -> partotabla -> act -> cantotabla)
    y lo convierte en una lista de filas simples, listas para SQLite.
    """
    filas = []
    if not data:
        return filas

    camaras = data.get("camaras", [])

    for camara in camaras:
        partidos = camara.get("partotabla", [])

        for partido_wrapper in partidos:
            partido = partido_wrapper.get("act", {})
            codpar = partido.get("codpar")
            candidatos = partido.get("cantotabla", [])

            for cand in candidatos:
                candidato_nombre = f"{cand.get('nomcan','')} {cand.get('apecan','')}".strip()
                votos = int(cand.get("vot", 0) or 0)

                filas.append((
                    municipio,
                    codigo_puesto,
                    corporacion,
                    codpar,
                    candidato_nombre,
                    votos
                ))
    return filas

def crear_tabla_si_no_existe(conn):
    """Crea la tabla básica si aún no existe (versión mínima para el scraper)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipio TEXT NOT NULL,
            puesto TEXT NOT NULL,
            corporacion TEXT NOT NULL CHECK(corporacion IN ('CA','SE')),
            codpar INTEGER NOT NULL,
            candidato TEXT,
            votos INTEGER NOT NULL DEFAULT 0,
            UNIQUE(municipio, puesto, corporacion, codpar, candidato)
        )
    """)
    conn.commit()


def guardar_filas(conn, filas):
    """Inserta filas usando INSERT OR IGNORE para no duplicar (idempotencia)."""
    insertadas = 0
    for fila in filas:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO resultados
            (municipio, puesto, corporacion, codpar, candidato, votos)
            VALUES (?, ?, ?, ?, ?, ?)
        """, fila)
        if cursor.rowcount:
            insertadas += 1
    conn.commit()
    return insertadas, len(filas) - insertadas


def main():
    parser = argparse.ArgumentParser(description="Scraper de resultados electorales Boyacá 2026")
    parser.add_argument("--municipios", nargs="+",
                         default=list(MUNICIPIOS.keys()),
                         help="Lista de municipios a extraer")
    parser.add_argument("--preflight", action="store_true",
                         help="Solo muestra conteo, no descarga ni guarda nada")
    args = parser.parse_args()

    municipios_validos = [m for m in args.municipios if m in MUNICIPIOS]
    for m in args.municipios:
        if m not in MUNICIPIOS:
            logging.warning(f"Municipio desconocido, se omite: {m}")

    if args.preflight:
        logging.info("Modo preflight: consultando nomenclador para contar puestos (sin descargar resultados)")
        puestos_por_municipio = obtener_puestos_por_municipio(municipios_validos)
        for municipio, puestos in puestos_por_municipio.items():
            print(f"{municipio}: {len(puestos)} puestos encontrados (preflight, sin descargar resultados)")
        return

    conn = sqlite3.connect("db/puestos_2026.db")
    crear_tabla_si_no_existe(conn)

    puestos_por_municipio = obtener_puestos_por_municipio(municipios_validos)

    for municipio, codigos_puesto in puestos_por_municipio.items():
        logging.info(f"Procesando {municipio} ({len(codigos_puesto)} puestos)...")
        total_insertadas, total_omitidas = 0, 0

        for codigo_puesto in codigos_puesto:
            for corporacion in ["CA", "SE"]:
                url = construir_url_puesto(codigo_puesto, corporacion)
                data = fetch_con_retry(url)
                filas = parsear_resultados(data, municipio, corporacion, codigo_puesto)
                insertadas, omitidas = guardar_filas(conn, filas)
                total_insertadas += insertadas
                total_omitidas += omitidas

        logging.info(f"{municipio} completado: {total_insertadas} insertadas, {total_omitidas} omitidas")

        conn.execute(
            "INSERT INTO carga_log (municipio, filas_insertadas, filas_omitidas) VALUES (?, ?, ?)",
            (municipio, total_insertadas, total_omitidas)
        )
        conn.commit()

    conn.close()
    logging.info("Proceso finalizado.")


if __name__ == "__main__":
    main()