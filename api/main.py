# HooshiGap API Layer
# Central communication point for all platforms

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HooshiGap API",
    description="Privacy-first anonymous social platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "platform": "HooshiGap"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
