import logging
from fastapi import FastAPI
from app.resources.mock_data.populate_db import populate_db
import uvicorn
from app import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omnicom MVP",
    description="Omnicom MVP Backend API",
)
app.include_router(api.router, prefix="/rest/api")

@app.get("/")
def read_root():
    return {"Message": "Ok 🪅"}

if __name__ == "__main__":
    populate_db()
    uvicorn.run("main:app", host="127.0.0.1", port=3000, reload=False, workers=6)