# Portal firmy KoziołNet (repozytorium `portal_koziol`)

Statyczny portal wewnętrzny wdrażany przez Ansible jako kontener Nginx na serwery TEST i PROD.
Potok wdrożeniowy w Jenkins jest częścią projektu do samodzielnego wykonania.

## Zawartość

| Plik / katalog | Przeznaczenie |
|---|---|
| `strona/index.html` | Strona portalu (wyświetla dane z `version.json` i `srodowisko.json`, na TEST - baner) |
| `strona/health` | Plik do testów dostępności - adres `/health` zwraca `OK` |
| `strona/version.json` | Plik **przykładowy** - potok nadpisuje go podczas przygotowania paczki |
| `wdrozenie_portalu.yml` | Playbook: Docker + kontener Nginx z zawartością katalogu `strona/` |
| `zadania/docker.yml` | Instalacja Docker Engine (dołączana do playbooka) |
| `inventory.yml` | Serwery w grupach `test` i `prod` (konto `deploy`, zmienna `portal_srodowisko`) |
| `ansible.cfg`, `requirements.yml`, `.ansible-lint` | Konfiguracja Ansible, wymagane kolekcje, konfiguracja lintera |

## Paczka, wersja i środowisko

Artefaktem potoku jest **paczka wdrożeniowa**: katalog `strona/` z wygenerowanym plikiem
`version.json` oraz pliki Ansible (playbook, `zadania/`, inwentarz, `ansible.cfg`). Ta sama paczka
trafia najpierw na TEST, a po udanym teście - bez ponownego budowania - na PROD.

1. **`strona/version.json`** - generowany przez potok podczas przygotowania paczki. Zawiera
   wyłącznie dane paczki (nie zawiera nazwy środowiska, dzięki czemu paczka na TEST i PROD jest
   identyczna):

   ```json
   {
     "build": "42",
     "commit": "1a2b3c4",
     "data": "2026-10-03T12:34:56+02:00"
   }
   ```

   Pole `build` musi zawierać numer budowania Jenkins, z którego pochodzi paczka - na tej
   podstawie test po wdrożeniu sprawdza, czy na serwerze działa właściwa wersja.

2. **`srodowisko.json`** - zapisywany na serwerze przez playbook na podstawie zmiennej
   `portal_srodowisko` z inwentarza (`{"srodowisko": "TEST"}` lub `{"srodowisko": "PROD"}`).
   Nie należy go umieszczać w repozytorium ani w paczce.

## Wdrożenie (kontrakt dla potoku)

```bash
ansible-playbook wdrozenie_portalu.yml --limit test     # lub --limit prod
```

Klucz prywatny SSH do konta `deploy` powinien pochodzić z Jenkins Credentials
(np. parametr `credentialsId` kroku `ansiblePlaybook`).

Test po wdrożeniu - minimalne kryteria:

| Adres | Oczekiwany wynik |
|---|---|
| `/` | kod HTTP 200, treść zawiera nazwisko autora |
| `/health` | tekst `OK` |
| `/version.json` | `build` = numer budowania wdrażanej paczki |
| `/srodowisko.json` | `srodowisko` = `TEST` lub `PROD` - zgodnie z serwerem |

Playbook jest idempotentny, a pliki usunięte z katalogu `strona/` znikają także z serwera.

## Uruchomienie ręczne (z AGENT)

```bash
ansible-galaxy collection install -r requirements.yml   # jeżeli brak kolekcji community.docker
ansible-playbook wdrozenie_portalu.yml --limit test --private-key ~/.ssh/jenkins
```

## Do wykonania samodzielnie (nie ma w tym repozytorium)

- `Jenkinsfile` potoku `portal_koziol` (Część 2, pkt 3),
- potok monitorujący `monitoring_koziol` (Część 2, pkt 4).
