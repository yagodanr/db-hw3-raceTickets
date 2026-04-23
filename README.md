# Race Ticketing App

First Flask draft for the HW3 motorsport ticketing domain.

## What this draft does

- starts a local Flask server;
- connects to MySQL using environment variables;
- checks that the `RaceTicketingDB` schema is reachable;
- shows live counts for the core HW3 tables.

## Run

```bash
cd workspace/HW3/web/race_ticketing_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export $(grep -v '^#' .env | xargs)
python app.py
```

Open `http://127.0.0.1:5000/`.

## Current routes

- `/` dashboard page
- `/db-status` JSON connectivity check

## Next step

Add the first CRUD forms for the HW3 entities, starting with race events, visitors, and race tickets.
