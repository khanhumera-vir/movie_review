from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import movies, users, reviews
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import engine

from models import Base

app = FastAPI(title="Movie Review Aggregator API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(movies.router, prefix="/movies", tags=["movies"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Movie Review Aggregator API"}