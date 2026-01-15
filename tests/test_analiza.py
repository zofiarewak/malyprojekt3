#importy modułów ktore chce testowac:
import sys
import numpy as np
import os
import pytest
sys.path.append(os.path.join(os.getcwd(), "..", "src"))
from analiza import *
@pytest.fixture
def przykladowy_df():
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    data = {
        ("Miejscowość", "Warszawa"): [10, 20, np.nan, 40, 50, 60],
        ("Miejscowość", "Krakow"): [5, 15, 25, np.nan, 45, 55]
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_srednie_miesieczne(przykladowy_df):
    wynik = srednie_miesieczne(przykladowy_df)
    assert isinstance(wynik, pd.DataFrame)
    assert wynik.index.names == ['Rok','Miesiąc']
    # Sprawdzamy czy wartości liczbowe się zgadzają
    assert np.isclose(wynik.iloc[0,0], np.nanmean([10,20,np.nan,40,50,60]))

def test_srednie_dla_miast(przykladowy_df):
    miesieczne = srednie_miesieczne(przykladowy_df)
    sr_warszawa = srednie_dla_miast(miesieczne, "Warszawa")
    assert isinstance(sr_warszawa, pd.Series)
    # Sprawdzenie wartości
    assert np.isclose(sr_warszawa.iloc[0], np.nanmean([10,20,np.nan,40,50,60]))

def test_srednie_po_stacjach(przykladowy_df):
    miesieczne = srednie_miesieczne(przykladowy_df)
    wynik = srednie_po_stacjach(miesieczne)
    assert "Warszawa" in wynik.columns.get_level_values(0)
    assert "Krakow" in wynik.columns.get_level_values(0)

def test_dni_przekroczenia_normy(przykladowy_df):
    norma = 30
    wyn = dni_przekroczenia_normy(przykladowy_df, norma_dobowa=norma, years=[2024])
    assert wyn.loc[2024, ("Miejscowość", "Warszawa")] == 3  # dni > 30: 40,50,60
    assert wyn.loc[2024, ("Miejscowość", "Krakow")] == 2    # dni > 30: 45,55

def test_wybierz_stacje_max_min(przykladowy_df):
    norma = 30
    dni_wiecej = dni_przekroczenia_normy(przykladowy_df, norma_dobowa=norma, years=[2024])
    stacje, wybrane = wybierz_stacje_max_min(dni_wiecej, 2024, ile_maxmin=1)
    assert len(stacje) == 2  # 1 max + 1 min
    assert set(stacje) == set(wybrane.columns)
