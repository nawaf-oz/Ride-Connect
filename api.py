from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from transactional_services import request_ride, accept_ride

app = FastAPI(title="RideConnect Phase 5")

class RequestRidePayload(BaseModel):
    rider_id: int
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    vehicletypeid: str
class AcceptRidePayload(BaseModel):
    trip_id: int
    driver_id: int
#
@app.get("/")

def read_root():
    return {"message": "RideConnect Phase 5 API is up!"}

@app.post("/request_ride")

def api_request_ride(payload: RequestRidePayload):
    try:
        trip_id, driver_id, fare = request_ride(
            payload.rider_id,
            payload.pickup_lat, payload.pickup_lng,
            payload.dropoff_lat, payload.dropoff_lng,
            payload.vehicletypeid
        )
        return {"trip_id": trip_id, "driver_id": driver_id, "estimated_fare": fare}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/accept_ride")

def api_accept_ride(payload: AcceptRidePayload):
    try:
        success = accept_ride(payload.trip_id, payload.driver_id)
        return {"accepted": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# To run: uvicorn api:app --reload --host 0.0.0.0 --port 8000
