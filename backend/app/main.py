from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import get_db

from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.github import router as github_router
from app.api.routes.files import router as files_router

app = FastAPI(
    title="CodeAtlas API",
    description=(
        "Universal AI codebase analysis "
        "and understanding platform."
    ),
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(uploads_router)
app.include_router(github_router)
app.include_router(files_router)


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Welcome to CodeAtlas API",
        "application": "CodeAtlas",
        "status": "running"
    }


# --------------------------------------------------
# APPLICATION HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "CodeAtlas"
    }


# --------------------------------------------------
# DATABASE HEALTH CHECK
# --------------------------------------------------

@app.get("/health/database")
def database_health(
    db: Session = Depends(get_db)
):

    try:

        db.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "PostgreSQL"
        }

    except SQLAlchemyError:

        raise HTTPException(
            status_code=503,
            detail="PostgreSQL database connection failed."
        )
