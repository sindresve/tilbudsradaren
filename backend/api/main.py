from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalogs, health, products, stores, settings

app = FastAPI(title="Tilbudsradaren API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(stores.router)
app.include_router(catalogs.router)
app.include_router(health.router)
app.include_router(settings.router)