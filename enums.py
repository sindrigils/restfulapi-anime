from enum import Enum
from typing import List


class Genres(str, Enum):
    """Enumeration representing genres associated with anime"""

    DRAMA = "Drama"
    ACTION = "Action"
    SUPERNATRUAL = "Supernatural"
    ADVENTURE = "Adventure"
    COMEDY = "Comedy"
    FANTASY = "Fantasy"
    SHOUNEN = "Shounen"
    SEINEN = "Seinen"
    SHOUJO = "Shoujo"
    ISEKAI = "Isekai"
    MECHA = "Mecha"
    MYSTERY = "Mystery"
    SPORTS = "Sports"


def filter_valid_genres(genres_list: List[str]) -> List[str]:
    """
    Removes any genres that are not included in the Genres enum class, and strips all white spaces.
    Makes sure no errors occures when importing csv data into the database.
    """
    return [
        genre.strip()
        for genre in genres_list
        if genre.strip() in Genres.__members__.values()
    ]
