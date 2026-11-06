import csv
import io
from datetime import date
import streamlit as st
from irrigation import initialize_database, get_plots, add_plot, add_log, get_logs, recommend_irrigation

st.set_page_config(page_title="Smart Irrigation Optimizer", page_icon="💧", layout="wide")
initialize_database()
st.title("💧 Smart Irrigation Optimizer")
st.caption("Practical irrigation planning for farms with or without connected sensors.")
st.sidebar.selectbox("Working as", ["Farmer", "Irrigation operator", "Farm manager"])
st.sidebar.caption("Session context only; this is not an authenticated account.")
page = st.sidebar.radio("Go to", ["Dashboard", "Recommendation", "Manage plots", "Irrigation log", "About"])
plots = [dict(plot) for plot in get_plots()]

if page == "Dashboard":
    st.subheader("Farm overview")
    logs = get_logs()
    a, b, c = st.columns(3)
    a.metric("Managed plots", len(plots))
    b.metric("Irrigation events", len(logs))
    volumes = {p["id"]: p["area_acres"] * 4.047 for p in plots}
    c.metric("Water logged (m³)", round(sum(r["water_mm"] * volumes.get(r["plot_id"], 0) for r in logs), 1))
    if plots:
        query = st.text_input("Search plots by name, location, or crop")
        st.dataframe([dict(p) for p in plots if query.lower() in (p["name"] + p["location"] + p["crop"]).lower()], use_container_width=True, hide_index=True)
    else:
        st.info("No plots yet. Open Manage plots to add your first field.")
    if logs:
        st.markdown("#### Recent irrigation activity")
        st.dataframe([dict(r) for r in logs[:10]], use_container_width=True, hide_index=True)

elif page == "Manage plots":
    st.subheader("Manage farm plots")
    with st.form("plot_form", clear_on_submit=True):
        left, right = st.columns(2)
        name = left.text_input("Plot name *")
        location = right.text_input("Village / location")
        area = left.number_input("Area (acres) *", min_value=.01, value=1., step=.1)
        crop = right.text_input("Crop *", placeholder="e.g., tomato")
        stage = left.selectbox("Growth stage", ["Establishment", "Vegetative", "Flowering/Fruiting", "Maturity"])
        soil = right.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Other"])
        target = left.number_input("Target soil moisture (%)", min_value=1., max_value=100., value=60.)
        if st.form_submit_button("Save plot"):
            if not name.strip() or not crop.strip():
                st.error("Plot name and crop are required.")
            else:
                try:
                    add_plot(name=name.strip(), location=location.strip(), area_acres=area, crop=crop.strip(), growth_stage=stage, soil_type=soil, target_moisture=target)
                    st.success("Plot saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save plot: {exc}")
    if plots:
        st.dataframe([dict(p) for p in plots], use_container_width=True, hide_index=True)

elif page == "Recommendation":
    st.subheader("Irrigation recommendation")
    if not plots:
        st.info("Add a plot before requesting a recommendation.")
    else:
        plot = st.selectbox("Choose plot", plots, format_func=lambda p: f'{p["name"]} — {p["crop"]}')
        moisture = st.slider("Current soil moisture (%)", 0., 100., 35.)
        rain = st.number_input("Expected rain in next 24 hours (mm)", min_value=0., value=0., step=1.)
        if st.button("Calculate recommendation", type="primary"):
            rec = recommend_irrigation(moisture, plot["target_moisture"], rain, plot["growth_stage"], plot["area_acres"])
            if rec["water_mm"] == 0:
                st.success(rec["reason"])
            else:
                x, y = st.columns(2)
                x.metric("Suggested net irrigation", f'{rec["water_mm"]} mm')
                y.metric("Approx. volume for plot", f'{rec["water_m3"]} m³')
                st.write(rec["reason"])
            st.caption("Estimate only. Check local crop guidance, soil conditions, irrigation efficiency, and water restrictions.")

elif page == "Irrigation log":
    st.subheader("Record irrigation")
    if not plots:
        st.info("Add a plot before recording irrigation.")
    else:
        with st.form("log_form", clear_on_submit=True):
            plot = st.selectbox("Plot", plots, format_func=lambda p: p["name"])
            when = st.date_input("Date", value=date.today())
            water = st.number_input("Applied water (mm)", min_value=0., value=0., step=1.)
            minutes = st.number_input("Run time (minutes)", min_value=0, value=0, step=5)
            energy = st.number_input("Energy used (kWh)", min_value=0., value=0., step=.1)
            notes = st.text_input("Notes (optional)")
            if st.form_submit_button("Save irrigation event"):
                try:
                    add_log(plot_id=plot["id"], irrigated_on=when.isoformat(), water_mm=water, duration_minutes=minutes, energy_kwh=energy, notes=notes.strip())
                    st.success("Irrigation event saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save event: {exc}")
    logs = get_logs()
    if logs:
        query = st.text_input("Filter by plot or crop")
        filtered = [r for r in logs if query.lower() in (r["plot_name"] + r["crop"]).lower()]
        st.dataframe([dict(r) for r in filtered], use_container_width=True, hide_index=True)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(logs[0].keys())
        writer.writerows([tuple(r) for r in logs])
        st.download_button("Download CSV report", output.getvalue(), "irrigation_report.csv", "text/csv")

else:
    st.subheader("About this estimate")
    st.write("Plot details and irrigation events are stored in local SQLite. Recommendations use user-entered soil moisture and forecast rain with a visible rule of thumb. The app does not fetch live weather or sensor readings.")
    st.warning("Educational decision support only. Coefficients are illustrative; calibrate them with local agricultural experts before operational use.")
