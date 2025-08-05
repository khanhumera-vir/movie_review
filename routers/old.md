from fastapi import APIRouter, Depends, HTTPException,FastAPI
from sqlalchemy.orm import Session
from typing import List
import requests
from models import Movie
from schemas import Movie, MovieCreate
from database import get_db
from auth import get_current_user

router = APIRouter()

TMDB_API_KEY = "9648cacf1821fbb47040d7aed3534b73"

@router.get("/", response_model=List[Movie])


    

async def search_movies(query: str, db: Session = Depends(get_db)):
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    # Search local database first
    movies = db.query(Movie).filter(Movie.title.ilike(f"%{query}%")).all()
    if movies:
        return movies
    
    # If not found, query TMDb
    response = requests.get(
        f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        
    )

    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }

    response = requests.get(url, params=params)
    print("URL:", response.url)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
 

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Error fetching movie data")
    
    tmdb_movies = response.json().get("results", [])
    for tmdb_movie in tmdb_movies[:5]:  # Limit to 5 results
        movie = db.query(Movie).filter(Movie.tmdb_id == str(tmdb_movie["id"])).first()
        if not movie:
            movie = Movie(
                tmdb_id=str(tmdb_movie["id"]),
                title=tmdb_movie["title"],
                genre=",".join([g["name"] for g in requests.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_movie['id']}?api_key={TMDB_API_KEY}"
                ).json().get("genres", [])]),
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

@router.get("/{movie_id}", response_model=Movie)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie