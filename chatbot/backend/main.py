from pathlib import Path
from dotenv import load_dotenv

# Load .env file từ backend/.env trước khi import các module khác
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.database import engine, Base
from api import auth, keywords, threads, query

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AnswerMe API", version="1.0.0")

# CORS - must be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# Routes
app.include_router(auth.router)
app.include_router(keywords.router)
app.include_router(threads.router)
app.include_router(query.router)

@app.get("/")
async def root():
    return {"message": "AnswerMe API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
