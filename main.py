from fastapi import FastAPI
from routers import anime, auth
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from config import limiter
from subprocess import Popen
from time import sleep
from os import kill
from signal import SIGINT

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(anime.router)
app.include_router(auth.router)

redis_server_process = None


@app.on_event("startup")
async def startup_event():
    global redis_server_process
    redis_server_process = Popen(["redis-server"])

    sleep(1)


@app.on_event("shutdown")
async def shutdown_event():
    global redis_server_process
    if redis_server_process:
        kill(redis_server_process.pid, SIGINT)
        redis_server_process.wait()
