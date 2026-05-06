from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()

TEMPLATE_DIR = Path(__file__).parent / "templates"

@router.get("/", response_class=HTMLResponse)
async def index():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/alerts", response_class=HTMLResponse)
async def alerts():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/events", response_class=HTMLResponse)
async def events():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/assets", response_class=HTMLResponse)
async def assets():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/correlations", response_class=HTMLResponse)
async def correlations():
    return (TEMPLATE_DIR / "index.html").read_text()

@router.get("/reports", response_class=HTMLResponse)
async def reports():
    return (TEMPLATE_DIR / "index.html").read_text()
