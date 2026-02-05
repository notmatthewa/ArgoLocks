import uvicorn
from fastapi import FastAPI

from argolocks.config import settings
from argolocks.routes import health, locks, slack

app = FastAPI(title="ArgoLocks")
app.include_router(locks.router)
app.include_router(slack.router)
app.include_router(health.router)


def main():
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
