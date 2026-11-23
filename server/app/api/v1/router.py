from fastapi import APIRouter

from app.api.v1 import auth, cases, demo, documents, forms, meta, operator

api_router = APIRouter(prefix="/api/v1")
for module in (meta, auth, operator, cases, documents, forms, demo):
    api_router.include_router(module.router)
