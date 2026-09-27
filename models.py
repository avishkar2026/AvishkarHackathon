from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Grower(Base):
    """A member of the informal seed-saving network."""

    __tablename__ = "growers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    location = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    seed_lots = relationship(
        "SeedLot", back_populates="owner", foreign_keys="SeedLot.owner_id"
    )
    quality_reports = relationship("QualityReport", back_populates="reporter")
    exchanges_sent = relationship(
        "Exchange", back_populates="from_grower", foreign_keys="Exchange.from_grower_id"
    )
    exchanges_received = relationship(
        "Exchange", back_populates="to_grower", foreign_keys="Exchange.to_grower_id"
    )


class SeedLot(Base):
    """A specific saved batch of seed, trackable across generations and owners."""

    __tablename__ = "seed_lots"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("growers.id"), nullable=False)
    variety = Column(String, nullable=False)
    species = Column(String, nullable=True)
    source = Column(String, nullable=True)  # "own harvest", "traded", "purchased", etc.
    date_saved = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    generation = Column(Integer, default=1)  # seasons this lineage has been saved
    parent_lot_id = Column(Integer, ForeignKey("seed_lots.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Grower", back_populates="seed_lots", foreign_keys=[owner_id])
    parent_lot = relationship("SeedLot", remote_side=[id])
    quality_reports = relationship(
        "QualityReport", back_populates="seed_lot", cascade="all, delete-orphan"
    )
    exchanges = relationship("Exchange", back_populates="seed_lot")


class QualityReport(Base):
    """A quality data point on a seed lot, submitted by whoever grew it out."""

    __tablename__ = "quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    seed_lot_id = Column(Integer, ForeignKey("seed_lots.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("growers.id"), nullable=False)
    germination_rate = Column(Float, nullable=True)  # 0-100 (%)
    purity_rating = Column(Integer, nullable=True)  # 1-5
    trueness_to_type = Column(Integer, nullable=True)  # 1-5
    notes = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), server_default=func.now())

    seed_lot = relationship("SeedLot", back_populates="quality_reports")
    reporter = relationship("Grower", back_populates="quality_reports")


class Exchange(Base):
    """A record of a seed lot moving between two growers -- the network's edges."""

    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True, index=True)
    seed_lot_id = Column(Integer, ForeignKey("seed_lots.id"), nullable=False)
    from_grower_id = Column(Integer, ForeignKey("growers.id"), nullable=False)
    to_grower_id = Column(Integer, ForeignKey("growers.id"), nullable=False)
    quantity = Column(String, nullable=True)  # free text, e.g. "20 seeds", "1 packet"
    exchange_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    seed_lot = relationship("SeedLot", back_populates="exchanges")
    from_grower = relationship(
        "Grower", back_populates="exchanges_sent", foreign_keys=[from_grower_id]
    )
    to_grower = relationship(
        "Grower", back_populates="exchanges_received", foreign_keys=[to_grower_id]
    )
