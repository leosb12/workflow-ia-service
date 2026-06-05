import urllib.request, json

data = json.dumps({
    'prompt': 'que los adm puedan editar el documento doc en la actividad Subir archivo y que sea tipo PDF', 
    'workflow': {
        'nodes': [{
            'id': '1', 
            'name': 'Subir archivo', 
            'type': 'task', 
            'formulario': [{
                'campo': 'doc', 
                'tipo': 'DOCUMENTO_COLABORATIVO'
            }]
        }]
    }, 
    'context': {}
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8001/api/ia/editar-flujo', data=data, headers={'Content-Type': 'application/json'})

try:
    res = urllib.request.urlopen(req)
    with open('res.json', 'w', encoding='utf-8') as f:
        f.write(res.read().decode('utf-8'))
except Exception as e:
    with open('res.json', 'w', encoding='utf-8') as f:
        f.write(str(e))
