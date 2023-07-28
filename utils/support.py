from sys import path

path.append("..")

from models import AnimeDocument
from typing import List, Dict


def serialize_documents_to_dict(documents: List[AnimeDocument]) -> List[Dict]:
    return [document.model_dump() for document in documents]


def serialize_cursor_and_sort(documents: AnimeDocument) -> List[AnimeDocument]:
    response = [AnimeDocument(**document) for document in documents]
    response.sort(key=lambda anime: anime.rank)
    return response
