"""Run this once to populate the DB with sample data for a demo:
    python seed_demo_data.py
"""
from datetime import datetime, timedelta

from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Clear existing data for a clean demo run
db.query(models.Exchange).delete()
db.query(models.QualityReport).delete()
db.query(models.SeedLot).delete()
db.query(models.Grower).delete()
db.commit()

# Growers
asha = models.Grower(name="Asha Patil", email="asha@example.com", location="Hubballi, Karnataka")
ravi = models.Grower(name="Ravi Kumar", email="ravi@example.com", location="Dharwad, Karnataka")
meera = models.Grower(name="Meera Joshi", email="meera@example.com", location="Belagavi, Karnataka")
db.add_all([asha, ravi, meera])
db.commit()
for g in (asha, ravi, meera):
    db.refresh(g)

# Seed lots
tomato_lot = models.SeedLot(
    owner_id=asha.id,
    variety="Desi Tomato - Arka Vikas",
    species="Solanum lycopersicum",
    source="own harvest",
    date_saved=datetime.utcnow() - timedelta(days=200),
    description="Saved from strongest plants in the kitchen garden.",
    generation=1,
)
db.add(tomato_lot)
db.commit()
db.refresh(tomato_lot)

# Second generation, grown out by Ravi after receiving from Asha
tomato_lot_gen2 = models.SeedLot(
    owner_id=ravi.id,
    variety="Desi Tomato - Arka Vikas",
    species="Solanum lycopersicum",
    source="traded from Asha Patil",
    date_saved=datetime.utcnow() - timedelta(days=30),
    description="Grown out from Asha's lot, reselected for fruit size.",
    generation=2,
    parent_lot_id=tomato_lot.id,
)
db.add(tomato_lot_gen2)

brinjal_lot = models.SeedLot(
    owner_id=meera.id,
    variety="Udupi Brinjal",
    species="Solanum melongena",
    source="own harvest",
    date_saved=datetime.utcnow() - timedelta(days=90),
    description="Traditional local variety, saved for 3 seasons.",
    generation=3,
)
db.add(brinjal_lot)
db.commit()
db.refresh(tomato_lot_gen2)
db.refresh(brinjal_lot)

# Quality reports
db.add_all([
    models.QualityReport(seed_lot_id=tomato_lot.id, reporter_id=asha.id,
                          germination_rate=92, purity_rating=5, trueness_to_type=5,
                          notes="Excellent germination, true to type."),
    models.QualityReport(seed_lot_id=tomato_lot.id, reporter_id=ravi.id,
                          germination_rate=85, purity_rating=4, trueness_to_type=5,
                          notes="Good results in my plot too."),
    models.QualityReport(seed_lot_id=brinjal_lot.id, reporter_id=meera.id,
                          germination_rate=78, purity_rating=4, trueness_to_type=4,
                          notes="Slight variation in fruit color."),
])
db.commit()

# Exchanges
db.add_all([
    models.Exchange(seed_lot_id=tomato_lot.id, from_grower_id=asha.id, to_grower_id=ravi.id,
                     quantity="30 seeds", exchange_date=datetime.utcnow() - timedelta(days=40),
                     notes="Swapped at the local seed exchange meetup."),
    models.Exchange(seed_lot_id=brinjal_lot.id, from_grower_id=meera.id, to_grower_id=asha.id,
                     quantity="1 packet", exchange_date=datetime.utcnow() - timedelta(days=15),
                     notes="Given in exchange for tomato seeds."),
])
db.commit()

print("Demo data loaded: 3 growers, 3 seed lots, 3 quality reports, 2 exchanges.")
db.close()
