import http.client
import dns.resolver

name = 'www.koziol.lan'
for label, server in [('BIND PROD', '192.168.60.14'), ('AdGuard PROD', '192.168.60.15')]:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.timeout = 3
    resolver.lifetime = 6
    addresses = sorted(answer.address for answer in resolver.resolve(name, 'A'))
    print(f'{label} @{server}: {name} -> {addresses}', flush=True)
    assert addresses == ['192.168.60.14'], f'Niepoprawny rekord A: {addresses}'
    connection = http.client.HTTPConnection(addresses[0], timeout=5)
    try:
        connection.request('GET', '/health', headers={'Host': name})
        response = connection.getresponse()
        body = response.read().decode().strip()
        print(f'HTTP http://{name}/health przez {label}: {response.status}, {body}', flush=True)
        assert response.status == 200 and body == 'OK', 'Portal nie jest zdrowy'
    finally:
        connection.close()
print('MONITORING OK: oba serwery DNS i portal odpowiadaja poprawnie.', flush=True)
