import sqlite3

conn = sqlite3.connect('db/puestos_2026.db')

print("=== TAREA 3.1 — Arrastre Verde CA->SE ===")
sql1 = open('sql/tarea_3_1.sql').read()
resultado1 = conn.execute(sql1).fetchall()
print(f"Total filas: {len(resultado1)}")
print("Primeras 5:")
for fila in resultado1[:5]:
    print(" ", fila)
print("Últimas 5 (menor ratio):")
for fila in resultado1[-5:]:
    print(" ", fila)

print()
print("=== TAREA 3.2 — Dominancia extrema ===")
sql2 = open('sql/tarea_3_2.sql').read()
resultado2 = conn.execute(sql2).fetchall()
print(f"Total filas: {len(resultado2)}")
print("Primeras 5:")
for fila in resultado2[:5]:
    print(" ", fila)

# Verificación extra: todos los pct_dominancia deben ser > 0.6
todos_mayores_60 = all(fila[6] > 0.6 for fila in resultado2)
print(f"¿Todos los casos tienen dominancia > 60%? {todos_mayores_60}")

print()
print("=== TAREA 3.3 — Atribución determinística (Top 5) ===")
sql3 = open('sql/tarea_3_3.sql').read()
resultado3 = conn.execute(sql3).fetchall()
print(f"Total filas (debe ser 5): {len(resultado3)}")
for fila in resultado3:
    print(" ", fila)

conn.close()