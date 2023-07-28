from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enums import Genres
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AnimeDocument(BaseModel):
    rank: int = Field(
        ge=1, description="The unique position of the anime in the ranking list"
    )
    name: str = Field(description="The name of the anime")
    rating: Optional[float] = Field(
        ge=0, le=5, description="A rating from 0 to 5", default=None
    )
    episodes: Optional[int] = Field(
        ge=0,
        default=None,
        description="Number of episodes the anime has (0 for ongoing or unspecified)",
    )
    studio: Optional[str] = Field(
        default=None, description="What studio animated the anime"
    )
    genres: Optional[List[Genres]] = Field(
        default=None, description="List of genres associated with the anime"
    )

    @field_validator("episodes", mode="before")
    def validate_episodes(cls, value):
        if value == "":
            return None
        return value

    @field_validator("rating", mode="before")
    def validate_rating(cls, value):
        if value == "":
            return None
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "name": "Jujutsu Kaisen",
                "rating": 4.9,
                "episodes": 24,
                "studio": "MAPPA",
                "genres": ["Action", "Supernatural", "Shonen"],
            }
        }


class UpdateAnimeDocument(BaseModel):
    rank: Optional[int] = Field(ge=1, default=None)
    name: Optional[str] = None
    rating: Optional[float] = Field(ge=0, le=5, default=None)
    episodes: Optional[int] = Field(ge=0, default=None)
    studio: Optional[str] = None
    genres: Optional[List[Genres]] = None


class User(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    email: str
    hashed_password: Optional[str] = Field(min_length=7, default=None)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, text_password: str):
        self.hashed_password = bcrypt_context.hash(text_password)

    def check_password_correction(self, attempted_password: str) -> bool:
        return bcrypt_context.verify(attempted_password, self.hashed_password)
