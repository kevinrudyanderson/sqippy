from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import SQLALCHEMY_DATABASE_URL

# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# def set_wal_mode(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA journal_mode=WAL;")
#     cursor.close()


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=1800,  # 30 minutes
    echo=False,
)

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
