from sys import path

from pymongo import ReturnDocument

path.append("..")

from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query, Response
from fastapi.responses import JSONResponse
from database import anime_collection
from starlette import status
from models import AnimeDocument, UpdateAnimeDocument
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId
from typing import Annotated
from .auth import get_current_user

from config import limiter, rate_lmits
from utils.cache_utils import get_cache, insert_cache
from utils.support import serialize_documents_to_dict, serialize_cursor_and_sort
from copy import deepcopy


router = APIRouter(prefix="/anime", tags=["Anime"])

user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/studio/{studio}", status_code=status.HTTP_200_OK)
@limiter.limit(rate_lmits.get("get"))
async def query_anime_by_studio(
    studio: str,
    user: user_dependency,
    request: Request,
    limit: int = Query(ge=1, default=5),
):
    cache_key = f"{studio}_{limit}"

    cache_data = get_cache(cache_key)
    if cache_data:
        return cache_data

    check_if_collection_empty = anime_collection.find_one({"studio": studio})
    if check_if_collection_empty:
        animes = anime_collection.find({"studio": studio}).limit(limit)
        response = serialize_cursor_and_sort(animes)
        response_dict = serialize_documents_to_dict(response)

        insert_cache(cache_key, response_dict)
        return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No anime exists by this studio!"
    )


@router.get("/genres/{genre}", status_code=status.HTTP_200_OK)
@limiter.limit(rate_lmits.get("get"))
async def query_anime_by_genres(
    genre: str,
    user: user_dependency,
    request: Request,
    limit: int = Query(ge=1, default=5),
):
    cache_key = f"{genre}_{limit}"

    cache_data = get_cache(cache_key)
    if cache_data:
        return cache_data

    check_if_collection_empty = anime_collection.find_one({"genres": {"$in": [genre]}})
    if check_if_collection_empty:
        animes = anime_collection.find({"genres": {"$in": [genre]}}).limit(limit)
        response = serialize_cursor_and_sort(animes)
        response_dict = serialize_documents_to_dict(response)

        insert_cache(cache_key, response_dict)
        return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No anime exists with this genre!"
    )


@router.get("/name/{name}", status_code=status.HTTP_200_OK)
@limiter.limit(rate_lmits.get("get"))
async def query_anime_by_name(name: str, user: user_dependency, request: Request):
    cache_key = f"{name}"
    cache_data = get_cache(cache_key)
    if cache_data:
        print(cache_data)
        return cache_data

    anime = anime_collection.find_one({"name": name})
    if anime:
        response = AnimeDocument(**anime)
        insert_cache(cache_key, response.model_dump())
        return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="No anime exists with this name!"
    )


@router.get("/rank/{rank}", status_code=status.HTTP_200_OK)
@limiter.limit(rate_lmits.get("get"))
async def query_anime_by_rank(
    user: user_dependency, request: Request, rank: int = Path(ge=1)
):
    cache_key = f"{rank}"
    cache_data = get_cache(cache_key)
    if cache_data:
        return cache_data

    anime = anime_collection.find_one({"rank": rank})
    if anime:
        response = AnimeDocument(**anime)
        insert_cache(cache_key, response.model_dump())
        return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="An anime with this rank does not exists!",
    )


@router.get("/rating/{rating_range}", status_code=status.HTTP_200_OK)
@limiter.limit(rate_lmits.get("get"))
async def query_animes_by_rating(
    user: user_dependency,
    request: Request,
    rating_range: float = Path(ge=0, le=5),
    limit: int = Query(ge=1, default=5),
):
    cache_key = f"{rating_range}_{limit}"
    cache_data = get_cache(cache_key)
    if cache_data:
        return cache_data

    check_if_collection_empty = anime_collection.find_one(
        {"rating": {"$gte": rating_range}}
    )
    if check_if_collection_empty:
        animes = anime_collection.find({"rating": {"$gte": rating_range}})
        response = serialize_cursor_and_sort(animes)
        response_dict = serialize_documents_to_dict(response)

        insert_cache(cache_key, response_dict)
        return response

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No anime exists with this rank or higher!",
    )


@router.post("/add-anime", status_code=status.HTTP_201_CREATED)
@limiter.limit(rate_lmits.get("post"))
async def create_anime(anime: AnimeDocument, user: user_dependency, request: Request):
    try:
        result = anime_collection.insert_one(anime.model_dump(exclude_unset=True))
        if result.acknowledged:
            return Response(
                content={
                    "message": "Anime created successfully",
                    "anime_id": str(result.inserted_id),
                }
            )

    except DuplicateKeyError as e:
        duplicate_key = e.details.get("keyPattern", {})
        conflicting_field = next(iter(duplicate_key.keys()), None)

        if conflicting_field == "rank":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An anime with the same rank already exists",
            )
        elif conflicting_field == "name":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An anime with the same name already exists",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An anime with conflicting data already exists",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occured",
        )


@router.delete("/delete-anime/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_lmits.get("delete"))
async def delete_anime(anime_id: str, user: user_dependency, request: Request):
    try:
        anime_id_obj = ObjectId(anime_id)
        anime_collection.delete_one({"_id": anime_id_obj})
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This id does not exists!"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occured",
        )


@router.put("/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_lmits.get("put"))
async def update_anime_document(
    anime_id: str,
    updated_anime: UpdateAnimeDocument,
    user: user_dependency,
    request: Request,
):
    try:
        anime_id_obj = ObjectId(str(anime_id))
        updated_data = updated_anime.model_dump(by_alias=True, exclude_unset=True)

        if not updated_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update, or some field names are incorrect!",
            )

        anime_collection.find_one_and_update(
            {"_id": anime_id_obj},
            {"$set": updated_data},
            return_document=ReturnDocument.AFTER,
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException as e:
        raise e

    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, no anime with this id exists!",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
