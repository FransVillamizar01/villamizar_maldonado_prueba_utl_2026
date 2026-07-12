import requests

data = requests.get('https://resultadospreccongreso2026.registraduria.gov.co/json/nomenclator.json').json()
ambitos = data['amb'][0]['ambitos']
por_indice = {a['i']: a for a in ambitos}

# Tomamos el primer local de la primera zona de Tunja como muestra
indices_locales_tunja_zona01 = [4541, 6251, 6422, 6982, 10346, 11581]

for idx in indices_locales_tunja_zona01:
    local = por_indice[idx]
    print(local)