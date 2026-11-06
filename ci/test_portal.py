import json
import os
import time
import urllib.request

environment = os.environ['CEL']
server = {'TEST': '192.168.60.13', 'PROD': '192.168.60.14'}[environment]
expected = os.environ['OCZEKIWANY_BUILD']
base = 'http://' + server


def get(path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        assert response.status == 200, (path, response.status)
        return response.read().decode('utf-8')


for attempt in range(1, 11):
    try:
        page = get('/')
        assert 'kozioł' in page.casefold() or 'koziol' in page.casefold(), 'Brak nazwiska autora'
        assert get('/health').strip() == 'OK', 'Niepoprawny health'
        version = json.loads(get('/version.json'))
        assert str(version['build']) == expected, (version, expected)
        assert json.loads(get('/srodowisko.json'))['srodowisko'] == environment
        print(f'OK: {base}, HTTP 200, autor, health=OK, build={expected}, {environment}')
        print(json.dumps(version, ensure_ascii=False))
        break
    except Exception as error:
        print(f'Proba {attempt}/10: {error}', flush=True)
        if attempt == 10:
            raise
        time.sleep(3)
