# Ilmanlaatudatan haku

Tämä on tehtävän ensimmäinen sovellus. Ohjelma hakee OpenAQ:sta ilmanlaatudataa ja tallentaa sen SQLite-tietokantaan.

Valitsin SQLite-tietokannan, koska sitä on helppo käyttää paikallisesti eikä erillistä tietokantapalvelinta tarvitse asentaa.

## Tietokannan rakenne

Tietokannan fyysinen malli on tiedostossa `schema.sql`.

Taulut ovat:

- `countries` = maat
- `cities` = kaupungit
- `locations` = mittauspaikat
- `sensors` = sensorit
- `measurements` = mittaukset

Yhdellä mittauspaikalla voi olla monta sensoria. Tämän takia sensorit ovat omassa taulussaan.

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

Oletuksena ohjelma hakee dataa yhden kuukauden ajalta yhdeltä sensorilta. Asetuksia voi vaihtaa `.env`-tiedostosta.

Tärkeimmät asetukset ovat:

- `OPENAQ_API_KEY` = oma OpenAQ API-avain
- `OPENAQ_SENSOR_ID` = haettavan sensorin id
- `OPENAQ_LOCATION_ID` = mittauspaikan id
- `DATE_FROM` ja `DATE_TO` = aikaväli
- `DATABASE_PATH` = tietokantatiedoston sijainti

Jos tietokantaa ei vielä ole, ohjelma luo sen automaattisesti.

## Käyttämäni OpenAQ endpoint

```text
https://api.openaq.org/v3/sensors/{sensor_id}/measurements
```
