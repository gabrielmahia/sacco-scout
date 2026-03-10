"""SACCO Scout — test suite."""
from __future__ import annotations
import pandas as pd
import pytest
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "saccos"


class TestSeedData:
    def test_load(self):
        df = pd.read_csv(DATA / "saccos_seed.csv")
        assert len(df) >= 15

    def test_required_columns(self):
        df = pd.read_csv(DATA / "saccos_seed.csv")
        required = {
            "sacco_id","name","county","sector","members",
            "assets_kes_m","deposits_kes_m","loans_kes_m",
            "dividend_2022_pct","dividend_2023_pct",
            "min_shares_kes","min_deposit_kes",
            "loan_rate_monthly_pct","npfl_ratio_pct","capital_adequacy_pct",
            "source","verified",
        }
        assert required.issubset(df.columns)

    def test_all_confirmed(self):
        df = pd.read_csv(DATA / "saccos_seed.csv")
        bad = df[df["verified"] != "confirmed"]
        assert len(bad) == 0, f"Unverified: {bad['name'].tolist()}"

    def test_source_is_sasra(self):
        df = pd.read_csv(DATA / "saccos_seed.csv")
        assert df["source"].str.contains("SASRA").all()

    def test_no_duplicate_ids(self):
        df = pd.read_csv(DATA / "saccos_seed.csv")
        assert df["sacco_id"].is_unique


class TestRatios:
    def _df(self): return pd.read_csv(DATA / "saccos_seed.csv")

    def test_npfl_range(self):
        assert self._df()["npfl_ratio_pct"].between(0, 100).all()

    def test_capital_adequacy_range(self):
        assert self._df()["capital_adequacy_pct"].between(0, 100).all()

    def test_deposits_lt_assets(self):
        df = self._df()
        assert (df["deposits_kes_m"] <= df["assets_kes_m"]).all()

    def test_dividend_non_negative(self):
        assert (self._df()["dividend_2023_pct"] >= 0).all()

    def test_sasra_npfl_threshold_coverage(self):
        df = self._df()
        assert (df["npfl_ratio_pct"] <= 5).sum() >= 10

    def test_sasra_capital_threshold_coverage(self):
        df = self._df()
        assert (df["capital_adequacy_pct"] >= 8).sum() >= 10


class TestComparison:
    def _df(self): return pd.read_csv(DATA / "saccos_seed.csv")

    def test_sort_by_dividend(self):
        df = self._df().sort_values("dividend_2023_pct", ascending=False)
        assert df["dividend_2023_pct"].iloc[0] >= df["dividend_2023_pct"].iloc[-1]

    def test_entry_cost_positive(self):
        df = self._df()
        entry = df["min_shares_kes"] + df["min_deposit_kes"]
        assert (entry > 0).all()

    def test_county_filter_nairobi(self):
        assert len(self._df()[self._df()["county"] == "Nairobi"]) >= 3

    def test_sector_variety(self):
        assert self._df()["sector"].nunique() >= 4


def test_app_compiles():
    import py_compile
    py_compile.compile(str(Path(__file__).parent.parent / "app.py"), doraise=True)
