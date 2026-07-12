import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

conn = sqlite3.connect("db/puestos_2026.db")

# Votos CA y SE por puesto (sumando todos los partidos y candidatos, es el consolidado de la mesa)
df = pd.read_sql("""
    SELECT ca.municipio, ca.puesto, ca.votos AS votos_ca, se.votos AS votos_se
    FROM (
        SELECT municipio, puesto, SUM(votos) as votos
        FROM resultados WHERE corporacion = 'CA'
        GROUP BY municipio, puesto
    ) ca
    JOIN (
        SELECT municipio, puesto, SUM(votos) as votos
        FROM resultados WHERE corporacion = 'SE'
        GROUP BY municipio, puesto
    ) se
    ON ca.municipio = se.municipio AND ca.puesto = se.puesto
""", conn)
conn.close()

slope, intercept, r_value, p_value, std_err = stats.linregress(df["votos_ca"], df["votos_se"])

fig, ax = plt.subplots(figsize=(9, 7))

colores = {"TUNJA": "#1E477D", "PAIPA": "#E07B00", "SOGAMOSO": "#007C34", "DUITAMA": "#7B2D8B"}
for municipio, grupo in df.groupby("municipio"):
    ax.scatter(grupo["votos_ca"], grupo["votos_se"],
               label=municipio, alpha=0.7, s=60,
               color=colores.get(municipio, "gray"))

x_line = df["votos_ca"].sort_values()
y_line = intercept + slope * x_line
ax.plot(x_line, y_line, color="black", linestyle="--", linewidth=1.5, label="Regresión OLS")

ax.set_xlabel("Votos Cámara (CA) por puesto")
ax.set_ylabel("Votos Senado (SE) por puesto")
ax.set_title("Relación votos CA vs SE por puesto de votación")
ax.legend()
ax.annotate(f"r = {r_value:.3f}", xy=(0.05, 0.95), xycoords="axes fraction",
            fontsize=11, verticalalignment="top")

plt.tight_layout()
plt.savefig("viz/scatter_ca_se.png", dpi=150)

print(f"r={r_value:.3f} | pendiente={slope:.3f} | n_mesas={len(df)}")