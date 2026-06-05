import urllib.request, json

data = json.dumps({
    'prompt': 'agrega un documento colaborativo de tipo Word para que los adm puedan editar en la actividad Subir archivo', 
    'workflow': {
        'nodes': [{
            'id': '1', 
            'name': 'Subir archivo', 
            'type': 'task', 
            'formulario': []
        }]
    }, 
    'context': {}
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8001/api/ia/editar-flujo', data=data, headers={'Content-Type': 'application/json'})

try:
    res = urllib.request.urlopen(req)
    with open('res_add.json', 'w', encoding='utf-8') as f:
        f.write(res.read().decode('utf-8'))
except Exception as e:
    with open('res_add.json', 'w', encoding='utf-8') as f:
        f.write(str(e))
