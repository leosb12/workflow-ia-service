import urllib.request, urllib.error, json

data = json.dumps({
    'prompt': 'que los adm puedan editar el documento doc en la actividad Subir archivo', 
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
    print(res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
