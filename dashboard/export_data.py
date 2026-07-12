import sqlite3
import json

conn = sqlite3.connect("db/puestos_2026.db")

# 1. Comparativo: votos CA totales por municipio
comparativo = conn.execute("""
    SELECT municipio, SUM(votos) as total
    FROM resultados
    WHERE corporacion = 'CA'
    GROUP BY municipio
    ORDER BY municipio
""").fetchall()

# 2. Por municipio: top 10 candidatos CA + partido lider SE
municipios = [row[0] for row in comparativo]

top_candidatos_por_municipio = {}
partido_lider_se_por_municipio = {}

for municipio in municipios:
    top10 = conn.execute("""
        SELECT candidato, codpar, SUM(votos) as total
        FROM resultados
        WHERE corporacion = 'CA' AND municipio = ? AND candidato != 'SOLO POR LA LISTA'
        GROUP BY candidato, codpar
        ORDER BY total DESC
        LIMIT 10
    """, (municipio,)).fetchall()
    top_candidatos_por_municipio[municipio] = [
        {"candidato": c, "codpar": p, "votos": v} for c, p, v in top10
    ]

    lider_se = conn.execute("""
        SELECT p.nombre, SUM(r.votos) as total
        FROM resultados r
        JOIN partidos p ON r.codpar = p.codpar
        WHERE r.corporacion = 'SE' AND r.municipio = ?
        GROUP BY r.codpar
        ORDER BY total DESC
        LIMIT 1
    """, (municipio,)).fetchone()
    partido_lider_se_por_municipio[municipio] = {
        "nombre": lider_se[0] if lider_se else "N/A",
        "votos": lider_se[1] if lider_se else 0
    }

# 3. Arrastre: ratio Verde por puesto y municipio (reutilizamos la query 3.1)
sql_arrastre = open("sql/tarea_3_1.sql").read()
arrastre_raw = conn.execute(sql_arrastre).fetchall()

arrastre_por_municipio = {}
for municipio, puesto, votos_ca, votos_se, ratio in arrastre_raw:
    arrastre_por_municipio.setdefault(municipio, []).append({
        "puesto": puesto,
        "votos_ca": votos_ca,
        "votos_se": votos_se,
        "ratio": ratio
    })

conn.close()

data = {
    "municipios": municipios,
    "comparativo_ca": [{"municipio": m, "votos": v} for m, v in comparativo],
    "top_candidatos": top_candidatos_por_municipio,
    "partido_lider_se": partido_lider_se_por_municipio,
    "arrastre": arrastre_por_municipio,
}

with open("dashboard/data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("data.json generado correctamente")
print(f"Municipios: {municipios}")