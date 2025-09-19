from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import SQLALCHEMY_DATABASE_URL


def set_sqlite_pragmas(dbapi_connection, connection_record):
    """SQLite-specific optimizations"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=1000;")
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.close()


def set_postgresql_settings(dbapi_connection, connection_record):
    """PostgreSQL-specific optimizations"""
    # PostgreSQL doesn't need special pragmas like SQLite
    pass


# Determine database type and configure accordingly
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_recycle=1800,  # 30 minutes
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Register SQLite event listener
    event.listen(engine, "connect", set_sqlite_pragmas)
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_recycle=1800,  # 30 minutes
        echo=False,
        pool_pre_ping=True,  # Verify connections before use
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Additional connections beyond pool_size
    )
    # Register PostgreSQL event listener (currently no-op)
    event.listen(engine, "connect", set_postgresql_settings)
else:
    # Fallback for other database types
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_recycle=1800,
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
