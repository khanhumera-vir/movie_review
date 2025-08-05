from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
from models import Movie as MovieModel
from schemas import Movie as MovieSchema, MovieCreate
from database import get_db
from auth import get_current_user
import logging
from fastapi import Query


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

TMDB_API_KEY = "bfca8e37f0c13bd5829bf7725b507ffb" 


@router.get("/search", response_model=List[MovieSchema])
async def search_movies(query: str = Query(..., alias="title"), db: Session = Depends(get_db)):

    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Search local DB
    movies = db.query(MovieModel).filter(MovieModel.title.ilike(f"%{query}%")).all()
    if movies:
        return movies

    # TMDb API call
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query  
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info(f"Requested TMDb URL: {response.url}")
    except requests.RequestException as e:
        logger.error(f"TMDb request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch data from TMDb")

    tmdb_movies = response.json().get("results", [])
    for tmdb_movie in tmdb_movies[:5]:
        movie = db.query(MovieModel).filter(MovieModel.tmdb_id == str(tmdb_movie["id"])).first()
        if not movie:
            genre_response = requests.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_movie['id']}?api_key={TMDB_API_KEY}"
            )
            genres = genre_response.json().get("genres", [])
            movie = MovieModel(
                tmdb_id=str(tmdb_movie["id"]),
                title=tmdb_movie["title"],
                genre=",".join([g["name"] for g in genres]),
                release_date=tmdb_movie.get("release_date", ""),
                director=get_director(tmdb_movie["id"])
            )
            db.add(movie)
            db.commit()
            db.refresh(movie)
            movies.append(movie)
    return movies


def get_director(tmdb_id):
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={TMDB_API_KEY}"
    )
    if response.status_code == 200:
        crew = response.json().get("crew", [])
        for member in crew:
            if member["job"] == "Director":
                return member["name"]
    return ""


@router.get("/{movie_id}", response_model=MovieSchema)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
