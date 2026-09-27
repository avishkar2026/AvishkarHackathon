from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Grower ----------

class GrowerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class GrowerCreate(GrowerBase):
    pass


class GrowerOut(GrowerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    joined_at: datetime


class GrowerDetail(GrowerOut):
    model_config = ConfigDict(from_attributes=True)
    seed_lot_count: int = 0
    reputation_score: Optional[float] = None  # avg quality across all their lots


# ---------- Seed Lot ----------

class SeedLotBase(BaseModel):
    variety: str
    species: Optional[str] = None
    source: Optional[str] = None
    date_saved: Optional[datetime] = None
    description: Optional[str] = None
    generation: int = 1
    parent_lot_id: Optional[int] = None


class SeedLotCreate(SeedLotBase):
    owner_id: int


class SeedLotOut(SeedLotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    created_at: datetime


class SeedLotDetail(SeedLotOut):
    model_config = ConfigDict(from_attributes=True)
    owner: GrowerOut
    avg_germination_rate: Optional[float] = None
    avg_purity_rating: Optional[float] = None
    avg_trueness_to_type: Optional[float] = None
    report_count: int = 0
    exchange_count: int = 0


# ---------- Quality Report ----------

class QualityReportBase(BaseModel):
    germination_rate: Optional[float] = Field(None, ge=0, le=100)
    purity_rating: Optional[int] = Field(None, ge=1, le=5)
    trueness_to_type: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class QualityReportCreate(QualityReportBase):
    reporter_id: int


class QualityReportOut(QualityReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    seed_lot_id: int
    reporter_id: int
    reported_at: datetime


# ---------- Exchange ----------

class ExchangeBase(BaseModel):
    seed_lot_id: int
    from_grower_id: int
    to_grower_id: int
    quantity: Optional[str] = None
    exchange_date: Optional[datetime] = None
    notes: Optional[str] = None


class ExchangeCreate(ExchangeBase):
    pass


class ExchangeOut(ExchangeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Network graph ----------

class NetworkNode(BaseModel):
    id: int
    name: str
    seed_lot_count: int
    reputation_score: Optional[float] = None


class NetworkEdge(BaseModel):
    from_grower_id: int
    to_grower_id: int
    exchange_count: int
    lots: List[str] = []  # variety names exchanged


class NetworkGraph(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]


class NetworkStats(BaseModel):
    grower_count: int
    seed_lot_count: int
    exchange_count: int
    quality_report_count: int
    avg_germination_rate: Optional[float] = None
