SELECT
    ca.municipio,
    ca.puesto,
    ca.votos AS votos_ca_verde,
    se.votos AS votos_se_verde,
    ROUND(CAST(se.votos AS FLOAT) / NULLIF(ca.votos, 0), 3) AS ratio_arrastre
FROM
    (SELECT municipio, puesto, SUM(votos) AS votos
     FROM resultados
     WHERE codpar = 5 AND corporacion = 'CA'
     GROUP BY municipio, puesto) ca
JOIN
    (SELECT municipio, puesto, SUM(votos) AS votos
     FROM resultados
     WHERE codpar = 57 AND corporacion = 'SE'
     GROUP BY municipio, puesto) se
ON ca.municipio = se.municipio AND ca.puesto = se.puesto
ORDER BY ca.municipio, ratio_arrastre DESC;