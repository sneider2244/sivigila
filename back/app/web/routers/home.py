from fastapi import APIRouter, Request

from app.web.navigation import NAV_ITEMS
from app.web.templating import templates

router = APIRouter()


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"active": "dashboard", "nav_items": NAV_ITEMS},
    )
