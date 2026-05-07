# FireHox Connect Backend

FastAPI backend for the FireHox Connect MVP.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

For production-reproducible installs, use the pinned constraints file:

```bash
pip install -r requirements.txt -c constraints.txt
```

## Run

```bash
source .venv/bin/activate
python run.py
```

## Verification

```bash
source .venv/bin/activate
python -c "from app.main import app; print(app.title)"
```

```bash
source .venv/bin/activate
python -m pytest tests -q
```

Prompt 2 adds the base FastAPI app, an async `/health` route, and a uvicorn entrypoint.
