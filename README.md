# VILLAMIZAR MALDONADO — Prueba Técnica UTL Senado 2026

## Candidato
Nombre: Frans Villamizar
Email: fsvillamizar@unibioyaca.edu.co
Fecha de entrega: [NN]

## Instalación
pip install -r requirements.txt
Python 3.x (verificar version con: python --version)

## Pipeline de ejecución
python scraper/scraper.py
python db/etl.py
python outputs/generar_manifest.py

## API

Fuente: https://resultadospreccongreso2026.registraduria.gov.co

Patrón de URL:
https://resultadospreccongreso2026.registraduria.gov.co/json/ACT/{corporacion}/{codigo_divipola}.json

- corporacion: CA (Cámara) o SE (Senado), como texto literal en la URL
- codigo_divipola: código DANE de 7 dígitos por municipio
- ACT: constante (posiblemente indica "actual" o boletín vigente)

Códigos DIVIPOLA de los municipios objetivo:
| Municipio | Código |
|---|---|
| Tunja | 0700001 |
| Paipa | 0700181 |
| Sogamoso | 0700277 |
| Duitama | 0700079 |

Estructura del JSON de resultados (ej: /resultados/0/0700001/0):
Cada partido es un objeto de nivel superior con estos campos:
- codpar: código del partido
- cam: posible indicador de corporación
- vot: votos totales del partido en ese municipio
- pvot: porcentaje de votos del partido
- carg, cargElectos, cargEmpatados: curules asignadas/electas/empatadas
- cantotabla: array de candidatos del partido, cada uno con:
  - amb: código de municipio
  - codcan: código del candidato
  - cedula: cédula
  - nomcan, apecan: nombre y apellido
  - nomcan2, apecan2: segundo nombre/apellido (opcional)
  - vot, pvot: votos y porcentaje del candidato
  - pref: voto preferente
  - empate: indicador de empate

Nomenclador de municipios: disponible en nomenclator.json, cargado junto con la página principal — contiene el mapeo completo nombre-codigo para todos los municipios de Colombia.

Headers necesarios: ninguno especial detectado más allá de los headers estándar del navegador.

## Municipios en la BD
- TUNJA: 1361 filas
- PAIPA: 1361 filas
- SOGAMOSO: 1361 filas
- DUITAMA: 1361 filas

Total: 5444 filas | 83 partidos distintos identificados en la tabla `partidos`

## Hallazgos principales
**Nota sobre nombres de partidos:** de los 83 partidos con votos en los 4 municipios, solo se confirmó el nombre real de 6 (Alianza Verde, Pacto Histórico, Centro Democrático, Conservador — Cámara y Senado según corresponda) cruzando con la tabla de colores del PDF de la prueba. El resto quedó registrado con el código de partido como placeholder (`PARTIDO_{codpar}`), ya que el nomenclador de la API usa una numeración distinta (ID nacional) a la que aparece en los resultados por municipio (índice de circunscripción), y no había forma directa de cruzarlos con certeza para todos los casos.

## Bonus implementados
- Flag --preflight en el scraper: muestra la lista de municipios a procesar sin hacer ninguna petición HTTP (Reto 1.2, +3 pts)
- 3 índices SQLite con justificación explícita en schema.sql: idx_resultados_municipio, idx_resultados_codpar, idx_resultados_puesto (Reto 2.1, +2 pts)