from typing import Callable
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
import re
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, HTMLResponse
from src.database.db import get_db
from src.middleware.middleware import CustomMiddleware
from src.routes import contacts, birthdays, auth, email_tracker, users
from dotenv import load_dotenv
from src.conf.config import config
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan function that initializes FastAPILimiter with Redis connection.

    Initializes FastAPILimiter with Redis connection. This function is used
    as a lifespan function for FastAPI application.

    It yields control back to the ASGI framework after initializing
    FastAPILimiter and closes the Redis connection when the application
    is shutting down.
    """
    redis_client = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
        decode_responses=True
    )
    await FastAPILimiter.init(redis_client)

    yield

    await redis_client.close()


app = FastAPI(lifespan=lifespan)

if os.getenv("SPHINX_BUILD") != "1":
    if os.path.isdir("src/static"):
        app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_agent_ban_list = [r"Python-urllib", r"python-requests", r"bot", r"spider"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """
    This middleware bans requests from user-agents that match a list of regex patterns.

    The list of regex patterns is defined in the user_agent_ban_list variable.
    If a request's user-agent matches any of the patterns, it is rejected with
    a 403 Forbidden response.

    Otherwise, the request is passed on to the next middleware in the chain.
    """
    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
    response = await call_next(request)
    return response


app.add_middleware(CustomMiddleware)

app.include_router(auth.router, prefix="/api", tags=["auth"])

app.include_router(email_tracker.router, prefix="/api", tags=["email_tracking"])

app.include_router(users.router, prefix="/api", tags=["users"])

app.include_router(contacts.router, prefix="/api", tags=["contacts"])

app.include_router(birthdays.router, prefix="/api", tags=["birthdays"])

templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def root(requests: Request):
    """
    The root route of the API. It returns a simple HTML page with a welcome message.

    The page is rendered using a Jinja2 template and the request object is passed
    as a variable to the template.

    The status code of this route is 200 OK.

    Parameters
    ----------
    requests : fastapi.Request
        The request object.

    Returns
    -------
    fastapi.responses.HTMLResponse
        The rendered HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": requests})


@app.get("/healthchecker", status_code=status.HTTP_200_OK)
async def healthchecker(db: AsyncSession = Depends(get_db)) :
    """
    A healthcheck endpoint for the API.

    This endpoint is used to check the health of the API. It returns a 200 OK
    response with a welcome message if the database is configured correctly.
    If the database is not configured, it raises a 500 Internal Server Error
    with a detail message.

    Returns
    -------
    dict
        A dictionary with a single key "message" and a value "Welcome to FastAPI!".
    """
    try:
        result = await (db.execute(text("SELECT 1")))
        result = result.fetchone()
        if result is None:
            raise Exception()
        return {"message": "Welcome to FastAPI!"}

    except Exception:
        raise HTTPException(status_code=500, detail="Database is not configured.")
