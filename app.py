"""
SACCO Scout — Compare Kenya's deposit-taking SACCOs side by side.

Data: SASRA Annual Supervision Report 2023 (public domain).
Covers 20 of Kenya's 175+ SASRA-licensed deposit-taking SACCOs.
All financial figures are from published SASRA reports, not estimated.

Tools:
  1. SACCO Finder    — filter by county, sector, entry cost
  2. Side-by-side    — compare up to 3 SACCOs on key ratios
  3. Health Monitor  — NPFL ratio, capital adequacy, dividend trend
  4. Eligibility     — check whether you can join based on employer/sector

TRUST RULE:
  - All figures from SASRA Annual Supervision Report 2023.
  - Dividend figures are historical — past dividends do not guarantee future returns.
  - Loan rates are indicative; always confirm with the SACCO directly.
  - NPFL (Non-Performing Facilities to Loans) and capital adequacy are
    regulatory ratios. SASRA benchmarks: NPFL ≤ 5%, capital adequacy ≥ 8%.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import urllib.request, json
from pathlib import Path

st.set_page_config(
    page_title="Chagua — SACCO Finder Kenya",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Mobile CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}

.ss-header{
  background:linear-gradient(135deg,#023e8a 0%,#0077b6 60%,#00b4d8 100%);
  color:white;padding:1.6rem 2rem;border-radius:10px;margin-bottom:1.2rem;
}
.ss-header h1{font-family:'IBM Plex Mono',monospace;font-size:1.8rem;margin:0 0 .2rem;letter-spacing:-1px;}
.ss-header p{font-size:.9rem;opacity:.8;margin:0;}

.sacco-card{background:#f8f9fa;border-radius:8px;padding:1rem 1.2rem;border-left:4px solid #0077b6;margin-bottom:.6rem;}
.sacco-card h4{margin:0 0 .4rem;color:#023e8a;}
.sacco-card .meta{font-size:.78rem;color:#6c757d;}

.health-good{color:#2d6a4f;font-weight:600;}
.health-warn{color:#856404;font-weight:600;}
.health-bad {color:#721c24;font-weight:600;}

.ratio-badge-good{background:#d4edda;color:#155724;padding:2px 8px;border-radius:20px;font-size:.78rem;}
.ratio-badge-warn{background:#fff3cd;color:#856404;padding:2px 8px;border-radius:20px;font-size:.78rem;}
.ratio-badge-bad {background:#f8d7da;color:#721c24;padding:2px 8px;border-radius:20px;font-size:.78rem;}

.disclaimer{font-size:.78rem;color:#6c757d;font-style:italic;margin-top:.5rem;}

@media(max-width:768px){
  [data-testid="column"]{width:100%!important;flex:1 1 100%!important;min-width:100%!important;}
  [data-testid="stMetricValue"]{font-size:1.3rem!important;}
  [data-testid="stDataFrame"]{overflow-x:auto!important;}
  .stButton>button{width:100%!important;min-height:48px!important;}
  .ss-header h1{font-size:1.3rem!important;}
}
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
DATA = Path(__file__).parent / "data" / "saccos" / "saccos_seed.csv"


@st.cache_data(ttl=3600)
def fetch_kes_rate():
    """Live USD/KES mid-market rate from open.er-api.com."""
    try:
        with urllib.request.urlopen(
            "https://open.er-api.com/v6/latest/USD", timeout=6
        ) as r:
            d = json.loads(r.read())
        kes = d["rates"]["KES"]
        updated = d.get("time_last_update_utc", "")[:16]
        return {"rate": kes, "updated": updated, "live": True}
    except Exception:
        return {"rate": 129.0, "updated": "fallback", "live": False}


@st.cache_data(ttl=86400)
def fetch_kenya_macro_sacco():
    """World Bank Kenya macro — contextualises SACCO dividend vs inflation."""
    results = {}
    for code, label in [
        ("FP.CPI.TOTL.ZG", "Inflation (CPI %)"),
        ("NY.GDP.PCAP.CD",  "GDP per capita (USD)"),
        ("SL.UEM.TOTL.ZS",  "Unemployment (%)"),
    ]:
        try:
            url = (f"https://api.worldbank.org/v2/country/KE/indicator/{code}"
                   f"?format=json&mrv=1&per_page=1")
            with urllib.request.urlopen(url, timeout=15) as r:
                import json as _j
                d = _j.loads(r.read())
            entries = [e for e in (d[1] if len(d) > 1 else []) if e.get("value")]
            if entries:
                e = entries[0]
                results[code] = {"label": label, "value": round(e["value"], 2),
                                  "year": e.get("date", "?")}
        except Exception:
            pass
    return results

@st.cache_data
def load_saccos() -> pd.DataFrame:
    return pd.read_csv(DATA)

saccos = load_saccos()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ss-header">
  <h1>🏦 ChaguaSacco — SACCO Scout Kenya</h1>
  <p>Compare deposit-taking SACCOs — dividends, loan rates, financial health · SASRA 2023</p>
</div>
""", unsafe_allow_html=True)

_kes = fetch_kes_rate()
_rate_str = f"1 USD = {_kes['rate']:.2f} KES" if _kes["live"] else "Rate unavailable"
_rate_badge = "📡 Live" if _kes["live"] else "⚠️ Fallback"
st.caption(f"{_rate_badge} · {_rate_str} · open.er-api.com · {_kes['updated']}")

_wb_s = fetch_kenya_macro_sacco()
if _wb_s:
    _wbs_cols = st.columns(len(_wb_s) + 1)
    if _kes.get("live"):
        _wbs_cols[0].metric("USD/KES", f"{_kes['rate']:.2f}", help="open.er-api.com live")
    for i, (_code, _d) in enumerate(_wb_s.items(), 1):
        _wbs_cols[i].metric(
            _d["label"].replace(" (%)", "").replace(" (USD)", ""),
            f"{_d['value']}{'%' if '%' in _d['label'] else ''}",
            help=f"World Bank {_d['year']}"
        )
    # Real return = dividend - inflation
    _cpi_entry = _wb_s.get("FP.CPI.TOTL.ZG")
    if _cpi_entry:
        st.caption(
            f"📡 World Bank {_cpi_entry['year']} · open.er-api.com · "
            f"Tip: real return = dividend % minus inflation ({_cpi_entry['value']}%)"
        )

st.info(
    "📋 **Seed data:** 20 of 175+ SASRA-licensed deposit-taking SACCOs. "
    "Figures from **SASRA Annual Supervision Report 2023** (public document). "
    "Dividends are historical — past performance does not guarantee future returns. "
    "Confirm eligibility and current rates with each SACCO directly.",
    icon=None
)

# ── Navigation ────────────────────────────────────────────────────────────────
tab_find, tab_compare, tab_health, tab_eligibility = st.tabs([
    "🔍 Find a SACCO", "⚖️ Compare", "❤️ Health Monitor", "✅ Eligibility Check"
])

# Helper: health badge
def npfl_badge(val: float) -> str:
    if val <= 5:  return f'<span class="ratio-badge-good">NPFL {val:.1f}% ✓</span>'
    if val <= 10: return f'<span class="ratio-badge-warn">NPFL {val:.1f}% ⚠</span>'
    return f'<span class="ratio-badge-bad">NPFL {val:.1f}% ✗</span>'

def cap_badge(val: float) -> str:
    if val >= 15: return f'<span class="ratio-badge-good">CAR {val:.1f}% ✓</span>'
    if val >= 8:  return f'<span class="ratio-badge-warn">CAR {val:.1f}% ⚠</span>'
    return f'<span class="ratio-badge-bad">CAR {val:.1f}% ✗</span>'

# ═══════════════════════════════════════════════════════════
# TAB 1: FIND
# ═══════════════════════════════════════════════════════════
with tab_find:
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        county_f = st.selectbox("County", ["All"] + sorted(saccos["county"].unique()))
    with col_f2:
        sector_f = st.selectbox("Sector", ["All"] + sorted(saccos["sector"].unique()))
    with col_f3:
        max_entry = st.slider("Max entry cost (KES shares + deposit)",
                              500, 20000, 10000, step=500)

    f = saccos.copy()
    if county_f != "All": f = f[f["county"] == county_f]
    if sector_f != "All": f = f[f["sector"] == sector_f]
    f["entry_cost"] = f["min_shares_kes"] + f["min_deposit_kes"]
    f = f[f["entry_cost"] <= max_entry]

    st.caption(f"**{len(f)} SACCO{'s' if len(f)!=1 else ''}** match your criteria")

    if f.empty:
        st.info("No SACCOs match — try relaxing the filters.")
    else:
        # Sort by dividend desc
        for _, row in f.sort_values("dividend_2023_pct", ascending=False).iterrows():
            with st.expander(f"**{row['name']}** — {row['sector']} · {row['county']}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("2023 Dividend", f"{row['dividend_2023_pct']:.1f}%",
                          delta=f"{row['dividend_2023_pct']-row['dividend_2022_pct']:+.1f}% vs 2022")
                c2.metric("Loan Rate", f"{row['loan_rate_monthly_pct']:.2f}%/mo",
                          help="Monthly reducing balance rate — indicative only")
                c3.metric("Entry Cost", f"KES {int(row['entry_cost']):,}",
                          help="Minimum shares + minimum deposit")
                c4.metric("Members", f"{int(row['members']):,}")

                st.markdown(
                    f"**Assets:** KES {row['assets_kes_m']:.0f}M · "
                    f"**Deposits:** KES {row['deposits_kes_m']:.0f}M · "
                    f"**Loans:** KES {row['loans_kes_m']:.0f}M"
                )
                st.markdown(
                    npfl_badge(row["npfl_ratio_pct"]) + " &nbsp; " +
                    cap_badge(row["capital_adequacy_pct"]),
                    unsafe_allow_html=True
                )
                st.markdown(f'<p class="disclaimer">Source: {row["source"]} · {row["verified"]}</p>',
                            unsafe_allow_html=True)

    st.caption(
        "NPFL = Non-Performing Facilities to Loans. SASRA benchmark: ≤5%. "
        "CAR = Capital Adequacy Ratio. SASRA benchmark: ≥8%."
    )

# ═══════════════════════════════════════════════════════════
# TAB 2: COMPARE
# ═══════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("⚖️ Side-by-side comparison")
    all_names = saccos["name"].tolist()
    selected = st.multiselect(
        "Select 2–3 SACCOs to compare",
        options=all_names,
        default=["Mwalimu National SACCO", "Stima SACCO", "Kenya Airways SACCO"],
        max_selections=3,
    )

    if len(selected) < 2:
        st.info("Select at least 2 SACCOs to compare.")
    else:
        cmp = saccos[saccos["name"].isin(selected)].set_index("name")

        metrics = {
            "2023 Dividend %":          "dividend_2023_pct",
            "2022 Dividend %":          "dividend_2022_pct",
            "Loan rate %/mo":           "loan_rate_monthly_pct",
            "Min entry cost (KES)":     None,   # computed
            "Members":                  "members",
            "Assets (KES M)":           "assets_kes_m",
            "NPFL ratio %":             "npfl_ratio_pct",
            "Capital adequacy %":       "capital_adequacy_pct",
        }

        rows = []
        for label, col in metrics.items():
            if col is None:
                values = {n: int(cmp.loc[n, "min_shares_kes"] + cmp.loc[n, "min_deposit_kes"])
                          for n in selected}
            else:
                values = {n: cmp.loc[n, col] for n in selected}
            row = {"Metric": label}
            row.update(values)
            rows.append(row)

        compare_df = pd.DataFrame(rows).set_index("Metric")
        st.dataframe(compare_df, use_container_width=True)

        # Radar chart
        radar_metrics = [
            ("Dividend 2023", "dividend_2023_pct", False),
            ("Loan Rate (inv)", "loan_rate_monthly_pct", True),   # lower = better
            ("Capital Adequacy", "capital_adequacy_pct", False),
            ("NPFL (inv)", "npfl_ratio_pct", True),               # lower = better
            ("Members (log)", None, False),
        ]

        fig = go.Figure()
        for name in selected:
            row = cmp.loc[name]
            # Normalize each dimension to 0–10 relative to all saccos
            def norm(col, invert=False):
                mn, mx = saccos[col].min(), saccos[col].max()
                val = row[col]
                n = 10 * (val - mn) / (mx - mn + 1e-9)
                return round(10 - n if invert else n, 1)

            r_vals = [
                norm("dividend_2023_pct"),
                norm("loan_rate_monthly_pct", invert=True),
                norm("capital_adequacy_pct"),
                norm("npfl_ratio_pct", invert=True),
                norm("members"),
            ]
            theta = ["Dividend", "Low Rate", "Capital", "Loan Quality", "Scale"]
            fig.add_trace(go.Scatterpolar(
                r=r_vals + [r_vals[0]],
                theta=theta + [theta[0]],
                fill="toself", name=name,
                line_width=2,
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="Relative performance radar (0–10 normalized across seed dataset)",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Radar scores are normalized relative to the 20 SACCOs in the seed dataset, not all Kenyan SACCOs.")

# ═══════════════════════════════════════════════════════════
# TAB 3: HEALTH MONITOR
# ═══════════════════════════════════════════════════════════
with tab_health:
    st.subheader("❤️ SACCO Financial Health — SASRA Regulatory Benchmarks")
    st.markdown("""
**SASRA benchmarks for deposit-taking SACCOs:**
- **NPFL ratio** (Non-Performing Facilities to Loans): ≤ 5% = healthy · 5–10% = watch · >10% = concern
- **Capital Adequacy Ratio (CAR)**: ≥ 15% = strong · 8–14% = adequate · <8% = regulatory risk

These are from the SASRA SACCO Supervision Annual Report 2023. Figures are as of the SACCO's last audit date.
""")

    h_col1, h_col2 = st.columns(2)

    with h_col1:
        # NPFL scatter
        fig_h1 = px.scatter(
            saccos,
            x="npfl_ratio_pct", y="dividend_2023_pct",
            size="assets_kes_m",
            color="npfl_ratio_pct",
            color_continuous_scale=["#2d6a4f", "#f4a261", "#e63946"],
            range_color=[0, 12],
            hover_name="name",
            hover_data={"county": True, "sector": True},
            labels={"npfl_ratio_pct": "NPFL %", "dividend_2023_pct": "Dividend 2023 %"},
            title="Loan Quality vs Dividend — bubble = asset size",
        )
        fig_h1.add_vline(x=5, line_dash="dash", line_color="orange",
                         annotation_text="5% NPFL limit")
        fig_h1.update_layout(coloraxis_showscale=False, height=380)
        st.plotly_chart(fig_h1, use_container_width=True)

    with h_col2:
        # Capital adequacy bar
        fig_h2 = px.bar(
            saccos.sort_values("capital_adequacy_pct"),
            x="capital_adequacy_pct", y="name",
            orientation="h",
            color="capital_adequacy_pct",
            color_continuous_scale=["#e63946", "#f4a261", "#2d6a4f"],
            range_color=[8, 28],
            labels={"capital_adequacy_pct": "CAR %", "name": "SACCO"},
            title="Capital Adequacy Ratio — higher = more buffer",
        )
        fig_h2.add_vline(x=8, line_dash="dot", line_color="red",
                         annotation_text="8% min", annotation_position="top right")
        fig_h2.add_vline(x=15, line_dash="dash", line_color="green",
                         annotation_text="15% strong", annotation_position="top right")
        fig_h2.update_layout(coloraxis_showscale=False, height=380)
        st.plotly_chart(fig_h2, use_container_width=True)

    # NPFL league table
    st.subheader("Regulatory compliance table")
    health_df = saccos[["name", "sector", "npfl_ratio_pct", "capital_adequacy_pct",
                         "dividend_2023_pct"]].sort_values("npfl_ratio_pct")
    health_df = health_df.rename(columns={
        "name": "SACCO", "sector": "Sector",
        "npfl_ratio_pct": "NPFL %", "capital_adequacy_pct": "CAR %",
        "dividend_2023_pct": "Div 2023 %",
    })
    st.dataframe(health_df, use_container_width=True, hide_index=True)
    st.caption(
        "Source: SASRA Annual Supervision Report 2023 · "
        "NPFL = Non-Performing Facilities to Loans · CAR = Capital Adequacy Ratio"
    )

# ═══════════════════════════════════════════════════════════
# TAB 4: ELIGIBILITY
# ═══════════════════════════════════════════════════════════
with tab_eligibility:
    st.subheader("✅ Can I join?")
    st.markdown(
        "Most SACCOs restrict membership to people in a specific employer, sector, or region. "
        "This tool matches your profile to SACCOs you may be eligible for — "
        "always confirm with the SACCO directly before applying."
    )

    e_col1, e_col2 = st.columns(2)
    with e_col1:
        employer_sector = st.selectbox(
            "Your employment sector",
            ["Civil Service (Teachers)", "Civil Service (Police)", "Civil Service (General)",
             "Energy Sector", "Health Sector", "Aviation Sector", "Port Sector",
             "Telecoms Sector", "Transport Sector", "Agriculture Sector",
             "Education Sector", "Forestry Sector", "General Public"]
        )
        user_county = st.selectbox("Your county", sorted(saccos["county"].unique()))
    with e_col2:
        budget_kes = st.number_input(
            "Entry budget (KES — shares + deposit)",
            min_value=100, max_value=50000, value=3000, step=500
        )
        priority = st.radio(
            "What matters most to you?",
            ["Highest dividend", "Lowest loan rate", "Best financial health", "Lowest entry cost"],
        )

    # Eligibility matching logic
    eligible = saccos.copy()
    eligible["entry_cost"] = eligible["min_shares_kes"] + eligible["min_deposit_kes"]

    # Sector match: "General Public" SACCOs are open to all
    sector_eligible = eligible[
        (eligible["sector"] == employer_sector) |
        (eligible["sector"] == "General Public")
    ]

    # County: some SACCOs are national, some county-specific
    # Simple rule: national SACCOs (Nairobi-based) are accessible from anywhere
    # county SACCOs require match
    def is_accessible(row):
        if row["county"] == "Nairobi":  # national SACCOs
            return True
        return row["county"] == user_county

    sector_eligible = sector_eligible[sector_eligible.apply(is_accessible, axis=1)]
    sector_eligible = sector_eligible[sector_eligible["entry_cost"] <= budget_kes]

    # Sort by priority
    sort_map = {
        "Highest dividend":      ("dividend_2023_pct", False),
        "Lowest loan rate":      ("loan_rate_monthly_pct", True),
        "Best financial health": ("npfl_ratio_pct", True),
        "Lowest entry cost":     ("entry_cost", True),
    }
    sort_col, sort_asc = sort_map[priority]
    sector_eligible = sector_eligible.sort_values(sort_col, ascending=sort_asc)

    st.divider()
    st.markdown(f"**{len(sector_eligible)} SACCO{'s' if len(sector_eligible)!=1 else ''} match your profile**")

    if sector_eligible.empty:
        st.info(
            "No matches within your budget and sector. "
            "Consider increasing your entry budget, or look at General Public SACCOs. "
            "You can also contact your employer's HR — many sectors have employer-specific SACCOs not yet in this seed dataset."
        )
    else:
        for _, row in sector_eligible.head(5).iterrows():
            with st.expander(f"✅ **{row['name']}** — {row['sector']}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Dividend 2023", f"{row['dividend_2023_pct']:.1f}%")
                c2.metric("Entry cost", f"KES {int(row['entry_cost']):,}")
                c3.metric("Loan rate", f"{row['loan_rate_monthly_pct']:.2f}%/mo")
                st.markdown(
                    npfl_badge(row["npfl_ratio_pct"]) + " &nbsp; " +
                    cap_badge(row["capital_adequacy_pct"]),
                    unsafe_allow_html=True
                )
                st.markdown(
                    '<p class="disclaimer">'
                    "This is a match based on sector/county/budget filters only. "
                    "Confirm current eligibility criteria, loan products, and rates "
                    "directly with the SACCO before applying."
                    '</p>',
                    unsafe_allow_html=True
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "ChaguaSacco · SACCO Scout · Data: SASRA Annual Supervision Report 2023 (public domain) · "
    "CC BY-NC-ND 4.0 · contact@aikungfu.dev · "
    "Not affiliated with SASRA, nor any listed SACCO · "
    "Past dividends do not guarantee future returns"
)
