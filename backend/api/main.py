from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalogs, health, products, stores, settings, scheduler

app = FastAPI(title="Tilbudsradaren API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scheduler.router)
app.include_router(products.router)
app.include_router(stores.router)
app.include_router(catalogs.router)
app.include_router(health.router)
app.include_router(settings.router)

@app.on_event("startup")
def startup_event():
    from .utils.deps import get_db
    from .routers import scheduler

    gen = get_db()
    conn = next(gen)
    try:
        scheduler.ensure_scheduled(conn)
    finally:
        try:
            next(gen)  
        except StopIteration:
            pass