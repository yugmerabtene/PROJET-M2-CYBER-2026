from fastapi import APIRouter
from app.attack_lab import routes as attack_routes

router = APIRouter()
router.include_router(attack_routes.router, prefix="/attack-lab", tags=["attack-lab"])
