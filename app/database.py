from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import SQLALCHEMY_DATABASE_URL

# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"


def set_wal_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=1000;")
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.close()


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=1800,  # 30 minutes
    echo=False,
    connect_args={"check_same_thread": False},
)

# Register the event listener
event.listen(engine, "connect", set_wal_mode)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

# Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
