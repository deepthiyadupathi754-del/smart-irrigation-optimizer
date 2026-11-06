# Smart Irrigation Optimizer

A beginner-friendly Streamlit prototype for planning irrigation from plot details, manually observed soil moisture, and a user-entered rain forecast. It demonstrates how a farm team can avoid relying only on fixed schedules while keeping recommendations explainable.

## Features

- Dashboard with plot count, irrigation activity, water estimate, search, and recent events.
- Plot management for location, area, crop, crop stage, soil type, and target moisture.
- Explainable recommendation using the moisture deficit, a conservative 70% rain credit, a crop-stage factor, and plot area.
- Irrigation log with water, run time, energy, notes, filtering, and CSV export.
- Local SQLite storage; tables are created with `IF NOT EXISTS` and existing rows are not erased.
- Session role selector for farmer, operator, and manager context. This is not account authentication.

## Requirements and run (Windows PowerShell)

1. Install Python 3.10 or newer from python.org and select **Add Python to PATH**.
2. Open PowerShell in this project folder.
3. Create a virtual environment: `py -m venv .venv`
4. Activate it: `.\.venv\Scripts\Activate.ps1`
   - If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.
5. Install dependencies: `python -m pip install -r requirements.txt`
6. Start the app: `python -m streamlit run app.py`
7. Open the local address printed by Streamlit (usually `http://localhost:8501`).

The database file `irrigation.db` is created next to `app.py` when the app starts. Back it up before moving the project to another computer.

## Tests

Run: `python -m unittest -v`

## How the recommendation works

The prototype estimates a moisture deficit as `(target moisture - current moisture) × 0.5`, applies an illustrative growth-stage factor, then subtracts 70% of the entered rain forecast. Negative results become zero. Approximate volume is `net mm × acres × 4.047 m³`. These are demonstration coefficients, not calibrated agricultural advice. Confirm local units, soil water-holding capacity, irrigation method efficiency, crop requirements, and water restrictions with an agricultural expert before operational use. No sensor, weather API, or live farm data is included.

## Streamlit Community Cloud

Push the source files to a GitHub repository, then create a Streamlit Community Cloud app pointing to `app.py`. The SQLite database on a cloud deployment may not be durable across restarts or multiple users. For a class demo this is suitable; for production, use persistent managed storage and access controls.

## Student submission checklist

See `outputs/Submission Guide.md` for the project summary and step-by-step GitHub, deployment, demo, and submission instructions.
