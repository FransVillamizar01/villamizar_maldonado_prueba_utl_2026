import sqlite3
import json
import subprocess
import sys

# ============ SECCION META (edita con tus datos) ============
META = {
    "nombre": "Frans Sebastian Villamizar Maldonado",
    "email": "fsvillamizar@unibioyaca.edu.co",
    "repo_url": "https://github.com/FransVillamizar01/villamizar_maldonado_prueba_utl_2026"
}
# ==============================================================

DB_PATH = "db/puestos_2026.db"
MUNICIPIOS_ESPERADOS = ["TUNJA", "PAIPA", "SOGAMOSO", "DUITAMA"]

resultado = {"meta": META}

# 1. Verificar 4/4 municipios
conn = sqlite3.connect(DB_PATH)
municipios_bd = [row[0] for row in conn.execute("SELECT DISTINCT municipio FROM resultados").fetchall()]
municipios_ok = [m for m in MUNICIPIOS_ESPERADOS if m in municipios_bd]
print(f"{len(municipios_ok)}/{len(MUNICIPIOS_ESPERADOS)} municipios")
resultado["municipios"] = municipios_bd
resultado["municipios_check"] = f"{len(municipios_ok)}/{len(MUNICIPIOS_ESPERADOS)}"

# 2. Filas por tabla (verificacion Reto 2.3)
resultado["filas_por_tabla"] = {
    "resultados": conn.execute("SELECT COUNT(*) FROM resultados").fetchone()[0],
    "partidos": conn.execute("SELECT COUNT(*) FROM partidos").fetchone()[0],
    "carga_log": conn.execute("SELECT COUNT(*) FROM carga_log").fetchone()[0],
}

# 3. Partido lider SE por municipio (verificacion Reto 2.3)
lideres_se = {}
for municipio in municipios_bd:
    fila = conn.execute("""
        SELECT p.nombre, SUM(r.votos) as total
        FROM resultados r
        JOIN partidos p ON r.codpar = p.codpar
        WHERE r.corporacion = 'SE' AND r.municipio = ?
        GROUP BY r.codpar
        ORDER BY total DESC
        LIMIT 1
    """, (municipio,)).fetchone()
    lideres_se[municipio] = {"partido": fila[0], "votos": fila[1]} if fila else None
resultado["partido_lider_se"] = lideres_se

# 4. Ejecutar las 3 queries SQL y confirmar que no dan error
resultado["sql_checks"] = {}
for i, archivo in enumerate(["tarea_3_1", "tarea_3_2", "tarea_3_3"], start=1):
    try:
        sql = open(f"sql/{archivo}.sql", encoding="utf-8").read()
        filas = conn.execute(sql).fetchall()
        print("SQL OK")
        resultado["sql_checks"][archivo] = {"status": "OK", "filas": len(filas)}
    except Exception as e:
        print(f"ERROR en {archivo}: {e}")
        resultado["sql_checks"][archivo] = {"status": f"ERROR: {e}"}

conn.close()

# 5. Capturar los valores impresos por scatter.py (r, pendiente, n_mesas)
try:
    proceso = subprocess.run(
        [sys.executable, "viz/scatter.py"],
        capture_output=True, text=True, timeout=60
    )
    salida = proceso.stdout.strip()
    linea_resultado = [l for l in salida.splitlines() if l.startswith("r=")]
    resultado["scatter_output"] = linea_resultado[-1] if linea_resultado else salida
except Exception as e:
    resultado["scatter_output"] = f"ERROR ejecutando scatter.py: {e}"

# 6. Guardar el manifest
with open("outputs/evaluation_manifest.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print("evaluation_manifest.json generado correctamente")