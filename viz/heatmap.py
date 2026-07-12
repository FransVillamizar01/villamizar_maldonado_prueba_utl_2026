import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect("db/puestos_2026.db")

# Traemos votos por candidato y municipio, solo Camara (CA), excluyendo "SOLO POR LA LISTA"
df = pd.read_sql("""
    SELECT municipio, candidato, SUM(votos) as votos
    FROM resultados
    WHERE corporacion = 'CA' AND candidato != 'SOLO POR LA LISTA'
    GROUP BY municipio, candidato
""", conn)
conn.close()

# Top 8 candidatos por votos totales (sumando los 4 municipios)
top8 = df.groupby("candidato")["votos"].sum().nlargest(8).index
df_top8 = df[df["candidato"].isin(top8)]

# % del total del municipio (no del total general) para cada candidato
df_top8 = df_top8.copy()
df_top8["pct"] = df_top8.groupby("municipio")["votos"].transform(lambda x: x / x.sum() * 100)

pivot = df_top8.pivot(index="candidato", columns="municipio", values="pct").fillna(0)

plt.figure(figsize=(9, 6))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "% del total municipal"})
plt.title("Top 8 candidatos CA — % del total de votos por municipio")
plt.xlabel("Municipio")
plt.ylabel("Candidato")
plt.tight_layout()
plt.savefig("viz/heatmap_municipios.png", dpi=150)
print("Heatmap guardado en viz/heatmap_municipios.png")