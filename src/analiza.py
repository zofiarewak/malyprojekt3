import pandas as pd
import pytest

def srednie_miesieczne(df):
    df_pomiary = df.copy()
    df_pomiary = df_pomiary.apply(pd.to_numeric, errors="coerce")
    
    miesieczne_srednie = df_pomiary.groupby([df_pomiary.index.year, df_pomiary.index.month]).mean()
    miesieczne_srednie.index.names = ['Rok','Miesiąc']
    return miesieczne_srednie

def srednie_dla_miast(miesieczne_srednie, miasto):
    sr_miasto = miesieczne_srednie.loc[:, miesieczne_srednie.columns.get_level_values("Miejscowość") == miasto]
    sr_miasto = sr_miasto.mean(axis=1)
    return sr_miasto 

def srednie_po_stacjach(miesieczne_srednie):
    return miesieczne_srednie.groupby(level="Miejscowość", axis=1).mean()

def dni_przekroczenia_normy(df_pomiary, norma_dobowa, years=[2015, 2018, 2021, 2024]):
    #wymuszam wartości liczbowe, NaN dla niepoprawnych
    df_numeric = df_pomiary.apply(pd.to_numeric, errors="coerce")
    dzienne_srednie = (
        df_numeric
        .groupby([df_numeric.index.year, df_numeric.index.month, df_numeric.index.day])
        .mean(numeric_only=True)
    )
    dzienne_srednie.index.names = ['Rok','Miesiąc','Dzień']

    # Tworzymy DataFrame wynikowy
    ile_dni = pd.DataFrame(index=years, columns=dzienne_srednie.columns)

    for year in years:
        if year in dzienne_srednie.index.get_level_values(0):
            df_year = dzienne_srednie.loc[year]
            ile_dni.loc[year] = (df_year > norma_dobowa).sum()
        else:
            ile_dni.loc[year] = 0 #jesli brak danych 
    return ile_dni


def wybierz_stacje_max_min(ile_dni_wiecej_normy, rok, ile_maxmin=3):
    max3 = ile_dni_wiecej_normy.loc[rok].sort_values(ascending=False).head(ile_maxmin)
    min3 = ile_dni_wiecej_normy.loc[rok].sort_values(ascending=False).tail(ile_maxmin)
    wybrane_stacje = max3.index.tolist() + min3.index.tolist()
    return wybrane_stacje, ile_dni_wiecej_normy[wybrane_stacje]
