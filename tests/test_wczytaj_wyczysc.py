import pandas as pd
import sys
import os
import pytest
sys.path.append(os.path.join(os.getcwd(), "..", "src"))
from wczytaj_wyczysc import *

# Tworzę testowy plik z metadanymi
@pytest.fixture
def metadata_df():
    return pd.DataFrame({
        "Nr": [1, 2, 3],
        "Kod stacji": ["StationA", "StationB", "StationC"],
        "Kod międzynarodowy": ["INT_A", "", ""],
        "Nazwa stacji": ["Alpha City", "Beta Town", "Gamma Village"],
        "Stary Kod stacji \n(o ile inny od aktualnego)": [
            "OldStationA",
            "",
            "OldStationC",
        ],
        "Miejscowość": ["Alpha", "Beta", "Gamma"],
    })

# Testowy DF
@pytest.fixture
def raw_gios_df_1():
    return pd.DataFrame({
        0: [
            "Nr",
            "Kod stacji",
            "Wskaźnik",
            "Czas uśredniania",
            "Jednostka",
            "Kod stanowiska",
            "2020-01-01 00:00:00",
            "2020-01-01 01:00:00",
        ],
        1: [
            "1",
            "OldStationA",
            "PM2.5",
            "1g",
            "ug/m3",
            "XXX",
            10.0,
            11.0,
        ],
        2: [
            "2",
            "StationB",
            "PM2.5",
            "1g",
            "ug/m3",
            "YYY",
            20.0,
            21.0,
        ],
    })

# Testowy DF
@pytest.fixture
def raw_gios_df_2():
    return pd.DataFrame({
        0: [
            "Nr",
            "Kod stacji",
            "Wskaźnik",
            "Czas uśredniania",
            "Jednostka",
            "Kod stanowiska",
            "2021-01-01 00:00:00",
            "2021-01-01 01:00:00",
        ],
        1: [
            "1",
            "StationA",
            "PM2.5",
            "1g",
            "ug/m3",
            "ZZZ",
            30.0,
            31.0,
        ],
        2: [
            "2",
            "OldStationC",
            "PM2.5",
            "1g",
            "ug/m3",
            "WWW",
            40.0,
            41.0,
        ],
    })

def test_zaktualizuj_nazwy_stacji(metadata_df):
    df = pd.DataFrame(
        {"OldStationA": [1, 2], "StationB": [3, 4]},
        index=["a", "b"]
    )

    df2 = zaktualizuj_nazwy_stacji(df, metadata_df)

    assert "StationA" in df2.columns
    assert "OldStationA" not in df2.columns
    assert "StationB" in df2.columns

def test_ujednolic_dane_columns(raw_gios_df_1, metadata_df):
    df = ujednolic_dane(raw_gios_df_1, metadata_df)

    assert set(df.columns) == {"StationA", "StationB"}

def test_ujednolic_dane_index_is_datetime(raw_gios_df_1, metadata_df):
    df = ujednolic_dane(raw_gios_df_1, metadata_df)

    assert isinstance(df.index, pd.Index)
    assert pd.to_datetime(df.index, errors="coerce").notna().all()

def test_wspolne_stacje(raw_gios_df_1, raw_gios_df_2, metadata_df):
    df1 = ujednolic_dane(raw_gios_df_1, metadata_df)
    df2 = ujednolic_dane(raw_gios_df_2, metadata_df)

    wsp = wspolne_stacje([df1, df2])

    assert wsp.equals(pd.Index(["StationA"]))

def test_przesun_date_midnight():
    idx = pd.to_datetime([
        "2020-01-02 00:00:00",
        "2020-01-02 01:00:00",
    ])

    df = pd.DataFrame({"StationA": [1, 2]}, index=idx)

    df2 = przesun_date(df)

    assert df2.index[0].date() == pd.Timestamp("2020-01-01").date()

def test_przesun_date_order_preserved():
    idx = pd.to_datetime([
        "2020-01-02 00:00:00",
        "2020-01-02 01:00:00",
    ])

    df = pd.DataFrame({"StationA": [1, 2]}, index=idx)
    df2 = przesun_date(df)

    assert df2.index.is_monotonic_increasing

def test_df_gotowy_pipeline(raw_gios_df_1, raw_gios_df_2, metadata_df):
    """
    Test integracyjny całego pipeline'u
    """

    raw_data = {}
    raw_data[2020] = ujednolic_dane(raw_gios_df_1, metadata_df)
    raw_data[2021] = ujednolic_dane(raw_gios_df_2, metadata_df)

    data = df_gotowy(list(raw_data.values()), metadata_df)

    # --- ASERCJE ---

    # wynik to DataFrame
    assert isinstance(data, pd.DataFrame)

    # df nie jest pusty
    assert not data.empty

    # indeks ma typ daty i czasu
    assert isinstance(data.index, pd.DatetimeIndex)

    # kolumny mają MultiIndex (Kod stacji, Miejscowość)
    assert isinstance(data.columns, pd.MultiIndex)
    assert data.columns.nlevels == 2

    # tylko wspólne stacje
    assert set(data.columns.get_level_values(0)) == {"StationA"}

    # indeks jest posortowany rosnąco
    assert data.index.notna().all()
    assert data.index.is_monotonic_increasing


