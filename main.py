from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Smartpath API",
    version="1.0.0",
    description="API del MVP"
)

app.include_router(router)
