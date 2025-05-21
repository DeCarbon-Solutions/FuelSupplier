import streamlit as st
import pandas as pd
import plotly.express as px # For Plotly charts
import math
import datetime # For footer
import matplotlib.pyplot as plt # For Matplotlib charts
import matplotlib.ticker as mticker
from io import StringIO # To read string data as if it's a file
import re # For more flexible parsing
import numpy as np # For np.nan

# *** Call set_page_config() immediately after imports ***
st.set_page_config(layout="wide")

# --- Configuration ---
YEAR_OPTIONS = [2030, 2040, 2050]
VESSEL_TYPES_OWNED = ["VLCC", "Suezmax", "Aframax", "Panamax", "MR Tanker"]
MILLION = 1_000_000

DEFAULT_OWNED_VESSEL_COUNTS = {
    2030: {"vlcc": 18, "suezmax": 29, "aframax": 5, "panamax": 1, "mr_tanker": 4},
    2040: {"vlcc": 18, "suezmax": 29, "aframax": 5, "panamax": 0, "mr_tanker": 0},
    2050: {"vlcc": 18, "suezmax": 29, "aframax": 0, "panamax": 0, "mr_tanker": 0},
}

# NEW: Default Fleet GFI values for plotting
DEFAULT_FLEET_GFI = {
    2030: 85.8,
    2040: 14.0,
    2050: 16.8
}

FUEL_MIX_CATEGORIES = {
    2030: {"diesel_prod": "Diesel (Produced)", "b30_prod": "B30 (Produced)", "methanol_prod": "Methanol (Produced)", "methanol_proc": "Methanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "hvo_prod": "HVO (Produced)", "hvo_proc": "HVO (Procured)"},
    2040: {"diesel_prod": "Diesel (Produced)", "b50_prod": "B50 (Produced)", "methanol_prod": "Methanol (Produced)", "methanol_proc": "Methanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "hvo_prod": "HVO (Produced)", "hvo_proc": "HVO (Procured)", "biolng_prod": "BioLNG (Produced)", "biolng_proc": "BioLNG (Procured)", "blueh2_prod": "BlueH2 (Produced)", "blueh2_proc": "BlueH2 (Procured)"},
    2050: {"diesel_prod": "Diesel (Produced)", "b100_prod": "B100 (Produced)", "b100_proc": "B100 (Procured)", "biomethanol_prod": "bioMethanol (Produced)", "biomethanol_proc": "bioMethanol (Procured)", "ammonia_prod": "Ammonia (Produced)", "ammonia_proc": "Ammonia (Procured)", "biolng_prod": "BioLNG (Produced)", "biolng_proc": "BioLNG (Procured)", "blueh2_prod": "BlueH2 (Produced)", "blueh2_proc": "BlueH2 (Procured)", "elng_prod": "eLNG (Produced)", "elng_proc": "eLNG (Procured)", "ediesel_prod": "eDiesel (Produced)", "ediesel_proc": "eDiesel (Procured)", "emethanol_prod": "eMethanol (Produced)", "emethanol_proc": "eMethanol (Procured)"}
}
DEFAULT_FUEL_MIX = {
    2030: {"diesel_prod": 92.91, "b30_prod": 1.54, "methanol_prod": 0.01, "methanol_proc": 0.00, "ammonia_prod": 0.02, "ammonia_proc": 0.01, "hvo_prod": 0.02, "hvo_proc": 5.49},
    2040: {"diesel_prod": 7.49, "b50_prod": 2.10, "methanol_prod": 10.80, "methanol_proc": 0.02, "ammonia_prod": 7.80, "ammonia_proc": 8.07, "hvo_prod": 12.78, "hvo_proc": 12.60, "biolng_prod": 11.83, "biolng_proc": 11.27, "blueh2_prod": 7.69, "blueh2_proc": 7.56},
    2050: {"diesel_prod": 11.66, "b100_prod": 11.60, "b100_proc": 7.90, "biomethanol_prod": 8.22, "biomethanol_proc": 5.14, "ammonia_prod": 4.84, "ammonia_proc": 0.03, "biolng_prod": 21.30, "biolng_proc": 16.26, "blueh2_prod": 1.46, "blueh2_proc": 0.61, "elng_prod": 3.06, "elng_proc": 2.91, "ediesel_prod": 0.87, "ediesel_proc": 0.02, "emethanol_prod": 1.99, "emethanol_proc": 2.13}
}
VESSEL_CONSUMPTION_FACTORS = {
    2030: {"vlcc": 1306537.24, "suezmax": 618990.62, "aframax": 526902.73, "panamax": 468391.74, "mr_tanker": 355173.15},
    2040: {"vlcc": 1304860.84, "suezmax": 617547.63, "aframax": 525203.36, "panamax": 467124.63, "mr_tanker": 354390.79},
    2050: {"vlcc": 1303743.24, "suezmax": 616585.64, "aframax": 524070.44, "panamax": 466279.89, "mr_tanker": 353869.23}
}
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

# --- Callbacks ---
def clear_results_if_individual_input_changes():
    st.session_state.results = None
    st.session_state.show_results = False
    # Clear GFI data if individual inputs change, as it's tied to a full calculation run
    if 'calculated_fleet_gfi' in st.session_state:
        del st.session_state.calculated_fleet_gfi
    if 'gfi_calculation_year' in st.session_state:
        del st.session_state.gfi_calculation_year


def handle_year_selection_change():
    st.session_state.results = None
    st.session_state.show_results = False
    if 'calculated_fleet_gfi' in st.session_state:
        del st.session_state.calculated_fleet_gfi
    if 'gfi_calculation_year' in st.session_state:
        del st.session_state.gfi_calculation_year

    newly_selected_year = st.session_state.selected_year
    year_vessel_defaults = DEFAULT_OWNED_VESSEL_COUNTS.get(newly_selected_year, {})
    for vessel_type_display in VESSEL_TYPES_OWNED:
        internal_key_for_defaults = vessel_type_display.lower().replace(' ', '_')
        session_state_key = f"owned_{internal_key_for_defaults}"
        st.session_state[session_state_key] = year_vessel_defaults.get(internal_key_for_defaults, 0)
    st.session_state.reset_request_for_year = newly_selected_year

# --- Initialize Session State ---
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = YEAR_OPTIONS[0]
if 'results' not in st.session_state:
    st.session_state.results = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'reset_request_for_year' not in st.session_state:
    st.session_state.reset_request_for_year = None
if 'fuel_mix_defaults_loaded_for_year' not in st.session_state:
    st.session_state.fuel_mix_defaults_loaded_for_year = None
# For GFI plotting
if 'calculated_fleet_gfi' not in st.session_state:
    st.session_state.calculated_fleet_gfi = None
if 'gfi_calculation_year' not in st.session_state:
    st.session_state.gfi_calculation_year = None


_current_year_for_init = st.session_state.selected_year
_initial_vessel_counts_for_year = DEFAULT_OWNED_VESSEL_COUNTS.get(_current_year_for_init, {})
for vessel_type_display in VESSEL_TYPES_OWNED:
    _internal_key = vessel_type_display.lower().replace(' ', '_')
    _ss_key = f"owned_{_internal_key}"
    if _ss_key not in st.session_state:
        st.session_state[_ss_key] = _initial_vessel_counts_for_year.get(_internal_key, 0)

_initial_fuel_mix_for_year = DEFAULT_FUEL_MIX.get(_current_year_for_init, {})
for key in ALL_FUEL_MIX_KEYS:
    if key not in st.session_state:
        st.session_state[key] = _initial_fuel_mix_for_year.get(key, 0.0)

if st.session_state.fuel_mix_defaults_loaded_for_year != st.session_state.selected_year:
    st.session_state.reset_request_for_year = st.session_state.selected_year

# --- Process Reset Request for Fuel Mix ---
if st.session_state.get('reset_request_for_year'):
    year_to_reset = st.session_state.reset_request_for_year
    defaults_to_set = DEFAULT_FUEL_MIX.get(year_to_reset, {})
    categories_to_reset = FUEL_MIX_CATEGORIES.get(year_to_reset, {}).keys()
    for key in categories_to_reset:
        if key in st.session_state:
            st.session_state[key] = defaults_to_set.get(key, 0.0)
    st.session_state.fuel_mix_defaults_loaded_for_year = year_to_reset
    st.session_state.reset_request_for_year = None

# --- App Layout ---
st.title("⛽ Fuel Supplier Decision Making Tool")
st.divider()

# --- Input Section ---
col_main_1, col_main_2 = st.columns([1, 1])

with col_main_1:
    st.subheader("1. Select Year & Fleet")
    selected_year_widget = st.selectbox(
        "Select Target Year:", options=YEAR_OPTIONS, key='selected_year',
        on_change=handle_year_selection_change
    )
    st.markdown("**Owned Vessel Counts:**")
    for vessel in VESSEL_TYPES_OWNED:
        key = f"owned_{vessel.lower().replace(' ', '_')}"
        st.number_input(
            f"# Owned {vessel}", min_value=0, step=1, key=key,
            on_change=clear_results_if_individual_input_changes
        )
    # Manual GFI input removed. GFI will be taken from DEFAULT_FLEET_GFI based on selected year.

with col_main_2:
    selected_year = st.session_state.selected_year
    st.subheader(f"2. Input Fuel Mix (%) for {selected_year}")
    st.markdown("_Source: External Analysis (e.g., Matlab)_")
    current_fuel_mix_categories = FUEL_MIX_CATEGORIES.get(selected_year, {})
    if not current_fuel_mix_categories:
        st.error(f"Fuel mix configuration not found for year {selected_year}.")
    else:
        cols_mix_inner = st.columns(2)
        col_idx = 0
        total_percentage = 0.0
        for key, display_name in current_fuel_mix_categories.items():
            with cols_mix_inner[col_idx]:
                 st.number_input(
                     display_name.replace(" Percentage", ""), min_value=0.0, max_value=100.0,
                     step=1.0, format="%.2f", key=key, help="Percentage (0-100).",
                     on_change=clear_results_if_individual_input_changes
                 )
                 total_percentage += st.session_state.get(key, 0.0)
            col_idx = (col_idx + 1) % 2
        
        if not math.isclose(total_percentage, 100.0, abs_tol=0.1):
            st.warning(f"Mix % sum = {total_percentage:.2f}%. Should be 100%.")
        else:
            st.success(f"Mix % sum = {total_percentage:.2f}%.")

        if st.button(f"Reset {selected_year} Mix to Defaults"):
            st.session_state.reset_request_for_year = selected_year
            st.rerun()


st.divider()

# --- Calculation Trigger ---
st.header("📊 Calculate & Visualize")
if st.button("Run Calculation", type="primary"):
    current_year = st.session_state.selected_year
    current_consumption_factors = VESSEL_CONSUMPTION_FACTORS.get(current_year)
    current_fuel_mix_categories = FUEL_MIX_CATEGORIES.get(current_year)
    current_fuel_costs_gj = DEFAULT_FUEL_COSTS_GJ.get(current_year)

    if not current_consumption_factors or not current_fuel_mix_categories or not current_fuel_costs_gj:
        st.error(f"Configuration missing for {current_year}.")
        clear_results_if_individual_input_changes()
    else:
        total_percentage = sum(st.session_state.get(key, 0.0) for key in current_fuel_mix_categories.keys())
        if not math.isclose(total_percentage, 100.0, abs_tol=0.1):
             st.error(f"Cannot proceed. Fuel mix % must sum to 100%.")
             clear_results_if_individual_input_changes()
        else:
            fleet_cons_by_type = {}
            total_annual_cons = 0.0
            fuel_cons_by_mix = {}
            fuel_mix_perc = {}
            fuel_cost_by_mix = {}
            total_fuel_cost = 0.0
            prod_vs_proc_cost = {'Produced': 0.0, 'Procured': 0.0}
            base_fuel_demand_gj = {}

            with st.spinner(f"Calculating for {current_year}..."):
                for vessel in VESSEL_TYPES_OWNED:
                    v_key = f"owned_{vessel.lower().replace(' ', '_')}"
                    factor_key = vessel.lower().replace(' ', '_')
                    num_vessels = st.session_state.get(v_key, 0)
                    consumption_per_vessel = current_consumption_factors.get(factor_key, 0)
                    consumption = num_vessels * consumption_per_vessel
                    fleet_cons_by_type[vessel] = consumption
                    total_annual_cons += consumption

                for key, display_name in current_fuel_mix_categories.items():
                    percentage = st.session_state.get(key, 0.0)
                    cost_gj = current_fuel_costs_gj.get(key, 0.0)
                    if cost_gj == 0.0 and percentage > 0:
                        st.warning(f"Cost is $0/GJ for {display_name} which has a {percentage:.2f}% share.")
                    fuel_consumption_gj = total_annual_cons * (percentage / 100.0)
                    fuel_cost_usd = fuel_consumption_gj * cost_gj
                    
                    fuel_cons_by_mix[display_name] = fuel_consumption_gj
                    fuel_cost_by_mix[display_name] = fuel_cost_usd / MILLION
                    fuel_mix_perc[display_name] = percentage
                    total_fuel_cost += fuel_cost_usd

                    if "(Produced)" in display_name:
                        prod_vs_proc_cost['Produced'] += fuel_cost_usd
                    elif "(Procured)" in display_name:
                        prod_vs_proc_cost['Procured'] += fuel_cost_usd
                    
                    base_name = display_name.replace(" (Produced)", "").replace(" (Procured)", "")
                    base_fuel_demand_gj[base_name] = base_fuel_demand_gj.get(base_name, 0.0) + fuel_consumption_gj
            
            total_fuel_cost_million = total_fuel_cost / MILLION
            prod_vs_proc_cost['Produced'] /= MILLION
            prod_vs_proc_cost['Procured'] /= MILLION

            st.session_state.results = {
                "fleet_consumption_by_type": fleet_cons_by_type,
                "fuel_mix_percentages": fuel_mix_perc,
                "total_annual_consumption": total_annual_cons,
                "fuel_consumption_by_mix": fuel_cons_by_mix,
                "fuel_cost_by_mix": fuel_cost_by_mix,
                "total_fuel_cost_million": total_fuel_cost_million,
                "prod_vs_proc_cost_million": prod_vs_proc_cost,
                "base_fuel_demand_gj": base_fuel_demand_gj,
                "calculated_for_year": current_year
            }
            st.session_state.show_results = True
            
            # MODIFICATION: Set GFI for plotting from defaults
            st.session_state.calculated_fleet_gfi = DEFAULT_FLEET_GFI.get(current_year)
            st.session_state.gfi_calculation_year = current_year

            st.success(f"Calculation Complete for {current_year}!")

st.divider()

# --- Output Section: Main Calculation Results ---
st.header("📈 Calculation Outputs")
if st.session_state.show_results and st.session_state.results:
    results = st.session_state.results
    calc_year = results["calculated_for_year"]
    
    st.subheader(f"Annual Fuel Analysis (Year: {calc_year})")
    
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric(label="Total Annual Fleet Consumption", value=f"{results['total_annual_consumption']:,.2f} GJ/Year")
    with m_col2:
        st.metric(label="Total Annual Fuel Expenditure", value=f"{format_value(results['total_fuel_cost_million'], 3)} Million USD")
    
    st.divider()
    
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.markdown("**Fuel Volume & Cost Breakdown (by Source)**")
        breakdown_data = []
        sorted_mix_keys = sorted(results["fuel_consumption_by_mix"].keys())
        for fuel_name in sorted_mix_keys:
            if results["fuel_consumption_by_mix"][fuel_name] > 1e-9: 
                breakdown_data.append({
                    "Fuel Source": fuel_name,
                    "Consumption (GJ/Year)": results["fuel_consumption_by_mix"][fuel_name],
                    "Cost (Million USD/Year)": results["fuel_cost_by_mix"][fuel_name] 
                })
        if breakdown_data:
            df_breakdown = pd.DataFrame(breakdown_data)
            st.dataframe(
                df_breakdown.style.format({
                    "Consumption (GJ/Year)": "{:,.0f}",
                    "Cost (Million USD/Year)": "{:,.3f}"
                }),
                height = 350, use_container_width=True
            )
        else: st.info("No significant fuel consumption to display.")

    with row1_col2:
        st.markdown("**Cost Contribution by Fuel Source**")
        cost_data = {k: v for k, v in results["fuel_cost_by_mix"].items() if v > 1e-9}
        if cost_data:
            df_cost_pie = pd.DataFrame(cost_data.items(), columns=['Fuel Source', 'Cost (Million USD/Year)'])
            fig_cost_pie = px.pie(df_cost_pie, values='Cost (Million USD/Year)', names='Fuel Source', hole=0.3)
            fig_cost_pie.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')
            fig_cost_pie.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig_cost_pie, use_container_width=True)
        else: st.info("No cost data to display in pie chart.")

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.markdown("**Production vs. Procurement Costs**")
        prod_proc_data = results['prod_vs_proc_cost_million']
        if sum(prod_proc_data.values()) > 1e-9 :
            df_prod_proc = pd.DataFrame(prod_proc_data.items(), columns=['Source Type', 'Total Cost (Million USD)'])
            fig_prod_proc = px.bar(df_prod_proc, x='Source Type', y='Total Cost (Million USD)', 
                                   text_auto='.3s', labels={'Total Cost (Million USD)': 'Million USD/Year'})
            fig_prod_proc.update_layout(xaxis_title=None, height=350, margin=dict(b=50))
            fig_prod_proc.update_traces(textposition='outside')
            st.plotly_chart(fig_prod_proc, use_container_width=True)
        else: st.info("Costs are effectively zero.")
            
    with row2_col2:
        st.markdown("**Consumption by Vessel Type**")
        if results["fleet_consumption_by_type"] and any(abs(v) > 1e-9 for v in results["fleet_consumption_by_type"].values()):
            df_type = pd.DataFrame(results["fleet_consumption_by_type"].items(), columns=['Vessel Type', 'Consumption (GJ/Year)'])
            df_type_plot = df_type[abs(df_type['Consumption (GJ/Year)']) > 1e-9]
            if not df_type_plot.empty:
                fig_type = px.bar(df_type_plot, x='Vessel Type', y='Consumption (GJ/Year)',
                                  text_auto='.3s', labels={'Consumption (GJ/Year)': 'GJ / Year'})
                fig_type.update_layout(xaxis_tickangle=-45, height=350, margin=dict(b=50))
                fig_type.update_traces(textposition='outside')
                st.plotly_chart(fig_type, use_container_width=True)
            else: st.info("Consumptions for all vessel types are effectively zero.")
        else: st.info("No vessel consumption data to display.")
    
    st.divider()
    st.markdown("**Total Demand by Base Fuel Type (Aggregated)**")
    base_fuel_demand_data = results.get("base_fuel_demand_gj", {})
    plot_base_fuel_demand = {
        fuel: demand for fuel, demand in base_fuel_demand_data.items() if abs(demand) > 1e-9
    }
    if plot_base_fuel_demand:
        df_base_demand = pd.DataFrame(plot_base_fuel_demand.items(), columns=['Base Fuel Type', 'Total Demand (GJ/Year)'])
        df_base_demand = df_base_demand.sort_values(by='Total Demand (GJ/Year)', ascending=False) 
        
        fig_base_demand = px.bar(
            df_base_demand, x='Base Fuel Type', y='Total Demand (GJ/Year)',
            color='Base Fuel Type', 
            text_auto='.4s', 
            labels={'Total Demand (GJ/Year)': 'Total Demand (GJ/Year)'}
        )
        fig_base_demand.update_layout(
            xaxis_tickangle=-45, 
            height=450, 
            margin=dict(b=120), 
            showlegend=False 
        )
        fig_base_demand.update_traces(textposition='outside')
        st.plotly_chart(fig_base_demand, use_container_width=True)
    else: st.info("No significant base fuel demand to display.")

else:
    if not st.session_state.show_results:
        st.info("Click 'Run Calculation' after entering parameters to see the results.")

st.divider()

# --- Static Charts Section ---
st.header("🌍 Regulatory & Market Outlook & Projections")

# --- GFI Compliance Zones Chart ---
st.subheader("GFI Compliance Zones")

@st.cache_data
def create_gfi_compliance_chart(calculated_gfi=None, calculation_year=None):
    gfi_data_string = """
Year	GFI Base	GFI DC	GFI_Credit
2028	89.568	77.439	19
2029	87.702	75.573	19
2030	85.836	73.707	19
2031	81.7308	69.6018	19
2032	77.6256	65.4966	19
2033	73.5204	61.3914	19
2034	69.4152	57.2862	19
2035	65.31	53.181	19
2036	58.779	46.65	19
2037	52.248	40.119	19
2038	45.717	32.655	19
2039	39.186	27.057	19
2040	32.655	20.526	14
2041	31.0689	18.9399	14
2042	29.4828	17.3538	14
2043	27.8967	15.7677	14
2044	26.3106	14.1816	3
2045	24.7245	12.5955	3
2046	23.1384	11.0094	3
2047	21.5523	9.4233	3
2048	19.9662	7.8372	3
2049	18.3801	6.2511	3
2050	16.794	4.665	3
"""
    df_gfi = pd.read_csv(StringIO(gfi_data_string), sep='\t')
    
    max_gfi_plot = 95
    min_gfi_plot = 0

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.fill_between(df_gfi['Year'], df_gfi['GFI Base'], max_gfi_plot,
                    color='red', alpha=0.3, label='Zone 1: Above GFI Base')
    ax.fill_between(df_gfi['Year'], df_gfi['GFI DC'], df_gfi['GFI Base'],
                    color='orange', alpha=0.4, label='Zone 2: Penalty Zone')
    ax.fill_between(df_gfi['Year'], df_gfi['GFI_Credit'], df_gfi['GFI DC'],
                    color='lightgreen', alpha=0.5, label='Zone 3: Compliant')
    ax.fill_between(df_gfi['Year'], min_gfi_plot, df_gfi['GFI_Credit'],
                    color='darkgreen', alpha=0.6, label='Zone 4: Credit Earning')

    ax.plot(df_gfi['Year'], df_gfi['GFI Base'], color='maroon', linestyle='--', linewidth=1.5, label='GFI Base Line')
    ax.plot(df_gfi['Year'], df_gfi['GFI DC'], color='darkorange', linestyle='--', linewidth=1.5, label='GFI DC Line')
    ax.plot(df_gfi['Year'], df_gfi['GFI_Credit'], color='green', linestyle='-', linewidth=2, label='GFI Credit Threshold')

    if calculated_gfi is not None and calculation_year is not None:
        if calculation_year >= 2028 and calculation_year <= 2050: 
            ax.plot(calculation_year, calculated_gfi, 
                    marker='*', markersize=15, color='blue', markeredgecolor='black',
                    label=f'Fleet Optimal GFI ({calculation_year}): {calculated_gfi:.1f}', zorder=10)
            ax.text(calculation_year + 0.5, calculated_gfi, f'{calculated_gfi:.1f}',
                    color='blue', fontsize=9, va='center', ha='left', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec='none'), zorder=11)

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("GFI Value", fontsize=11)
    ax.set_ylim(min_gfi_plot, max_gfi_plot)
    ax.set_xticks(df_gfi['Year'])
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
    ax.tick_params(axis='y', labelsize=9)
    ax.legend(loc='upper right', fontsize='x-small')
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    return fig

fleet_gfi_to_plot = st.session_state.get('calculated_fleet_gfi', None)
gfi_year_to_plot = st.session_state.get('gfi_calculation_year', None)
st.pyplot(create_gfi_compliance_chart(calculated_gfi=fleet_gfi_to_plot, calculation_year=gfi_year_to_plot))

st.divider()

# --- Fuel Price Projections Chart ---
st.subheader("Fuel Price Projections")
@st.cache_data
def create_fuel_price_chart():
    price_data_string = """
Fuel_Name	2025	2030	2035	2040	2045	2050
e-Ammonia	61.24785352	47.46029478	44.50672156	39.89256831	34.24853689	28.79520256
Biomethane	26.09708531	24.66623704	23.25329011	21.82979358	20.40872087	18.98996952
e-Methane 	72.65646649	64.82100948	59.77084571	53.26427583	45.65829988	38.44055425
Biomethanol	39.28383688	33.44040827	30.98830586	28.54051064	27.1786527	25.75435972
e-Methanol 	87.29803612	75.11334677	68.42818853	60.45467972	51.23354354	42.44528817
Biodiesel (B100)	NaN	25.4349855	25.17495816	24.86919054	24.58323743	24.1643283
e-Diesel 	99.27436485	85.01988267	78.03429746	69.55377919	57.97261473	47.23591239
Biodiesel (B50)	28.6564134	16.93428919	14.90773905	13.10412863	11.31781226	9.516140579
Biodiesel (B30)	18.9070653	14.7569101	12.58258398	10.4782824	8.392108316	6.287927955
Blue hydrogen	46.67661337	45.32488929	45.34955508	44.48399521	43.69016386	42.95888073
VLSFO	14.1	11.51	10.985	10.46	9.59	8.72
"""
    df_prices = pd.read_csv(StringIO(price_data_string), sep='\t', na_values=['NaN'])
    df_prices = df_prices.set_index('Fuel_Name')
    df_prices_transposed = df_prices.T
    df_prices_transposed.index = df_prices_transposed.index.astype(int)

    fig, ax = plt.subplots(figsize=(15, 8))
    for fuel_name in df_prices_transposed.columns:
        ax.plot(df_prices_transposed.index, df_prices_transposed[fuel_name],
                label=fuel_name, marker='o', linestyle='-', markersize=4)

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Price (USD/GJ)", fontsize=11)
    ax.set_xticks(df_prices_transposed.index)
    ax.tick_params(axis='x', rotation=0, labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))
    ax.tick_params(axis='y', labelsize=9)
    ax.legend(title="Fuel Types", loc='center left', bbox_to_anchor=(1.01, 0.5),
              fontsize='small', title_fontsize='medium')
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout(rect=[0, 0, 0.83, 1])
    return fig

st.pyplot(create_fuel_price_chart())
st.divider()

# --- Petrobras Major Export Products Projection Chart ---
st.subheader("Petrobras Major Export Products Projection")
@st.cache_data
def parse_export_data(data_string):
    lines = data_string.strip().split('\n')
    data_dict = {}
    current_category = None
    header = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        first_token = line.split('\t')[0].strip()
        
        if first_token == "Crude Oil" or first_token == "Oil Production":
             current_category = first_token
             continue 

        if re.match(r'^\d{4}', first_token): 
            header = [int(x) for x in line.split('\t')]
            continue
        
        if current_category and header:
            parts = line.split('\t')
            sub_category = parts[0].strip() 
            
            if not sub_category: 
                continue

            full_key = f"{current_category} - {sub_category}"
            
            values_str = parts[1:]
            try:
                values = [float(x) for x in values_str[:len(header)]]
                if len(values) == len(header):
                    data_dict[full_key] = dict(zip(header, values))
            except ValueError:
                pass 

    df = pd.DataFrame.from_dict(data_dict, orient='index')
    if df.empty:
        return df 
    return df.T

@st.cache_data
def create_export_projection_chart():
    export_data_string = """
	2025	2026	2027	2028	2029	2030	2031	2032	2033	2034	2035	2036	2037	2038	2039	2040	2041	2042	2043	2044	2045	2046	2047	2048	2049	2050
Crude Oil	
China	302.8911629	299.9015242	296.3035403	294.3102495	291.4302563	289.3692783	285.0007371	279.866639	274.6025704	269.2215079	264.2269436	257.3390506	249.9610299	242.5843525	234.2980337	225.5134432	220.4381078	215.7067959	211.0482387	206.2797271	201.9024627	197.4833218	193.213456	188.6563321	184.0054428	179.3571835
Europe	232.7906071	228.5011808	224.3783649	218.7718734	214.3074763	209.1999343	201.8416603	195.081824	188.5206788	182.3143133	176.0957568	168.9434908	162.4736253	155.6013989	149.5868885	143.8173272	140.7386884	137.3870809	134.164648	131.2167078	128.2597908	125.424756	122.6789039	119.8946582	117.2000431	114.5204089
USA 	48.09032613	47.59748877	46.92680692	46.37526612	45.77259329	45.17726274	44.09454012	43.15882524	42.10479055	41.02969272	39.97394621	38.6590697	37.19610461	35.92712755	34.66058342	33.49554286	32.96234597	32.34136165	31.70706964	31.05859781	30.43444222	29.89692952	29.4655663	29.07789836	28.72673933	28.37935688
SE Asia	90.10555164	91.00629743	92.52662249	93.80678911	94.88269568	95.77538969	95.85122452	95.94717078	96.09271636	96.02153922	95.55670356	93.45017602	91.29946432	89.35578213	87.46159257	85.71922184	85.26586357	84.82923793	84.20399074	83.42838502	82.24619255	81.84292359	81.09504736	80.62912761	80.13083362	79.61115212
	2025	2026	2027	2028	2029	2030	2031	2032	2033	2034	2035	2036	2037	2038	2039	2040	2041	2042	2043	2044	2045	2046	2047	2048	2049	2050
Oil Production	
Singapore (Oil Products)	110.4938074	112.771658	115.6106916	118.2102429	120.7781692	123.262747	124.9831055	126.5702625	128.3594557	130.0924646	131.6231022	131.4157635	131.4129089	131.2909177	131.2228979	131.1237478	130.7104447	130.4419177	130.0895922	129.6785904	129.0022658	128.5436541	127.7219922	126.99379	126.1892856	125.3665779
USA (Oil Products)	92.96593208	92.98058556	92.43405609	92.12700882	91.85158665	91.65951293	90.6396418	89.75297222	88.66426634	87.63174488	86.80159461	85.70347955	84.4008804	83.2174179	81.97998395	80.77368038	79.65864736	78.39883828	77.22282777	76.10549345	75.25348202	74.02455598	73.15868009	72.19934452	71.31631119	70.45148122
"""
    df_exports = parse_export_data(export_data_string)

    if df_exports.empty:
        fig, ax = plt.subplots(figsize=(15,8)) 
        ax.text(0.5, 0.5, "Data parsing for Petrobras Exports failed.\nPlease check data format.", ha='center', va='center', fontsize=12, color='red')
        return fig

    fig, ax = plt.subplots(figsize=(15, 8))
    highlight_years = [2030, 2040, 2050]

    for product_region in df_exports.columns:
        line, = ax.plot(df_exports.index, df_exports[product_region],
                        label=product_region, marker='.', linestyle='-', markersize=5)
        
        for year in highlight_years:
            if year in df_exports.index:
                value = df_exports.loc[year, product_region]
                ax.plot(year, value, marker='o', markersize=8, color=line.get_color(), markeredgecolor='black', zorder=5)
                ax.text(year, value + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.015, 
                        f'{value:.1f}', ha='center', va='bottom', fontsize=7, color=line.get_color(),
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', alpha=0.6, ec='none'), zorder=6)

    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Volume (Million Barrels per Year)", fontsize=11)
    ax.set_xticks(df_exports.index[::2]) 
    ax.tick_params(axis='x', rotation=45, labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
    ax.tick_params(axis='y', labelsize=9)
    
    ax.legend(title="Product - Destination", loc='center left', bbox_to_anchor=(1.01, 0.5),
              fontsize='small', title_fontsize='medium')
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout(rect=[0, 0, 0.80, 1]) 
    return fig

st.pyplot(create_export_projection_chart())

# --- Footer ---
st.divider()
st.markdown(f"<p style='text-align: center; color: grey;'>App Version 1.6 | Last Updated: {datetime.date.today().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)
current_year = datetime.datetime.now().year
st.caption(f"© {current_year} by Dr. Chenxi Ji, ABS EAL Lead")
st.caption("Disclaimer: Calculations based on user inputs and predefined factors.")
