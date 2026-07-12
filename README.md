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

Patrón de URL de resultados:
https://resultadospreccongreso2026.registraduria.gov.co/json/ACT/{corporacion}/{codigo}.json

- corporacion: CA (Cámara) o SE (Senado), como texto literal en la URL
- codigo: puede ser código de municipio (7 dígitos), zona (9 dígitos) o puesto de votación (13 dígitos) — el scraper usa el nivel de puesto para máximo detalle
- ACT: constante (posiblemente indica "actual" o boletín vigente)

Endpoint de nomenclador territorial: /json/nomenclator.json
Contiene el árbol completo Departamento→Municipio→Zona→Puesto (campo `amb[0].ambitos`, con niveles `l`: 2=departamento, 3=municipio, 4=zona, 6=puesto). Cada nodo tiene un código `c` que se usa directo en el endpoint de resultados. Este archivo fue clave para descubrir la jerarquía completa y obtener los códigos de los puestos de votación individuales.

Códigos DIVIPOLA de los municipios objetivo:
| Municipio | Código |
|---|---|
| Tunja | 0700001 |
| Paipa | 0700181 |
| Sogamoso | 0700277 |
| Duitama | 0700079 |

Estructura del JSON de resultados (ej: /json/ACT/CA/0700001010005.json):
Cada partido es un objeto de nivel superior con estos campos:
- codpar: código del partido
- cam: posible indicador de corporación
- vot: votos totales del partido en ese puesto
- pvot: porcentaje de votos del partido
- carg, cargElectos, cargEmpatados: curules asignadas/electas/empatadas
- cantotabla: array de candidatos del partido, cada uno con:
  - amb: código del puesto de votación
  - codcan: código del candidato
  - cedula: cédula
  - nomcan, apecan: nombre y apellido
  - nomcan2, apecan2: segundo nombre/apellido (opcional)
  - vot, pvot: votos y porcentaje del candidato
  - pref: voto preferente
  - empate: indicador de empate

Nomenclador de municipios: disponible en nomenclator.json, contiene el mapeo completo nombre-codigo para todos los municipios de Colombia, así como el árbol territorial completo hasta el nivel de puesto de votación.

Headers necesarios: ninguno especial detectado más allá de los headers estándar del navegador.

## Municipios en la BD
- TUNJA: 35386 filas (26 puestos de votación)
- PAIPA: 9527 filas (7 puestos de votación)
- SOGAMOSO: 24498 filas (18 puestos de votación)
- DUITAMA: 29942 filas (22 puestos de votación)

Total: 99353 filas | 83 partidos distintos identificados

## Hallazgos principales

**Nota sobre nivel de detalle:** inicialmente el endpoint de resultados por municipio (`/json/ACT/{corporacion}/{codigo_municipio}.json`) solo traía el consolidado a nivel de todo el municipio. Investigando la estructura de `nomenclator.json` se descubrió el árbol territorial completo (Departamento → Municipio → Zona → Puesto de votación), lo que permitió obtener el desglose real por puesto individual (código de 13 dígitos), tal como lo requiere la tarea 3.1.

**Nota sobre nombres de partidos:** de los 83 partidos con votos en los 4 municipios, solo se confirmó el nombre real de 6 (Alianza Verde, Pacto Histórico, Centro Democrático, Conservador — Cámara y Senado según corresponda) cruzando con la tabla de colores del PDF de la prueba. El resto quedó registrado con el código de partido como placeholder (`PARTIDO_{codpar}`), ya que el nomenclador nacional de partidos usa una numeración distinta (ID nacional) a la que aparece en los resultados por puesto (índice de circunscripción), y no había forma directa de cruzarlos con certeza para todos los casos.

**Sobre "SOLO POR LA LISTA" en la query de dominancia extrema (3.2):** de los 1248 casos de dominancia >60% encontrados, una parte significativa corresponde a votos marcados como "SOLO POR LA LISTA" (codcan=0), que representa a electores que votaron por el partido sin marcar un candidato específico — no es un error de los datos ni del scraper, es una categoría real del sistema de voto preferente colombiano. En mesas pequeñas donde solo hubo unos pocos votos para un partido y ninguno fue a un candidato individual, "SOLO POR LA LISTA" concentra automáticamente el 100% de esos votos. La query se dejó fiel a la definición literal del PDF ("un candidato concentra >60% de los votos de su partido"), ya que dentro de la estructura de datos de la API este registro es tratado como un candidato más (mismo nivel que los reales, con código propio). Para un análisis más orientado a candidatos reales, se recomendaría excluir codcan=0 en futuras iteraciones.

## Bonus implementados
- Flag --preflight en el scraper: consulta el nomenclador y muestra la cantidad de puestos a procesar por municipio, sin hacer ninguna petición de resultados (Reto 1.2, +3 pts)
- 3 índices SQLite con justificación explícita en schema.sql: idx_resultados_municipio, idx_resultados_codpar, idx_resultados_puesto (Reto 2.1, +2 pts)
**Por qué el top CA no siempre coincide con el top de atribución SE (bonus 3.3):** la atribución SE de un candidato depende de 2 factores multiplicados: (1) qué tan fuerte es el candidato dentro de su propio partido en Cámara, y (2) qué tan fuerte fue ese mismo partido en Senado en ese puesto. Un candidato puede ser el más votado de su partido en CA, pero si su partido tuvo un resultado débil en SE en ese puesto, su atribución baja proporcionalmente. Esto se ve reflejado en el top 5: "SOLO POR LA LISTA" (Duitama, partido 10) aparece en la posición #4 con 338.2 votos atribuidos, no porque sea un "candidato" fuerte individualmente, sino porque el partido 10 tuvo un resultado muy fuerte en Senado en ese puesto específico, y una porción grande de los votos de Cámara de ese partido fueron "solo por la lista" — inflando su atribución proporcional pese a no ser una persona real compitiendo por votos individuales.