WITH candidato_ca AS (
    SELECT municipio, puesto, codpar, candidato, SUM(votos) AS votos_cand
    FROM resultados
    WHERE corporacion = 'CA'
    GROUP BY municipio, puesto, codpar, candidato
),
partido_ca AS (
    SELECT municipio, puesto, codpar, SUM(votos) AS votos_partido_ca
    FROM resultados
    WHERE corporacion = 'CA'
    GROUP BY municipio, puesto, codpar
),
partido_se AS (
    SELECT municipio, puesto, codpar, SUM(votos) AS votos_partido_se
    FROM resultados
    WHERE corporacion = 'SE'
    GROUP BY municipio, puesto, codpar
)
SELECT
    c.municipio,
    c.puesto,
    c.candidato,
    c.codpar,
    ROUND((CAST(c.votos_cand AS FLOAT) / p_ca.votos_partido_ca) * p_se.votos_partido_se, 1) AS atribucion_se
FROM candidato_ca c
JOIN partido_ca p_ca
    ON c.municipio = p_ca.municipio AND c.puesto = p_ca.puesto AND c.codpar = p_ca.codpar
JOIN partido_se p_se
    ON c.municipio = p_se.municipio AND c.puesto = p_se.puesto AND c.codpar = p_se.codpar
WHERE p_ca.votos_partido_ca > 0
ORDER BY atribucion_se DESC
LIMIT 5;