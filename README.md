# OpenAQ data importer

Tämä repositorio sisältää pienen Python-sovelluksen, joka hakee OpenAQ API v3 -rajapinnasta ilmanlaatumittauksia ja tallentaa ne relaatiotietokantaan.

Tietokantana käytetään SQLiteä. Sama relaatiomalli toimii myös MySQLissä pienin tyyppimuutoksin.

## Tietokantamalli

Fyysinen malli on tiedostossa [schema.sql](schema.sql). Malli huomioi tehtävän vaatimukset:

- maa tallennetaan tauluun `countries`
- kaupunki tallennetaan tauluun `cities`
- mittauspaikka tallennetaan tauluun `locations`
- sensorit tallennetaan tauluun `sensors`
- mittausarvot tallennetaan tauluun `measurements`

Yhdellä mittauspaikalla voi olla monta sensoria. Tämä ratkaisee tilanteen, jossa yksi CSV- tai API-lähde sisältää useita eri sensoreita.

## Asennus

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Lisää `.env`-tiedostoon OpenAQ API -avain.

## Käyttö

```powershell
python src\import_openaq.py
```

Oletuksena sovellus hakee mittauksia yhden kuukauden ajalta yhdeltä sensorilta. Muuta asetukset `.env`-tiedostossa:

- `OPENAQ_API_KEY`
- `OPENAQ_SENSOR_ID`
- `OPENAQ_LOCATION_ID`
- `OPENAQ_COUNTRY_CODE`
- `OPENAQ_COUNTRY_NAME`
- `OPENAQ_CITY_NAME`
- `OPENAQ_LOCATION_NAME`
- `DATE_FROM`
- `DATE_TO`
- `DATABASE_PATH`

Tietokanta luodaan automaattisesti, jos sitä ei vielä ole.

## Lähde

OpenAQ API v3 käyttää sensorikohtaisia mittausresursseja:

`https://api.openaq.org/v3/sensors/{sensor_id}/measurements`
