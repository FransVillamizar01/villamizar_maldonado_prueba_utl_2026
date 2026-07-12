SELECT
    r.municipio,
    r.puesto,
    r.candidato,
    r.codpar,
    r.votos AS votos_candidato,
    tot.votos_partido,
    ROUND(CAST(r.votos AS FLOAT) / tot.votos_partido, 3) AS pct_dominancia
FROM resultados r
JOIN (
    SELECT municipio, puesto, corporacion, codpar, SUM(votos) AS votos_partido
    FROM resultados
    GROUP BY municipio, puesto, corporacion, codpar
) tot
ON r.municipio = tot.municipio
   AND r.puesto = tot.puesto
   AND r.corporacion = tot.corporacion
   AND r.codpar = tot.codpar
WHERE tot.votos_partido > 0
  AND CAST(r.votos AS FLOAT) / tot.votos_partido > 0.6
ORDER BY pct_dominancia DESC;