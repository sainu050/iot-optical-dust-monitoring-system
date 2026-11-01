import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATA_DIR = os.getenv("DATA_DIR", "/app/data" if os.path.exists("/app") else "./data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "sensor_readings.db").replace("\\", "/")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorRecord(Base):
    __tablename__ = "dust_readings"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    voltage = Column(Float)
    dust_density = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IoT Dust Monitoring System",
    description="Containerized Backend for ESP32 Optical Dust Sensor Telemetry",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SensorPayload(BaseModel):
    device_id: str
    voltage: float
    dust_density: float

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "iot-dust-backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/sensor-data")
def receive_sensor_data(payload: SensorPayload):
    db = SessionLocal()
    try:
        record = SensorRecord(
            device_id=payload.device_id,
            voltage=payload.voltage,
            dust_density=payload.dust_density
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "status": "success",
            "message": "Data saved",
            "id": record.id,
            "timestamp": record.timestamp.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/sensor-data/latest")
def get_latest_readings(limit: int = 20):
    db = SessionLocal()
    try:
        records = db.query(SensorRecord).order_by(SensorRecord.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "device_id": r.device_id,
                "voltage": r.voltage,
                "dust_density": r.dust_density,
                "timestamp": r.timestamp.strftime("%H:%M:%S")
            }
            for r in reversed(records)
        ]
    finally:
        db.close()

@app.get("/api/sensor-data/summary")
def get_sensor_summary():
    db = SessionLocal()
    try:
        records = db.query(SensorRecord).all()
        if not records:
            return {"count": 0, "avg_dust": 0.0, "max_dust": 0.0, "avg_voltage": 0.0}
        total_dust = sum(r.dust_density for r in records)
        max_dust = max(r.dust_density for r in records)
        avg_voltage = sum(r.voltage for r in records) / len(records)
        return {
            "count": len(records),
            "avg_dust": round(total_dust / len(records), 2),
            "max_dust": round(max_dust, 2),
            "avg_voltage": round(avg_voltage, 2)
        }
    finally:
        db.close()

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")