from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal, engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Seed Saving Quality Network Tracker",
    description=(
        "Backend + frontend for tracking an informal seed-saving network: who's "
        "saving what, how well it performs, and how seed lots move between growers."
    ),
    version="1.0.0",
)

# CORS left open in case anyone wants to hit the API from a separate origin
# during development; the shipped frontend is same-origin and doesn't need it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the single-page frontend at "/" and its assets under "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "seed-saving-network-tracker"}


# ---------------------------------------------------------------- Growers

@app.post("/growers", response_model=schemas.GrowerOut, tags=["growers"])
def create_grower(grower: schemas.GrowerCreate, db: Session = Depends(get_db)):
    return crud.create_grower(db, grower)


@app.get("/growers", response_model=List[schemas.GrowerOut], tags=["growers"])
def list_growers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_growers(db, skip, limit)


@app.get("/growers/{grower_id}", response_model=schemas.GrowerDetail, tags=["growers"])
def get_grower(grower_id: int, db: Session = Depends(get_db)):
    grower = crud.get_grower(db, grower_id)
    if not grower:
        raise HTTPException(status_code=404, detail="Grower not found")
    return schemas.GrowerDetail(
        **schemas.GrowerOut.model_validate(grower).model_dump(),
        seed_lot_count=len(grower.seed_lots),
        reputation_score=crud.grower_reputation(db, grower_id),
    )


@app.get(
    "/growers/{grower_id}/exchanges",
    response_model=List[schemas.ExchangeOut],
    tags=["growers"],
)
def get_grower_exchanges(grower_id: int, db: Session = Depends(get_db)):
    if not crud.get_grower(db, grower_id):
        raise HTTPException(status_code=404, detail="Grower not found")
    return crud.list_exchanges(db, grower_id=grower_id)


# ---------------------------------------------------------------- Seed Lots

@app.post("/seed-lots", response_model=schemas.SeedLotOut, tags=["seed lots"])
def create_seed_lot(lot: schemas.SeedLotCreate, db: Session = Depends(get_db)):
    if not crud.get_grower(db, lot.owner_id):
        raise HTTPException(status_code=404, detail="Owner (grower) not found")
    if lot.parent_lot_id and not crud.get_seed_lot(db, lot.parent_lot_id):
        raise HTTPException(status_code=404, detail="Parent seed lot not found")
    return crud.create_seed_lot(db, lot)


@app.get("/seed-lots", response_model=List[schemas.SeedLotOut], tags=["seed lots"])
def list_seed_lots(
    variety: Optional[str] = None,
    species: Optional[str] = None,
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.list_seed_lots(db, variety, species, owner_id, skip, limit)


@app.get(
    "/seed-lots/{lot_id}", response_model=schemas.SeedLotDetail, tags=["seed lots"]
)
def get_seed_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = crud.get_seed_lot(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    summary = crud.seed_lot_quality_summary(db, lot_id)
    return schemas.SeedLotDetail(
        **schemas.SeedLotOut.model_validate(lot).model_dump(),
        owner=schemas.GrowerOut.model_validate(lot.owner),
        **summary,
    )


@app.get(
    "/seed-lots/{lot_id}/lineage",
    response_model=List[schemas.SeedLotOut],
    tags=["seed lots"],
)
def get_seed_lot_lineage(lot_id: int, db: Session = Depends(get_db)):
    if not crud.get_seed_lot(db, lot_id):
        raise HTTPException(status_code=404, detail="Seed lot not found")
    return crud.get_lot_lineage(db, lot_id)


# ---------------------------------------------------------------- Quality Reports

@app.post(
    "/seed-lots/{lot_id}/quality-reports",
    response_model=schemas.QualityReportOut,
    tags=["quality"],
)
def add_quality_report(
    lot_id: int, report: schemas.QualityReportCreate, db: Session = Depends(get_db)
):
    if not crud.get_seed_lot(db, lot_id):
        raise HTTPException(status_code=404, detail="Seed lot not found")
    if not crud.get_grower(db, report.reporter_id):
        raise HTTPException(status_code=404, detail="Reporter (grower) not found")
    return crud.create_quality_report(db, lot_id, report)


@app.get(
    "/seed-lots/{lot_id}/quality-reports",
    response_model=List[schemas.QualityReportOut],
    tags=["quality"],
)
def get_quality_reports(lot_id: int, db: Session = Depends(get_db)):
    if not crud.get_seed_lot(db, lot_id):
        raise HTTPException(status_code=404, detail="Seed lot not found")
    return crud.list_quality_reports(db, lot_id)


# ---------------------------------------------------------------- Exchanges

@app.post("/exchanges", response_model=schemas.ExchangeOut, tags=["exchanges"])
def create_exchange(exchange: schemas.ExchangeCreate, db: Session = Depends(get_db)):
    if not crud.get_seed_lot(db, exchange.seed_lot_id):
        raise HTTPException(status_code=404, detail="Seed lot not found")
    if not crud.get_grower(db, exchange.from_grower_id):
        raise HTTPException(status_code=404, detail="from_grower not found")
    if not crud.get_grower(db, exchange.to_grower_id):
        raise HTTPException(status_code=404, detail="to_grower not found")
    if exchange.from_grower_id == exchange.to_grower_id:
        raise HTTPException(status_code=400, detail="from_grower and to_grower must differ")
    return crud.create_exchange(db, exchange)


@app.get("/exchanges", response_model=List[schemas.ExchangeOut], tags=["exchanges"])
def list_exchanges(
    grower_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.list_exchanges(db, grower_id, skip, limit)


# ---------------------------------------------------------------- Network

@app.get("/network/stats", response_model=schemas.NetworkStats, tags=["network"])
def get_network_stats(db: Session = Depends(get_db)):
    return crud.network_stats(db)


@app.get("/network/graph", response_model=schemas.NetworkGraph, tags=["network"])
def get_network_graph(db: Session = Depends(get_db)):
    """Nodes = growers, edges = exchange relationships. Feed straight into
    a force-directed graph (d3, vis.js, react-force-graph, etc.) on the frontend."""
    return crud.network_graph(db)
