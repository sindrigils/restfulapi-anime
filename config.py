# enviroment variables
from dotenv import load_dotenv
from os import getenv

load_dotenv()
PASSWORD = getenv("PASSWORD")
SECRET_KEY = getenv("SECRET_KEY")


# rate limits
from slowapi import Limiter
from slowapi.util import get_remote_address

rate_lmits = {
    "get": "60/minute",
    "post": "30/minute",
    "put": "20/minute",
    "delete": "15/minute",
}

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1 per minute"],
)
