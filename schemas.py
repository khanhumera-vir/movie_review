from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class MovieBase(BaseModel):
    title: str
    genre: Optional[str] = None
    release_date: Optional[str] = None
    director: Optional[str] = None

class MovieCreate(MovieBase):
    tmdb_id: str

class Movie(MovieBase):
    id: int
    tmdb_id: str
    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    rating: float
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    movie_id: int

class Review(ReviewBase):
    id: int
    movie_id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True