from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalogs, health, products, stores

app = FastAPI(title="Discount Catalog API")

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