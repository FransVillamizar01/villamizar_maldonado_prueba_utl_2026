import sqlite3

conn = sqlite3.connect('db/puestos_2026.db')

resultado = conn.execute("""
    SELECT candidato, codpar, SUM(votos) as total_votos
    FROM resultados
    WHERE corporacion = 'SE' AND candidato != 'SOLO POR LA LISTA'
    GROUP BY candidato, codpar
    ORDER BY total_votos DESC
    LIMIT 20
""").fetchall()

for candidato, codpar, votos in resultado:
    print(f"{candidato} (partido {codpar}): {votos} votos")

conn.close()