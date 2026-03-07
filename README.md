# pingpal

Initial scaffold for a Messenger group chat agent backend.

## Issue Tracking (Beads)

This repo uses `bd` (Beads) for task tracking.

```bash
# Show unblocked work
bd ready --json

# Claim work
bd update <id> --claim --json

# Close work
bd close <id> --reason "Completed" --json
```

If this is your first time in the repo:

```bash
bd onboard
```

## Run tests

```bash
python -m pip install -e '.[dev]'
pytest
```

## Run app

```bash
uvicorn pingpal.main:app --reload
```
