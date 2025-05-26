from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from geoalchemy2 import Geometry

# Database URL placeholder; replace with your credentials
DATABASE_URL = "****"

# SQLAlchemy engine and session setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# -- Schema from provided ER diagram --
#
class VehicleType(Base):
    __tablename__ = 'vehicletype'

    typeid = Column(String(50), primary_key=True)
    faremultiplier = Column(Float, nullable=False)

class SurgeArea(Base):
    __tablename__ = 'surgearea'

    areaid = Column(Integer, primary_key=True)
    area = Column(Geometry('POLYGON'), nullable=False)
    faremultiplier = Column(Float, nullable=False)

class Rider(Base):
    __tablename__ = 'rider'

    riderid = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contactdetails = Column(String(50), nullable=False)
    location = Column(Geometry('POINT'), nullable=False)

class Driver(Base):
    __tablename__ = 'driver'

    driverid = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    contactdetails = Column(String(50), nullable=False)
    licenseinfo = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    location = Column(Geometry('POINT'), nullable=False)

    vehicles = relationship('Vehicle', back_populates='driver')

class Vehicle(Base):
    __tablename__ = 'vehicle'

    vehicleid = Column(Integer, primary_key=True)
    driverid = Column(Integer, ForeignKey('driver.driverid'), nullable=False)
    vehicletypeid = Column(String(50), ForeignKey('vehicletype.typeid'), nullable=False)
    make = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    platenumber = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)

    driver = relationship('Driver', back_populates='vehicles')
    type = relationship('VehicleType')

class Trip(Base):
    __tablename__ = 'trip'

    tripid = Column(Integer, primary_key=True)
    driverid = Column(Integer, ForeignKey('driver.driverid'), nullable=True)
    riderid = Column(Integer, ForeignKey('rider.riderid'), nullable=False)
    areaid = Column(Integer, ForeignKey('surgearea.areaid'), nullable=True)
    ridestatus = Column(String(50), nullable=False)
    pickuploc = Column(Geometry('POINT'), nullable=False)
    dropoffloc = Column(Geometry('POINT'), nullable=False)
    starttime = Column(DateTime, nullable=True)
    endtime = Column(DateTime, nullable=True)
    distancetraveled = Column(Float, nullable=True)
    estimatedarrival = Column(DateTime, nullable=True)
    route = Column(Geometry('LINESTRING'), nullable=True)
    price = Column(Float, nullable=True)

    driver = relationship('Driver')
    rider = relationship('Rider')
    surgearea = relationship('SurgeArea')

class DriverOffer(Base):
    __tablename__ = 'driveroffer'

    tripid = Column(Integer, ForeignKey('trip.tripid'), primary_key=True)
    driverid = Column(Integer, ForeignKey('driver.driverid'), primary_key=True)
    route = Column(Geometry('LINESTRING'), nullable=False)
    price = Column(Float, nullable=False)
    pickuploc = Column(Geometry('POINT'), nullable=False)
    dropoffloc = Column(Geometry('POINT'), nullable=False)
    offerstatus = Column(String(50), nullable=False)

    trip = relationship('Trip')
    driver = relationship('Driver')

# Create all tables
Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    print("All tables created successfully.")
