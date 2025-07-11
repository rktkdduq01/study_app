from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, characters, quests, achievements, ai_tutor, gamification, payments, multiplayer, cms, content_generation, parent_dashboard
from app.api.v1 import security
from app.api.endpoints import test_errors, analytics, analytics_ws, i18n
from app.core.config import settings

api_router = APIRouter()

# Include routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    characters.router,
    prefix="/characters",
    tags=["characters"]
)

api_router.include_router(
    quests.router,
    prefix="/quests",
    tags=["quests"]
)

api_router.include_router(
    achievements.router,
    prefix="/achievements",
    tags=["achievements"]
)

api_router.include_router(
    ai_tutor.router,
    prefix="/ai-tutor",
    tags=["ai-tutor"]
)

api_router.include_router(
    gamification.router,
    prefix="/gamification",
    tags=["gamification"]
)

api_router.include_router(
    security.router,
    prefix="/security",
    tags=["security"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["payments"]
)

api_router.include_router(
    multiplayer.router,
    prefix="/multiplayer",
    tags=["multiplayer"]
)

api_router.include_router(
    cms.router,
    prefix="/cms",
    tags=["cms"]
)

api_router.include_router(
    content_generation.router,
    prefix="/content-generation",
    tags=["content-generation"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    analytics_ws.router,
    prefix="/analytics",
    tags=["analytics-websocket"]
)

api_router.include_router(
    i18n.router,
    prefix="/i18n",
    tags=["i18n"]
)

api_router.include_router(
    parent_dashboard.router,
    prefix="/parent",
    tags=["parent-dashboard"]
)

# Include test endpoints in debug mode
if settings.DEBUG:
    api_router.include_router(
        test_errors.router,
        prefix="/test",
        tags=["testing"]
    )