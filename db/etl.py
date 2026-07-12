import sqlite3
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

DB_PATH = "db/puestos_2026.db"
SCHEMA_PATH = "db/schema.sql"

# Partidos confirmados con certeza según el PDF de la prueba (tabla de colores)
PARTIDOS_CONOCIDOS = {
    5: "ALIANZA VERDE (CA)",
    57: "ALIANZA VERDE (SE)",
    87: "PACTO HISTORICO (CA)",
    92: "PACTO HISTORICO (SE)",
    10: "CENTRO DEMOCRATICO",
    2: "PARTIDO CONSERVADOR",
}


def normalizar_nombre(nombre):
    """Limpia espacios dobles y estandariza mayúsculas."""
    if not nombre:
        return ""
    nombre = nombre.strip().upper()
    nombre = re.sub(r"\s+", " ", nombre)
    return nombre


def aplicar_schema(conn):
    """Ejecuta schema.sql para asegurar que todas las tablas existen."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()
    logging.info("Schema aplicado correctamente.")


def poblar_partidos(conn):
    """
    Extrae los codpar únicos ya presentes en 'resultados' y los inserta
    en 'partidos', usando el nombre conocido si existe, o un placeholder
    honesto (PARTIDO_{codpar}) si no lo tenemos confirmado.
    """
    codpares = conn.execute(
        "SELECT DISTINCT codpar FROM resultados"
    ).fetchall()

    insertados, omitidos = 0, 0
    for (codpar,) in codpares:
        nombre = PARTIDOS_CONOCIDOS.get(codpar, f"PARTIDO_{codpar}")
        cursor = conn.execute(
            "INSERT OR IGNORE INTO partidos (codpar, nombre) VALUES (?, ?)",
            (codpar, nombre)
        )
        if cursor.rowcount:
            insertados += 1
        else:
            omitidos += 1

    conn.commit()
    logging.info(f"Partidos: {insertados} insertados, {omitidos} ya existentes")
    return insertados, omitidos


def normalizar_candidatos(conn):
    """
    Recorre 'resultados' y normaliza el campo 'candidato' (limpia espacios,
    mayúsculas consistentes). Actualiza in-place.
    """
    filas = conn.execute("SELECT id, candidato FROM resultados").fetchall()
    actualizadas = 0

    for id_fila, candidato in filas:
        candidato_normalizado = normalizar_nombre(candidato)
        if candidato_normalizado != candidato:
            conn.execute(
                "UPDATE resultados SET candidato = ? WHERE id = ?",
                (candidato_normalizado, id_fila)
            )
            actualizadas += 1

    conn.commit()
    logging.info(f"Candidatos normalizados: {actualizadas} filas actualizadas")
    return actualizadas


def main():
    conn = sqlite3.connect(DB_PATH)

    aplicar_schema(conn)
    insertados, omitidos = poblar_partidos(conn)
    normalizar_candidatos(conn)

    conn.close()
    logging.info("ETL finalizado correctamente.")


if __name__ == "__main__":
    main()