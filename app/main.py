import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.database import Base, engine
from app.locations.routers import router as location_router
from app.queue.routers import router as queue_router

load_dotenv()

ENV = os.getenv("ENV", "development")

docs_url = "/docs" if ENV == "development" else None
redoc_url = "/redoc" if ENV == "development" else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Muggli API",
    description="API for the Muggli application",
    version="0.0.1",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(queue_router)
app.include_router(location_router)
