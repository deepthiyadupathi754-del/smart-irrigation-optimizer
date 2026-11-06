"""SQLite storage and transparent irrigation estimate for the demo app."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "irrigation.db"


def connect(db_path=DB_PATH):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


@contextmanager
def database_session(db_path=DB_PATH):
    """Commit successful work and always close SQLite handles (important on Windows)."""
    db = connect(db_path)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize_database(db_path=DB_PATH):
    """Create missing tables without dropping or changing existing records."""
    with database_session(db_path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE, location TEXT NOT NULL DEFAULT '',
            area_acres REAL NOT NULL CHECK(area_acres > 0), crop TEXT NOT NULL,
            growth_stage TEXT NOT NULL, soil_type TEXT NOT NULL,
            target_moisture REAL NOT NULL CHECK(target_moisture BETWEEN 1 AND 100),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS irrigation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL REFERENCES plots(id) ON DELETE RESTRICT,
            irrigated_on TEXT NOT NULL, water_mm REAL NOT NULL CHECK(water_mm >= 0),
            duration_minutes INTEGER NOT NULL CHECK(duration_minutes >= 0),
            energy_kwh REAL NOT NULL CHECK(energy_kwh >= 0), notes TEXT NOT NULL DEFAULT ''
        );
        """)


def add_plot(db_path=DB_PATH, **plot):
    with database_session(db_path) as db:
        db.execute("""INSERT INTO plots(name,location,area_acres,crop,growth_stage,soil_type,target_moisture)
        VALUES(:name,:location,:area_acres,:crop,:growth_stage,:soil_type,:target_moisture)""", plot)


def get_plots(db_path=DB_PATH):
    with database_session(db_path) as db:
        return db.execute("SELECT * FROM plots ORDER BY name").fetchall()


def add_log(db_path=DB_PATH, **log):
    with database_session(db_path) as db:
        db.execute("""INSERT INTO irrigation_logs(plot_id,irrigated_on,water_mm,duration_minutes,energy_kwh,notes)
        VALUES(:plot_id,:irrigated_on,:water_mm,:duration_minutes,:energy_kwh,:notes)""", log)


def get_logs(db_path=DB_PATH):
    with database_session(db_path) as db:
        return db.execute("""SELECT l.*,p.name AS plot_name,p.crop FROM irrigation_logs l
        JOIN plots p ON p.id=l.plot_id ORDER BY l.irrigated_on DESC,l.id DESC""").fetchall()


def recommend_irrigation(moisture_pct, target_pct, rain_forecast_mm, crop_stage, area_acres):
    """Illustrative screening estimate; local expert guidance takes precedence."""
    if not 0 <= moisture_pct <= 100 or not 1 <= target_pct <= 100:
        raise ValueError("Moisture must be 0–100% and target must be 1–100%.")
    if rain_forecast_mm < 0 or area_acres <= 0:
        raise ValueError("Rain cannot be negative and area must be positive.")
    factors = {"Establishment": .9, "Vegetative": 1., "Flowering/Fruiting": 1.15, "Maturity": .8}
    deficit = max(0., target_pct - moisture_pct) * .5 * factors.get(crop_stage, 1.)
    net_mm = max(0., deficit - rain_forecast_mm * .7)
    reason = "Moisture is at/above target; defer irrigation." if net_mm == 0 else "Estimated moisture deficit adjusted for effective forecast rain and crop stage."
    return {"water_mm": round(net_mm, 1), "water_m3": round(net_mm * area_acres * 4.047, 1), "reason": reason}
