# Seed Saving Quality Network Tracker

One FastAPI app — API + frontend together, one process, one port — for
tracking an informal seed-saving network: who's saving what seed, how well
it performs when grown out, and how lots move between growers over time.

## Data model

- **Grower** — a person in the network.
- **SeedLot** — a saved batch of seed. Has `parent_lot_id` so you can trace
  lineage across generations (e.g. Asha's tomato lot → Ravi grows it out →
  Ravi's gen-2 lot points back to Asha's as its parent).
- **QualityReport** — germination rate, purity rating, trueness-to-type,
  submitted by *whoever grew that lot out* — not just the original saver.
  This is what makes quality a network signal rather than a self-report.
- **Exchange** — a lot moving from one grower to another. These are the
  edges of the network graph.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: populate with sample data for a demo
python seed_demo_data.py

# run the app
uvicorn main:app --reload
```

Open **http://localhost:8000** — that's the whole app, frontend included.
API docs (interactive, auto-generated): http://localhost:8000/docs

The SQLite file (`seed_network.db`) is created automatically on first run.
Delete it any time to reset.

## Project layout

```
main.py, models.py, schemas.py, crud.py, database.py   -- the API
static/index.html                                       -- the frontend
seed_demo_data.py                                        -- demo data loader
```

`main.py` serves `static/index.html` at `/` and the API at every other
path, so the frontend's fetch calls are same-origin (`/growers`,
`/seed-lots`, etc.) — no CORS config or backend-URL box needed.

## Endpoints

### Growers
| Method | Path | Description |
|---|---|---|
| POST | `/growers` | Create a grower |
| GET | `/growers` | List growers |
| GET | `/growers/{id}` | Grower detail incl. seed lot count + reputation score |
| GET | `/growers/{id}/exchanges` | All exchanges this grower sent or received |

### Seed Lots
| Method | Path | Description |
|---|---|---|
| POST | `/seed-lots` | Create a seed lot |
| GET | `/seed-lots?variety=&species=&owner_id=` | List/filter seed lots |
| GET | `/seed-lots/{id}` | Detail incl. aggregated quality scores |
| GET | `/seed-lots/{id}/lineage` | Walk the parent chain back to the original lot |

### Quality Reports
| Method | Path | Description |
|---|---|---|
| POST | `/seed-lots/{id}/quality-reports` | Add a quality report to a lot |
| GET | `/seed-lots/{id}/quality-reports` | List reports for a lot |

### Exchanges
| Method | Path | Description |
|---|---|---|
| POST | `/exchanges` | Record a seed lot moving between two growers |
| GET | `/exchanges?grower_id=` | List exchanges, optionally filtered by grower |

### Network
| Method | Path | Description |
|---|---|---|
| GET | `/network/stats` | Headline numbers: growers, lots, exchanges, avg germination |
| GET | `/network/graph` | `{nodes, edges}` — feed directly into d3 / vis.js / react-force-graph for a network visualization |

## Reputation score

A grower's `reputation_score` (0–100) is the average, across every quality
report left on any of their seed lots, of:
- germination rate (already 0–100)
- purity rating × 20 (1–5 scale → 0–100)
- trueness-to-type × 20 (1–5 scale → 0–100)

This rewards growers whose seed reliably performs well for *other* people
who grow it out — the core signal an informal seed network actually cares
about.

## Note on this environment

This was built and syntax-checked (Python compiled, frontend JS parsed) in
a sandbox without outbound network access, so the dependency install and
live server boot haven't been verified end-to-end here. Run the Setup
steps above locally before your demo — it's standard FastAPI/SQLAlchemy
with StaticFiles, so it should come up cleanly, but test it once ahead of
time.

## Ideas if you have extra hackathon time
- Simple grower "trust" endpoint: growers two exchanges apart in the graph
- Photo upload on quality reports (pest/disease documentation)
- Seasonal reminders ("this lot hasn't been regrown in 2 years")
- Auth (currently none — anyone can post as any grower_id, fine for a demo)
