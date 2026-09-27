from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas


# ---------- Grower ----------

def create_grower(db: Session, grower: schemas.GrowerCreate) -> models.Grower:
    db_grower = models.Grower(**grower.model_dump())
    db.add(db_grower)
    db.commit()
    db.refresh(db_grower)
    return db_grower


def get_grower(db: Session, grower_id: int) -> Optional[models.Grower]:
    return db.query(models.Grower).filter(models.Grower.id == grower_id).first()


def list_growers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Grower]:
    return db.query(models.Grower).offset(skip).limit(limit).all()


def grower_reputation(db: Session, grower_id: int) -> Optional[float]:
    """Average quality signal (germination + purity*20 + trueness*20, roughly normalized)
    across every report left on this grower's seed lots."""
    reports = (
        db.query(models.QualityReport)
        .join(models.SeedLot, models.QualityReport.seed_lot_id == models.SeedLot.id)
        .filter(models.SeedLot.owner_id == grower_id)
        .all()
    )
    if not reports:
        return None
    scores = []
    for r in reports:
        parts = []
        if r.germination_rate is not None:
            parts.append(r.germination_rate)
        if r.purity_rating is not None:
            parts.append(r.purity_rating * 20)
        if r.trueness_to_type is not None:
            parts.append(r.trueness_to_type * 20)
        if parts:
            scores.append(sum(parts) / len(parts))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


# ---------- Seed Lot ----------

def create_seed_lot(db: Session, lot: schemas.SeedLotCreate) -> models.SeedLot:
    db_lot = models.SeedLot(**lot.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot


def get_seed_lot(db: Session, lot_id: int) -> Optional[models.SeedLot]:
    return db.query(models.SeedLot).filter(models.SeedLot.id == lot_id).first()


def list_seed_lots(
    db: Session,
    variety: Optional[str] = None,
    species: Optional[str] = None,
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[models.SeedLot]:
    q = db.query(models.SeedLot)
    if variety:
        q = q.filter(models.SeedLot.variety.ilike(f"%{variety}%"))
    if species:
        q = q.filter(models.SeedLot.species.ilike(f"%{species}%"))
    if owner_id:
        q = q.filter(models.SeedLot.owner_id == owner_id)
    return q.offset(skip).limit(limit).all()


def seed_lot_quality_summary(db: Session, lot_id: int) -> dict:
    row = (
        db.query(
            func.avg(models.QualityReport.germination_rate),
            func.avg(models.QualityReport.purity_rating),
            func.avg(models.QualityReport.trueness_to_type),
            func.count(models.QualityReport.id),
        )
        .filter(models.QualityReport.seed_lot_id == lot_id)
        .first()
    )
    avg_germ, avg_purity, avg_true, count = row
    exchange_count = (
        db.query(func.count(models.Exchange.id))
        .filter(models.Exchange.seed_lot_id == lot_id)
        .scalar()
    )
    return {
        "avg_germination_rate": round(avg_germ, 1) if avg_germ is not None else None,
        "avg_purity_rating": round(avg_purity, 1) if avg_purity is not None else None,
        "avg_trueness_to_type": round(avg_true, 1) if avg_true is not None else None,
        "report_count": count or 0,
        "exchange_count": exchange_count or 0,
    }


def get_lot_lineage(db: Session, lot_id: int) -> List[models.SeedLot]:
    """Walk parent_lot_id chain back to the original lot."""
    lineage = []
    current = get_seed_lot(db, lot_id)
    seen = set()
    while current and current.id not in seen:
        lineage.append(current)
        seen.add(current.id)
        current = (
            get_seed_lot(db, current.parent_lot_id) if current.parent_lot_id else None
        )
    return lineage


# ---------- Quality Report ----------

def create_quality_report(
    db: Session, lot_id: int, report: schemas.QualityReportCreate
) -> models.QualityReport:
    db_report = models.QualityReport(seed_lot_id=lot_id, **report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def list_quality_reports(db: Session, lot_id: int) -> List[models.QualityReport]:
    return (
        db.query(models.QualityReport)
        .filter(models.QualityReport.seed_lot_id == lot_id)
        .order_by(models.QualityReport.reported_at.desc())
        .all()
    )


# ---------- Exchange ----------

def create_exchange(db: Session, exchange: schemas.ExchangeCreate) -> models.Exchange:
    db_exchange = models.Exchange(**exchange.model_dump())
    db.add(db_exchange)
    db.commit()
    db.refresh(db_exchange)
    return db_exchange


def list_exchanges(
    db: Session, grower_id: Optional[int] = None, skip: int = 0, limit: int = 100
) -> List[models.Exchange]:
    q = db.query(models.Exchange)
    if grower_id:
        q = q.filter(
            (models.Exchange.from_grower_id == grower_id)
            | (models.Exchange.to_grower_id == grower_id)
        )
    return q.offset(skip).limit(limit).all()


# ---------- Network ----------

def network_stats(db: Session) -> dict:
    grower_count = db.query(func.count(models.Grower.id)).scalar() or 0
    seed_lot_count = db.query(func.count(models.SeedLot.id)).scalar() or 0
    exchange_count = db.query(func.count(models.Exchange.id)).scalar() or 0
    report_count = db.query(func.count(models.QualityReport.id)).scalar() or 0
    avg_germ = db.query(func.avg(models.QualityReport.germination_rate)).scalar()
    return {
        "grower_count": grower_count,
        "seed_lot_count": seed_lot_count,
        "exchange_count": exchange_count,
        "quality_report_count": report_count,
        "avg_germination_rate": round(avg_germ, 1) if avg_germ is not None else None,
    }


def network_graph(db: Session) -> dict:
    growers = db.query(models.Grower).all()
    nodes = []
    for g in growers:
        lot_count = (
            db.query(func.count(models.SeedLot.id))
            .filter(models.SeedLot.owner_id == g.id)
            .scalar()
            or 0
        )
        nodes.append(
            {
                "id": g.id,
                "name": g.name,
                "seed_lot_count": lot_count,
                "reputation_score": grower_reputation(db, g.id),
            }
        )

    exchanges = db.query(models.Exchange).all()
    edge_map = {}
    for ex in exchanges:
        key = (ex.from_grower_id, ex.to_grower_id)
        if key not in edge_map:
            edge_map[key] = {"count": 0, "lots": set()}
        edge_map[key]["count"] += 1
        if ex.seed_lot:
            edge_map[key]["lots"].add(ex.seed_lot.variety)

    edges = [
        {
            "from_grower_id": k[0],
            "to_grower_id": k[1],
            "exchange_count": v["count"],
            "lots": sorted(v["lots"]),
        }
        for k, v in edge_map.items()
    ]

    return {"nodes": nodes, "edges": edges}
