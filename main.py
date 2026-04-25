from fastapi import FastAPI
from app.core.config.settings import Settings
from app.routers.routes_v1 import routes_v1

settings = Settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# Include Routes
app.include_router(routes_v1, prefix="/api/v1")

# Root url
@app.get("/")
def index():
    return {
        "status": "ok"
    }

# Health Check Endpoint
@app.get("/health")
def health():
    return {
        "status": "running",
    }