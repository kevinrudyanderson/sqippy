import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.database import Base, engine
from app.locations.routers import router as location_router
from app.organizations.routers import router as organization_router
from app.queue.routers import router as queue_router
from app.services.routers import router as services_router
# from app.access.routers import router as access_router  # Temporarily disabled

# Import models to ensure they're registered with SQLAlchemy (order matters for relationships)
from app.organizations import models as organization_models  # noqa: F401
from app.locations import models as location_models  # noqa: F401
from app.auth import models as auth_models  # noqa: F401
from app.services import models as service_models  # noqa: F401
from app.queue import models as queue_models  # noqa: F401
# from app.access import models as access_models  # noqa: F401  # Temporarily disabled

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(location_router)
app.include_router(organization_router)
app.include_router(services_router)
app.include_router(queue_router)
# app.include_router(access_router)  # Temporarily disabled
