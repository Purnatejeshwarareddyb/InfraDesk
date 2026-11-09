from fastapi import APIRouter

from app.api.v1 import activity, assets, auth, notifications, reports, tickets, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tickets.router)
api_router.include_router(assets.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
api_router.include_router(activity.router)
