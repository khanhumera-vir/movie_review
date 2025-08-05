from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from models import Review, Movie
from schemas import Review, ReviewCreate
from database import get_db
from auth import get_current_user
from schemas import User
router = APIRouter()

@router.post("/", response_model=Review)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if review.rating < 0 or review.rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 10")
    
    movie = db.query(Movie).filter(Movie.id == review.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    db_review = Review(
        movie_id=review.movie_id,
        user_id=current_user.id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/movie/{movie_id}", response_model=List[Review])
async def get_movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.movie_id == movie_id).all()
    return reviews

@router.get("/movie/{movie_id}/average")
async def get_average_rating(movie_id: int, db: Session = Depends(get_db)):
    result = db.query(func.avg(Review.rating)).filter(Review.movie_id == movie_id).scalar()
    if result is None:
        raise HTTPException(status_code=404, detail="No reviews found for this movie")
    return {"movie_id": movie_id, "average_rating": round(result, 2)}

@router.put("/{review_id}", response_model=Review)
async def update_review(review_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_review = db.query(Review).filter(Review.id == review_id, Review.user_id == current_user.id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    
    if review.rating < 0 or review.rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 10")
    
    db_review.rating = review.rating
    db_review.comment = review.comment
    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{review_id}")
async def delete_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_review = db.query(Review).filter(Review.id == review_id, Review.user_id == current_user.id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    
    db.delete(db_review)
    db.commit()
    return {"message": "Review deleted successfully"}