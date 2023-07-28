from pymongo.mongo_client import MongoClient
from config import PASSWORD
import csv
from models import AnimeDocument
from enums import filter_valid_genres

uri = f"mongodb+srv://sindrigils:{PASSWORD}@bankai.pg0xvyg.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)

db = client.AnimeDB
anime_collection = db["anime-collection"]
user_collection = db["user-collection"]


def import_data_from_csv(file_name):
    with open(file_name, newline="", encoding="utf-8") as csvfile:
        csvreader = csv.DictReader(csvfile)

        anime_documents = []

        for row in csvreader:
            anime_instance = AnimeDocument(
                rank=int(row["Rank"]),
                name=row["Name"],
                rating=row["Rating"],
                episodes=row["Episodes"],
                studio=row["Studio"],
                genres=filter_valid_genres(row["Tags"].split()),
            )

            anime_documents.append(anime_instance)

        if row:
            anime_collection.insert_many([doc.model_dump() for doc in anime_documents])
