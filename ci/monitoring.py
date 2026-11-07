import http.client
import dns.resolver
from pathlib import Path
import time

name = 'www.koziol.lan'
results = []
failures = []
for label, server in [('BIND PROD', '192.168.60.14'), ('AdGuard PROD', '192.168.60.15')]:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.timeout = 3
    resolver.lifetime = 6
    try:
        for attempt in range(3):
            try:
                addresses = sorted(answer.address for answer in resolver.resolve(name, 'A'))
                break
            except (dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers):
                if attempt == 2:
                    raise
                time.sleep(2)
        assert addresses == ['192.168.60.14'], f'Niepoprawny rekord A: {addresses}'
        results.append(f'OK DNS {label} @{server}: {name} -> {addresses}')
    except Exception as error:
        failures.append(f'BLAD DNS {label} @{server}: {error}')
        continue
    for path in ['/', '/health']:
        connection = http.client.HTTPConnection(addresses[0], timeout=5)
        try:
            connection.request('GET', path, headers={'Host': name})
            response = connection.getresponse()
            body = response.read().decode().strip()
            assert response.status == 200, f'HTTP {response.status}'
            if path == '/health':
                assert body == 'OK', f'Niepoprawna odpowiedz health: {body[:80]}'
            results.append(f'OK HTTP http://{name}{path} przez {label}: {response.status}'
                           + (', health=OK' if path == '/health' else ''))
        except Exception as error:
            failures.append(f'BLAD HTTP http://{name}{path} przez {label}: {error}')
        finally:
            connection.close()
report = '\n'.join(results + failures) + '\n'
Path('monitoring-wynik.txt').write_text(report, encoding='utf-8')
print(report, flush=True)
if failures:
    raise SystemExit(1)
print('MONITORING OK: oba serwery DNS oraz HTTP / i /health odpowiadaja poprawnie.', flush=True)
