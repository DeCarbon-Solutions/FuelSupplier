import streamlit as st
import pandas as pd
import plotly.express as px
import math
import datetime # For footer

# *** FIX: Call set_page_config() immediately after imports ***
st.set_page_config(layout="wide")
# ************************************************************

# --- Configuration ---
YEAR_OPTIONS = [2030, 2040, 2050]
VESSEL_TYPES_OWNED = ["VLCC", "Suezmax", "Aframax", "Panamax", "MR Tanker"]
MILLION = 1_000_000
# ... (Paste the rest of your config dictionaries: ROUTE_INFO, DEFAULT_EXPORT_VOLUMES,
#      VESSEL_CONSUMPTION_FACTORS, FUEL_MIX_CATEGORIES, DEFAULT_FUEL_MIX,
#      DEFAULT_FUEL_COSTS_GJ, ALL_FUEL_MIX_KEYS) ...
# Fuel Mix Categories
FUEL_MIX_CATEGORIES = {
    2030: {"diesel_prod": "Diesel (Produced)", "b30_prod": "B30 (Produced)", "methanol_prod": "Methanol (Produced)", "methanol_proc": "Methanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "hvo_prod": "HVO (Produced)", "hvo_proc": "HVO (Procured)"},
    2040: {"diesel_prod": "Diesel (Produced)", "b50_prod": "B50 (Produced)", "methanol_prod": "Methanol (Produced)", "methanol_proc": "Methanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "hvo_prod": "HVO (Produced)", "hvo_proc": "HVO (Procured)", "biolng_prod": "BioLNG (Produced)", "biolng_proc": "BioLNG (Procured)", "blueh2_prod": "BlueH2 (Produced)", "blueh2_proc": "BlueH2 (Procured)"},
    2050: {"diesel_prod": "Diesel (Produced)", "b100_prod": "B100 (Produced)", "b100_proc": "B100 (Procured)", "biomethanol_prod": "bioMethanol (Produced)", "biomethanol_proc": "bioMethanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "biolng_prod": "BioLNG (Produced)", "biolng_proc": "BioLNG (Procured)", "blueh2_prod": "BlueH2 (Produced)", "blueh2_proc": "BlueH2 (Procured)", "elng_prod": "eLNG (Produced)", "elng_proc": "eLNG (Procured)", "ediesel_prod": "eDiesel (Produced)", "ediesel_proc": "eDiesel (Procured)", "emethanol_prod": "eMethanol (Produced)", "emethanol_proc": "eMethanol (Procured)"}
}
# Default Fuel Mix Percentages
DEFAULT_FUEL_MIX = {
    2030: {"diesel_prod": 92.91, "b30_prod": 1.54, "methanol_prod": 0.01, "methanol_proc": 0.00, "ammonia_prod": 0.02, "ammonia_proc": 0.01, "hvo_prod": 0.02, "hvo_proc": 5.49},
    2040: {"diesel_prod": 7.49, "b50_prod": 2.10, "methanol_prod": 10.80, "methanol_proc": 0.02, "ammonia_prod": 7.80, "ammonia_proc": 8.07, "hvo_prod": 12.78, "hvo_proc": 12.60, "biolng_prod": 11.83, "biolng_proc": 11.27, "blueh2_prod": 7.69, "blueh2_proc": 7.56},
    2050: {"diesel_prod": 11.66, "b100_prod": 11.60, "b100_proc": 7.90, "biomethanol_prod": 8.22, "biomethanol_proc": 5.14, "ammonia_prod": 4.84, "ammonia_proc": 0.03, "biolng_prod": 21.30, "biolng_proc": 16.26, "blueh2_prod": 1.46, "blueh2_proc": 0.61, "elng_prod": 3.06, "elng_proc": 2.91, "ediesel_prod": 0.87, "ediesel_proc": 0.02, "emethanol_prod": 1.99, "emethanol_proc": 2.13}
}
# Consumption Factors (GJ/Year per vessel)
VESSEL_CONSUMPTION_FACTORS = {
    2030: {"vlcc": 1306537.24, "suezmax": 618990.62, "aframax": 526902.73, "panamax": 468391.74, "mr_tanker": 355173.15},
    2040: {"vlcc": 1304860.84, "suezmax": 617547.63, "aframax": 525203.36, "panamax": 467124.63, "mr_tanker": 354390.79},
    2050: {"vlcc": 1303743.24, "suezmax": 616585.64, "aframax": 524070.44, "panamax": 466279.89, "mr_tanker": 353869.23}
}
# Default Fuel Costs ($/GJ)
DEFAULT_FUEL_COSTS_GJ = {
    2030: {"diesel_prod": 11.51, "b30_prod": 14.76, "methanol_prod": 30.68, "methanol_proc": 33.44, "ammonia_prod": 43.54, "ammonia_proc": 47.46, "hvo_prod": 25.43, "hvo_proc": 23.33},
    2040: {"diesel_prod": 10.46, "b50_prod": 13.1, "methanol_prod": 26.18, "methanol_proc": 28.54, "ammonia_prod": 43.54, "ammonia_proc": 36.6, "hvo_prod": 22.82, "hvo_proc": 23.33, "biolng_prod": 20.03, "biolng_proc": 21.83, "blueh2_prod": 40.81, "blueh2_proc": 44.48},
    2050: {"diesel_prod": 8.72, "b100_prod": 22.17, "b100_proc": 24.16, "biomethanol_prod": 23.63, "biomethanol_proc": 25.75, "ammonia_prod": 26.62, "ammonia_proc": 28.8, "biolng_prod": 17.42, "biolng_proc": 18.99, "blueh2_prod": 39.41, "blueh2_proc": 42.96, "elng_prod": 35.27, "elng_proc": 35.73, "ediesel_prod": 43.34, "ediesel_proc": 47.23, "emethanol_prod": 38.94, "emethanol_proc": 38.44}
}
ALL_FUEL_MIX_KEYS = set().union(*(d.keys() for d in FUEL_MIX_CATEGORIES.values()))


# --- Helper Function for Formatting ---
def format_value(value, sig_figs=3):
    if value is None or math.isnan(value) or abs(value) < 1e-9: return "0.00"
    try: return f"{value:.{sig_figs}g}"
    except (ValueError, TypeError): return str(value)

# --- Initialize Session State (runs only if keys don't exist) ---
if 'selected_year' not in st.session_state: st.session_state.selected_year = YEAR_OPTIONS[0]
if 'results' not in st.session_state: st.session_state.results = None
if 'show_results' not in st.session_state: st.session_state.show_results = False
if 'reset_request_for_year' not in st.session_state: st.session_state.reset_request_for_year = None

for vessel in VESSEL_TYPES_OWNED:
    key = f"owned_{vessel.lower().replace(' ', '_')}"
    if key not in st.session_state: st.session_state[key] = 0

initial_year_defaults = DEFAULT_FUEL_MIX.get(YEAR_OPTIONS[0], {})
for key in ALL_FUEL_MIX_KEYS:
    if key not in st.session_state:
        st.session_state[key] = initial_year_defaults.get(key, 0.0)

# --- Process Reset Request (Place this *after* initialization, before layout) ---
if st.session_state.get('reset_request_for_year'):
    year_to_reset = st.session_state.reset_request_for_year
    # print(f"DEBUG: Resetting defaults for year {year_to_reset}") # Use print for debugging if needed
    defaults_to_set = DEFAULT_FUEL_MIX.get(year_to_reset, {})
    categories_to_reset = FUEL_MIX_CATEGORIES.get(year_to_reset, {}).keys()
    for key in categories_to_reset:
        if key in st.session_state:
            st.session_state[key] = defaults_to_set.get(key, 0.0)
    st.session_state.reset_request_for_year = None # Clear the flag

# --- Callback ---
def clear_results_on_change():
    st.session_state.results = None
    st.session_state.show_results = False

# --- App Layout ---
# Title etc. come AFTER set_page_config and reset processing
st.title("⛽ Fuel Supplier Decision Making Tool")
st.divider()

# --- Input Section ---
col_main_1, col_main_2 = st.columns([1, 1])

with col_main_1:
    st.subheader("1. Select Year & Fleet")
    # Widget reads value from st.session_state['selected_year']
    selected_year_widget = st.selectbox(
        "Select Target Year:", options=YEAR_OPTIONS, key='selected_year',
        on_change=clear_results_on_change
    )
    st.markdown("**Owned Vessel Counts:**")
    for vessel in VESSEL_TYPES_OWNED:
        key = f"owned_{vessel.lower().replace(' ', '_')}"
        st.number_input(f"# Owned {vessel}", min_value=0, step=1, key=key, on_change=clear_results_on_change)

with col_main_2:
    selected_year = st.session_state.selected_year # Get current year for display
    st.subheader(f"2. Input Fuel Mix (%) for {selected_year}")
    st.markdown("_Source: External Analysis (e.g., Matlab)_")
    current_fuel_mix_categories = FUEL_MIX_CATEGORIES.get(selected_year, {})
    if not current_fuel_mix_categories:
        st.error(f"Fuel mix configuration not found for year {selected_year}.")
    else:
        cols_mix_inner = st.columns(2)
        col_idx = 0
        total_percentage = 0.0
        current_year_defaults = DEFAULT_FUEL_MIX.get(selected_year, {}) # Needed for reset button logic
        for key, display_name in current_fuel_mix_categories.items():
            with cols_mix_inner[col_idx]:
                 st.number_input(
                     display_name.replace(" Percentage", ""), min_value=0.0, max_value=100.0,
                     step=1.0, format="%.2f", key=key, help="Percentage (0-100).",
                     on_change=clear_results_on_change
                 )
                 total_percentage += st.session_state.get(key, 0.0)
            col_idx = (col_idx + 1) % 2
        if not math.isclose(total_percentage, 100.0, abs_tol=0.1):
            st.warning(f"Mix % sum = {total_percentage:.2f}%. Should be 100%.")
        else:
            st.success(f"Mix % sum = {total_percentage:.2f}%.")

        # --- Corrected Reset Button Logic ---
        if st.button(f"Reset {selected_year} Mix to Defaults"):
            # Set the flag. The processing block at the top will handle it on the next rerun.
            st.session_state.reset_request_for_year = selected_year
            # Rerun is implicitly triggered by the button click
            st.rerun() # Explicit rerun MAY help ensure flag is processed first


st.divider()

# --- Calculation Trigger ---
st.header("📊 Calculate & Visualize")
if st.button("Run Calculation", type="primary"):
    # (Calculation logic remains the same)
    current_year = st.session_state.selected_year
    current_consumption_factors = VESSEL_CONSUMPTION_FACTORS.get(current_year)
    current_fuel_mix_categories = FUEL_MIX_CATEGORIES.get(current_year)
    current_fuel_costs_gj = DEFAULT_FUEL_COSTS_GJ.get(current_year)
    if not current_consumption_factors or not current_fuel_mix_categories or not current_fuel_costs_gj:
        st.error(f"Config missing for {current_year}."); clear_results_on_change()
    else:
        total_percentage = sum(st.session_state.get(key, 0.0) for key in current_fuel_mix_categories.keys())
        if not math.isclose(total_percentage, 100.0, abs_tol=0.1):
             st.error(f"Cannot proceed. Fuel mix % must sum to 100%."); clear_results_on_change()
        else:
            fleet_cons_by_type = {}; total_annual_cons = 0.0
            fuel_cons_by_mix = {}; fuel_mix_perc = {}
            fuel_cost_by_mix = {}; total_fuel_cost = 0.0
            prod_vs_proc_cost = {'Produced': 0.0, 'Procured': 0.0}
            with st.spinner(f"Calculating for {current_year}..."):
                for vessel in VESSEL_TYPES_OWNED:
                    v_key = f"owned_{vessel.lower().replace(' ', '_')}"
                    factor_key = vessel.lower().replace(' ', '_')
                    consumption = st.session_state.get(v_key, 0) * current_consumption_factors.get(factor_key, 0)
                    fleet_cons_by_type[vessel] = consumption
                    total_annual_cons += consumption
                for key, display_name in current_fuel_mix_categories.items():
                    percentage = st.session_state.get(key, 0.0)
                    cost_gj = current_fuel_costs_gj.get(key, 0.0)
                    if cost_gj == 0.0 and percentage > 0: st.warning(f"Cost=0 for {display_name}")
                    fuel_consumption_gj = total_annual_cons * (percentage / 100.0)
                    fuel_cost_usd = fuel_consumption_gj * cost_gj
                    fuel_cons_by_mix[display_name] = fuel_consumption_gj
                    fuel_cost_by_mix[display_name] = fuel_cost_usd / MILLION
                    fuel_mix_perc[display_name] = percentage
                    total_fuel_cost += fuel_cost_usd
                    if "(Produced)" in display_name: prod_vs_proc_cost['Produced'] += fuel_cost_usd
                    elif "(Procured)" in display_name: prod_vs_proc_cost['Procured'] += fuel_cost_usd
            total_fuel_cost_million = total_fuel_cost / MILLION
            prod_vs_proc_cost['Produced'] /= MILLION
            prod_vs_proc_cost['Procured'] /= MILLION
            st.session_state.results = {"fleet_consumption_by_type": fleet_cons_by_type, "fuel_mix_percentages": fuel_mix_perc, "total_annual_consumption": total_annual_cons, "fuel_consumption_by_mix": fuel_cons_by_mix, "fuel_cost_by_mix": fuel_cost_by_mix, "total_fuel_cost_million": total_fuel_cost_million, "prod_vs_proc_cost_million": prod_vs_proc_cost, "calculated_for_year": current_year}
            st.session_state.show_results = True
            st.success(f"Calculation Complete for {current_year}!")

st.divider()

# --- Output Section ---
# (Output display logic remains the same)
st.header("📈 Calculation Outputs")
if st.session_state.show_results and st.session_state.results:
    results = st.session_state.results; calc_year = results["calculated_for_year"]
    st.subheader(f"Annual Fuel Analysis (Year: {calc_year})")
    m_col1, m_col2 = st.columns(2)
    with m_col1: st.metric(label="Total Annual Fleet Consumption", value=f"{results['total_annual_consumption']:,.2f} GJ/Year")
    with m_col2: st.metric(label="Total Annual Fuel Expenditure", value=f"{format_value(results['total_fuel_cost_million'], 3)} Million USD")
    st.divider()
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    with row1_col1: # Table
        st.markdown("**Fuel Volume & Cost Breakdown**")
        breakdown_data = []
        sorted_mix_keys = sorted(results["fuel_consumption_by_mix"].keys())
        for fuel_name in sorted_mix_keys:
            if results["fuel_consumption_by_mix"][fuel_name] > 1e-9: breakdown_data.append({"Fuel Source": fuel_name, "Consumption (GJ/Year)": results["fuel_consumption_by_mix"][fuel_name], "Cost (Million USD/Year)": results["fuel_cost_by_mix"][fuel_name]})
        if breakdown_data: df_breakdown = pd.DataFrame(breakdown_data); st.dataframe(df_breakdown.style.format({"Consumption (GJ/Year)": "{:,.0f}", "Cost (Million USD/Year)": "{:,.3f}"}), height = 350, use_container_width=True)
        else: st.info("No significant consumption.")
    with row1_col2: # Pie Chart
        st.markdown("**Cost Contribution by Fuel Source**")
        cost_data = {k: v for k, v in results["fuel_cost_by_mix"].items() if v > 1e-9}
        if cost_data: df_cost_pie = pd.DataFrame(cost_data.items(), columns=['Fuel Source', 'Cost (Million USD/Year)']); fig_cost_pie = px.pie(df_cost_pie, values='Cost (Million USD/Year)', names='Fuel Source', hole=0.3); fig_cost_pie.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value'); fig_cost_pie.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20)); st.plotly_chart(fig_cost_pie, use_container_width=True)
        else: st.info("No cost data.")
    with row2_col1: # Prod/Proc Bar
        st.markdown("**Production vs. Procurement Costs**")
        prod_proc_data = results['prod_vs_proc_cost_million']
        if sum(prod_proc_data.values()) > 1e-9: df_prod_proc = pd.DataFrame(prod_proc_data.items(), columns=['Source Type', 'Total Cost (Million USD)']); fig_prod_proc = px.bar(df_prod_proc, x='Source Type', y='Total Cost (Million USD)', text_auto='.3s', labels={'Total Cost (Million USD)': 'Million USD/Year'}); fig_prod_proc.update_layout(xaxis_title=None, height=350, margin=dict(b=50)); fig_prod_proc.update_traces(textposition='outside'); st.plotly_chart(fig_prod_proc, use_container_width=True)
        else: st.info("Costs effectively zero.")
    with row2_col2: # Vessel Consumption Bar
        st.markdown("**Consumption by Vessel Type**")
        if results["fleet_consumption_by_type"] and any(abs(v) > 1e-9 for v in results["fleet_consumption_by_type"].values()):
            df_type = pd.DataFrame(results["fleet_consumption_by_type"].items(), columns=['Vessel Type', 'Consumption (GJ/Year)']); df_type_plot = df_type[abs(df_type['Consumption (GJ/Year)']) > 1e-9]
            if not df_type_plot.empty: fig_type = px.bar(df_type_plot, x='Vessel Type', y='Consumption (GJ/Year)', text_auto='.3s', labels={'Consumption (GJ/Year)': 'GJ / Year'}); fig_type.update_layout(xaxis_tickangle=-45, height=350, margin=dict(b=50)); fig_type.update_traces(textposition='outside'); st.plotly_chart(fig_type, use_container_width=True)
            else: st.info("Consumptions effectively zero.")
        else: st.info("No vessel consumption data.")
else:
    if not st.session_state.show_results: st.info("Click 'Run Calculation' after entering parameters.")

# --- Footer ---
st.divider()
current_year = datetime.datetime.now().year
st.caption(f"© {current_year} by Dr. Chenxi Ji, ABS EAL Lead")
st.caption("Disclaimer: Calculations based on user inputs and predefined factors.")