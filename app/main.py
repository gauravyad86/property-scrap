# app/main.py
import concurrent.futures
from fastapi import FastAPI, HTTPException, Query
from app.scrapers import squareyard, nobroker, housing

app = FastAPI(
    title="Property Scraper API",
    description="API endpoints to get property listings from Squareyard, NoBroker, and Housing.com.",
    version="1.0.0"
)

@app.get("/squareyard", summary="Squareyard Listings")
def get_squareyard(city: str = Query(..., example="Delhi"),
                   locality: str = Query(..., example="Saket"),
                   page: int = Query(1, ge=1, description="Page number (10 results per page)")):
    try:
        results = squareyard.scrape_squareyard(city, locality, page)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nobroker", summary="NoBroker Listings")
def get_nobroker(city: str = Query(..., example="Mumbai"),
                 locality: str = Query(..., example="Powai"),
                 page: int = Query(1, ge=1, description="Page number (10 results per page)")):
    try:
        results = nobroker.scrape_nobroker(city, locality, page)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/housing", summary="Housing.com Listings")
def get_housing(city: str = Query(..., example="Gurgaon"),
                locality: str = Query(..., example="Sector 9"),
                page: int = Query(1, ge=1, description="Page number (10 results per page)")):
    try:
        results = housing.scrape_housing(city, locality, page)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all", summary="All Listings")
def get_all(city: str = Query(..., example="Delhi"),
            locality: str = Query(..., example="Saket"),
            page: int = Query(1, ge=1, description="Page number (10 results per page)")):
    """
    Returns results from all three websites concurrently.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_squareyard = executor.submit(squareyard.scrape_squareyard, city, locality, page)
        future_nobroker = executor.submit(nobroker.scrape_nobroker, city, locality, page)
        future_housing = executor.submit(housing.scrape_housing, city, locality, page)
        results = {
            "squareyard": future_squareyard.result(),
            "nobroker": future_nobroker.result(),
            "housing": future_housing.result()
        }
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)