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

def construir_url(municipio, corporacion):
    """
    Arma la URL exacta según el patrón real descubierto en DevTools:
    /json/ACT/{corporacion}/{codigo_divipola}.json
    """
    codigo = MUNICIPIOS[municipio]
    return f"{BASE_URL}/json/ACT/{corporacion}/{codigo}.json"


def parsear_resultados(data, municipio, corporacion):
    """
    Recibe el JSON crudo completo (con camaras -> partotabla -> act -> cantotabla)
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
                puesto = cand.get("amb", "")
                candidato_nombre = f"{cand.get('nomcan','')} {cand.get('apecan','')}".strip()
                votos = int(cand.get("vot", 0) or 0)

                filas.append((
                    municipio,
                    puesto,
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

    if args.preflight:
        logging.info("Modo preflight: mostrando municipios a procesar (sin descargar)")
        for municipio in args.municipios:
            print(f"{municipio}: pendiente de descarga (preflight, sin datos aún)")
        return

    conn = sqlite3.connect("db/puestos_2026.db")
    crear_tabla_si_no_existe(conn)

    for municipio in args.municipios:
        if municipio not in MUNICIPIOS:
            logging.warning(f"Municipio desconocido, se omite: {municipio}")
            continue

        logging.info(f"Procesando {municipio}...")
        total_insertadas, total_omitidas = 0, 0

        for corporacion in ["CA", "SE"]:
            url = construir_url(municipio, corporacion)
            data = fetch_con_retry(url)
            filas = parsear_resultados(data, municipio, corporacion)
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