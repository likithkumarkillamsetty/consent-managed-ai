from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "consent.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import logging

logger = logging.getLogger("database")


def upgrade_db_schema(target_engine=None):
    """
    Safely upgrades the database schema if columns are missing.
    Idempotent and safe to run multiple times without data loss.
    """
    eng = target_engine or engine
    with eng.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(training_batches);")).fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "privacy_enabled" not in existing_cols:
                    logger.info("Migrating schema: adding training_batches.privacy_enabled column")
                    conn.execute(text("ALTER TABLE training_batches ADD COLUMN privacy_enabled BOOLEAN DEFAULT 0;"))
                if "privacy_mechanism" not in existing_cols:
                    logger.info("Migrating schema: adding training_batches.privacy_mechanism column")
                    conn.execute(text("ALTER TABLE training_batches ADD COLUMN privacy_mechanism VARCHAR(50);"))
                conn.commit()
        except Exception as e:
            logger.error("Database schema upgrade failed for training_batches: %s", e, exc_info=True)
            raise


def init_db():
    from app.models import consent, audit, training_data, training_batch, training_lineage  # noqa: F401
    Base.metadata.create_all(bind=engine)
    upgrade_db_schema(engine)
