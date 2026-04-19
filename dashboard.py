import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st

# --- CONFIG ---
st.set_page_config(page_title="Quality Control Dashboard", layout="wide", page_icon="")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FC; }
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 600; color: #1A1A2E; }
    [data-testid="stMetricLabel"] { font-size: 13px; color: #6B7280; font-weight: 500; }
    [data-testid="stSidebar"] { background-color: #1A1A2E; }
    [data-testid="stSidebar"] * { color: white !important; }
    hr { border-color: #E8ECF0; }
    </style>
""", unsafe_allow_html=True)

# --- LOAD ---
@st.cache_data
def load_data():
    df = pd.read_csv("quality_control_data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("Filtres")

selected_lines = st.sidebar.multiselect(
    "Ligne de Production", options=sorted(df["Production Line"].unique()), default=[]
)
selected_products = st.sidebar.multiselect(
    "Produit", options=sorted(df["Product"].unique()), default=[]
)
selected_shifts = st.sidebar.multiselect(
    "Shift", options=["Matin", "Après-midi", "Nuit"], default=[]
)
selected_defects = st.sidebar.multiselect(
    "Type de Défaut", options=sorted(df["Defect Type"].unique()), default=[]
)

date_min = df["Date"].min().date()
date_max = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Période", value=(date_min, date_max),
    min_value=date_min, max_value=date_max
)

if st.sidebar.button("🔄 Reset"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(df):,} défauts au total")

# --- FILTRES ---
filtered = df.copy()
if selected_lines:
    filtered = filtered[filtered["Production Line"].isin(selected_lines)]
if selected_products:
    filtered = filtered[filtered["Product"].isin(selected_products)]
if selected_shifts:
    filtered = filtered[filtered["Shift"].isin(selected_shifts)]
if selected_defects:
    filtered = filtered[filtered["Defect Type"].isin(selected_defects)]
if len(date_range) == 2:
    filtered = filtered[
        (filtered["Date"].dt.date >= date_range[0]) &
        (filtered["Date"].dt.date <= date_range[1])
    ]

if len(filtered) == 0:
    st.warning("⚠️ Aucun résultat pour ces filtres.")
    st.stop()

# --- CALCUL DPMO ---
total_defects       = len(filtered)
total_units         = filtered.drop_duplicates(subset=["Date","Production Line","Shift"])["Units Produced"].sum()
opportunities       = 6  # 6 types de défauts possibles
dpmo                = (total_defects / (total_units * opportunities)) * 1_000_000
sigma_level         = 0.8406 + np.sqrt(29.37 - 2.221 * np.log(dpmo)) if dpmo > 0 else 6

# --- HEADER ---
st.title("🔬 Quality Control Dashboard")
st.caption(f"Période : {filtered['Date'].min().date()} → {filtered['Date'].max().date()} · {len(filtered):,} défauts analysés")

# --- KPI CARDS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Défauts",     f"{total_defects:,}")
col2.metric("Unités Produites",  f"{total_units:,}")
col3.metric("DPMO",              f"{dpmo:,.0f}")
col4.metric("Niveau Sigma",       f"{sigma_level:.2f}")

st.markdown("---")

# --- ROW 1: Pareto + Défauts par ligne ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Diagramme de Pareto — Types de Défauts")
    pareto = filtered["Defect Type"].value_counts().reset_index()
    pareto.columns = ["Defect Type", "Count"]
    pareto["Cumulative %"] = pareto["Count"].cumsum() / pareto["Count"].sum() * 100

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()
    ax1.bar(pareto["Defect Type"], pareto["Count"], color="#378ADD", alpha=0.8)
    ax2.plot(pareto["Defect Type"], pareto["Cumulative %"],
             color="#E24B4A", marker="o", linewidth=2)
    ax2.axhline(y=80, color="gray", linestyle="--", alpha=0.5, label="80%")
    ax1.set_ylabel("Nombre de défauts")
    ax2.set_ylabel("Cumul (%)")
    ax2.set_ylim(0, 110)
    plt.xticks(rotation=30, ha="right", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)

with col_b:
    st.subheader("Défauts par Ligne de Production")
    line_defects = filtered["Production Line"].value_counts().reset_index()
    line_defects.columns = ["Ligne", "Défauts"]
    colors = ["#E24B4A" if l == "Ligne C" else "#378ADD" for l in line_defects["Ligne"]]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(line_defects["Ligne"], line_defects["Défauts"], color=colors)
    for bar, val in zip(bars, line_defects["Défauts"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                f"{val:,}", ha="center", fontsize=9)
    ax.set_ylabel("Nombre de défauts")
    ax.grid(axis="y", alpha=0.3)
    red_patch  = mpatches.Patch(color="#E24B4A", label="Ligne critique")
    blue_patch = mpatches.Patch(color="#378ADD", label="Ligne normale")
    ax.legend(handles=[red_patch, blue_patch], fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)

st.markdown("---")

# --- ROW 2: Tendance mensuelle + Défauts par shift ---
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Tendance Mensuelle des Défauts")
    monthly = filtered.groupby("Month").size().reset_index(name="Défauts")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(monthly["Month"], monthly["Défauts"],
            color="#378ADD", linewidth=2, marker="o", markersize=4)
    ax.fill_between(monthly["Month"], monthly["Défauts"],
                    alpha=0.1, color="#378ADD")
    ax.set_xticks(monthly["Month"][::2])
    ax.set_xticklabels(monthly["Month"][::2], rotation=45, fontsize=8)
    ax.set_ylabel("Nombre de défauts")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)

with col_d:
    st.subheader("Défauts par Shift")
    shift_data = filtered["Shift"].value_counts().reset_index()
    shift_data.columns = ["Shift", "Défauts"]
    shift_colors = {"Matin": "#1D9E75", "Après-midi": "#378ADD", "Nuit": "#E24B4A"}
    colors = [shift_colors[s] for s in shift_data["Shift"]]

    fig, ax = plt.subplots(figsize=(8, 4))
    wedges, texts, autotexts = ax.pie(
        shift_data["Défauts"],
        labels=shift_data["Shift"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=90
    )
    for text in autotexts:
        text.set_fontsize(10)
    fig.tight_layout()
    st.pyplot(fig)

st.markdown("---")

# --- ROW 3: Top machines + Défauts par produit ---
col_e, col_f = st.columns(2)

with col_e:
    st.subheader("Top 10 Machines les Plus Défectueuses")
    machine_defects = (
        filtered.groupby(["Production Line", "Machine"])
        .size().reset_index(name="Défauts")
        .sort_values("Défauts", ascending=False)
        .head(10)
    )
    machine_defects["Label"] = machine_defects["Machine"] + " (" + machine_defects["Production Line"] + ")"
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(machine_defects["Label"], machine_defects["Défauts"], color="#7F77DD")
    ax.invert_yaxis()
    ax.set_xlabel("Nombre de défauts")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)

with col_f:
    st.subheader("Défauts par Produit")
    product_defects = filtered["Product"].value_counts().reset_index()
    product_defects.columns = ["Produit", "Défauts"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(product_defects["Produit"], product_defects["Défauts"], color="#1D9E75")
    ax.invert_yaxis()
    ax.set_xlabel("Nombre de défauts")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig)

st.markdown("---")
st.caption("Built by Yahya Abouredouane · Quality Control Analysis — Portfolio Project")