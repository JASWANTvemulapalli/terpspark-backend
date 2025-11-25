"""
API router initialization.
Aggregates all API route modules.
"""
from fastapi import APIRouter
from app.api import auth, events

# Create main API router
api_router = APIRouter()

# Include authentication routes (Phase 1)
api_router.include_router(auth.router)

# Include event routes (Phase 2: Event Discovery & Browse)
api_router.include_router(events.router)

# Future phase routers will be added here:
# from app.api import registrations, organizer, admin
# api_router.include_router(registrations.router)
# api_router.include_router(organizer.router)
# api_router.include_router(admin.router)
