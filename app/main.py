from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import models as auth_models  # noqa: F401
from app.auth.routers import router as auth_router
from app.config import settings
from app.database import Base, engine
from app.locations import models as location_models  # noqa: F401
from app.locations.routers import router as location_router

# Import models to ensure they're registered with SQLAlchemy (order matters for relationships)
from app.organizations import models as organization_models  # noqa: F401
from app.organizations.routers import router as organization_router
from app.queue import models as queue_models  # noqa: F401
from app.queue.routers import router as queue_router
from app.services import models as service_models  # noqa: F401
from app.services.routers import router as services_router
from app.subscriptions import models as subscription_models  # noqa: F401
from app.subscriptions.routers import router as subscriptions_router
from app.users.routers import router as users_router

# from app.access.routers import router as access_router  # Temporarily disabled

# from app.access import models as access_models  # noqa: F401  # Temporarily disabled

load_dotenv()

docs_url = "/docs" if settings.ENV == "development" else None
redoc_url = "/redoc" if settings.ENV == "development" else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Start the subscription scheduler
    from app.subscriptions.scheduler import start_scheduler, stop_scheduler

    await start_scheduler()

    yield

    # Stop the scheduler on shutdown
    await stop_scheduler()


app = FastAPI(
    title="Queueless API",
    description="API for the Queueless application",
    version="0.0.1",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(location_router)
app.include_router(organization_router)
app.include_router(services_router)
app.include_router(queue_router)
app.include_router(subscriptions_router)
app.include_router(users_router)
# app.include_router(access_router)  # Temporarily disabled
