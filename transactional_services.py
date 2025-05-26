import googlemaps
from sqlalchemy.orm import Session
from geoalchemy2 import functions as geofunc
import datetime
from phase5_models_and_connection import (
    SessionLocal, SurgeArea, Driver, Vehicle, DriverOffer, Trip
)
import math
# from dotenv import load_dotenv
# import os
#
# # Load environment variables from .env file
# load_dotenv()
# 
# Google Maps API Key
GMAPS_API_KEY ='AIzaSyB2Nsc5oCO9KZHN_hdjlDNX1ohmhTYiFIw'
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

BASE_FARE = 5  # base rate per km
SEARCH_RADIUS = 5000  # meters
def calculate_distance(lat1, lng1, lat2, lng2):
    # Using the Euclidean formula, and multiplying by 111 km to get the distance in kilometers
    lat_diff = (lat1 - lat2) * 111  # 1 degree of latitude is approximately 111 km
    lng_diff = (lng1 - lng2) * 111  # 1 degree of longitude is approximately 111 km at the equator
    return math.sqrt(lat_diff**2 + lng_diff**2)

def calculate_duration(lat1, lng1, lat2, lng2):
    x=calculate_distance(lat1, lng1, lat2, lng2)
    return x/40

def calculate_fare(base, distance_km, duration_h, type_mult, area_mult):
    pricee= base * (distance_km + duration_h) * area_mult
    if type_mult == "Luxury":
        return pricee + (pricee * (10/100))
    elif type_mult == "Family":
        return pricee + (pricee * (25/100))
    else:
        return pricee

def get_route_from_gmaps(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    # Get route from Google Maps Directions API
    directions_result = gmaps.directions(
        (pickup_lat, pickup_lng),
        (dropoff_lat, dropoff_lng),
        mode="driving"
    )

    if directions_result:
        route = directions_result[0]['legs'][0]
        distance = route['distance']['value'] / 1000  # in kilometers
        duration = route['duration']['value'] / 3600  # in hours
        polyline = route['steps']
        route_geometry = []
        for step in polyline:
            # Append the encoded polyline from the Google Maps response as route geometry
            route_geometry.append(step['polyline']['points'])
        return distance, duration, route_geometry
    else:
        raise Exception("No route found for the specified locations")


def request_ride(rider_id: int, pickup_lat: float, pickup_lng: float,
                 dropoff_lat: float, dropoff_lng: float, vehicletypeid: str):
    session: Session = SessionLocal()
    # Calculate the distance, duration, and get the route from Google Maps API
    distance, duration, route_geometry = get_route_from_gmaps(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)

    try:
        with session.begin():
            # 1. Determine surge area and multiplier
            pickup_pt = geofunc.ST_SetSRID(geofunc.ST_MakePoint(pickup_lng, pickup_lat), 4326)
            area = session.query(SurgeArea).filter(
                geofunc.ST_Contains(SurgeArea.area, pickup_pt)
            ).first()
            area_mult = area.faremultiplier if area else 1.0

            # 2. Create trip record
            trip = Trip(
                riderid=rider_id,
                ridestatus='Requested',
                pickuploc=pickup_pt,
                dropoffloc=geofunc.ST_SetSRID(geofunc.ST_MakePoint(dropoff_lng, dropoff_lat), 4326),
                starttime=0,
                endtime=0,
                estimatedarrival=duration,
                route=route_geometry,  # Save the route in the Trip table
                price=calculate_fare(BASE_FARE, distance, duration, vehicletypeid, area_mult)
            )
            session.add(trip)
            session.flush()

            # 3. Select up to 5 nearest available drivers matching type and in radius
            pickup_point = geofunc.ST_SetSRID(geofunc.ST_MakePoint(pickup_lat, pickup_lng), 4326).cast(Geography)
            drivers = (
                session.query(Driver.driverid)
                .join(Vehicle, Driver.driverid == Vehicle.driverid)
                .filter(
                    Driver.status == 'Online',
                    Vehicle.vehicletypeid == vehicletypeid,
                    geofunc.ST_DWithin(
                        Driver.location.cast(Geography),
                        pickup_point,
                        5000
                    ) == True
                )
                .order_by(
                    geofunc.ST_Distance(Driver.location.cast(Geography), pickup_point)
                )
                .limit(5)
                .all()
            )
            if not drivers:
                raise Exception("No Drivers arround")

            # 4. Create driver offers with pending status
            offers = []
            for drv in drivers:
                offer = DriverOffer(
                    tripid=trip.tripid,
                    driverid=drv.driverid,
                    pickuploc=trip.pickuploc,
                    dropoffloc=trip.dropoffloc,
                    offerstatus='pending',
                    price=calculate_fare(BASE_FARE, distance, duration, vehicletypeid, area_mult),
                    route=route_geometry  # Save the same route in DriverOffer table
                )
                offers.append(offer)
            session.bulk_save_objects(offers)

        return trip.tripid, [d.driverid for d in drivers], calculate_fare(BASE_FARE, distance, duration,
                                                                          vehicletypemulti, area_mult)
    finally:
        session.close()


def accept_ride(trip_id: int, driver_id: int):
    session: Session = SessionLocal()
    try:
        with session.begin():
            # Lock trip row
            trip = session.query(Trip).filter(Trip.tripid == trip_id).with_for_update().one()
            if trip.ridestatus == 'accepted':
                raise Exception("Trip has already been accepted")
          

            # Validate selected offer
            offer = next((o for o in all_offers if o.driverid == driver_id), None)
            if not offer:
                raise Exception("Offer not found for driver on this trip")

            # 1. Accept selected, reject others
            for o in all_offers:
                if o.driverid == driver_id:
                    o.offerstatus = 'accepted'
                else:
                    o.offerstatus = 'rejected'
                session.add(o)

            # 2. Update trip and driver statuses
            trip.driverid = driver_id
            trip.ridestatus = 'accepted'
            trip.starttime=datetime.now()
            session.add(trip)

            drv.status = 'Busy'
            session.add(drv)

        return True
    finally:
        session.close()
