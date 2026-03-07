# pingpal

Initial scaffold for a Messenger group chat agent backend.

## Run tests

```bash
python -m pip install -e '.[dev]'
pytest
```

## Run app

```bash
uvicorn pingpal.main:app --reload
```
