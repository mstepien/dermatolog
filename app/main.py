import time
import logging
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware


from app.models import HealthCheckResponse
from app.routers.photos import router as photos_router
from app.routers.api import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dermatolog AI Scan",
    description="FastAPI application for dermatology analysis",
    version="1.0.0"
)

# Simple Session Middleware
class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        created_new = False
        if not session_id:
            session_id = str(uuid.uuid4())
            created_new = True
            # Hack: Inject into request scope so endpoints can see it if they looked there,
            # but usually they look at cookies. We rely on the client sending it back,
            # but for the *first* request, we need to handle it.
            # Ideally endpoints assume cookie exists.
            # Let's set the cookie on the response.

        # Pass session_id in request state if needed?
        # request.state.session_id = session_id
        
        response = await call_next(request)
        
        if created_new:
            # Set cookie for 1 day
            response.set_cookie(key="session_id", value=session_id, max_age=86400)
            
        return response

app.add_middleware(SessionMiddleware)

app.include_router(photos_router)
app.include_router(api_router)

# Mount static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main frontend page."""
    return templates.TemplateResponse("index.html", {"request": request})
