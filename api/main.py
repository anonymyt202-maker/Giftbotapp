from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from db.session import init_db
from api.routers import gifts, orders, users, accounts, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs("uploads", exist_ok=True)
    yield


app = FastAPI(title="GiftBot API", version="5.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(gifts.router,    prefix="/api")
app.include_router(orders.router,   prefix="/api")
app.include_router(users.router,    prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(admin.router,    prefix="/api")

# Static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# WebApp HTML fayllar
@app.get("/webapp/admin")
async def serve_admin():
    return FileResponse("webapp/admin.html")

@app.get("/webapp/user")
async def serve_user():
    return FileResponse("webapp/user.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
