# VILLAMIZAR MALDONADO — Prueba Técnica UTL Senado 2026

## Candidato
Nombre: Frans Villamizar
Email: fsvillamizar@unibioyaca.edu.co
Fecha de entrega: [completa cuando entregues]

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

Headers necesarios: ninguno especial detectado más allá de los headers estándar del navegador (pendiente confirmar si el scraper programático los necesita).

## Municipios en la BD
[completar tras correr el ETL]

## Hallazgos principales
[completar tras correr las queries SQL]

## Bonus implementados
[completar al final] 