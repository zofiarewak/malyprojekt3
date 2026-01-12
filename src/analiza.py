import pandas as pd

def srednie_miesieczne(df_pomiary):
    miesieczne_srednie = df_pomiary.groupby([df_pomiary.index.year, df_pomiary.index.month]).mean()
    miesieczne_srednie1424 = miesieczne_srednie.loc[[2014, 2024]]
    miesieczne_srednie1424.index.names = ['Rok', 'Miesiąc']
    kat = miesieczne_srednie1424.loc[:, miesieczne_srednie1424.columns.get_level_values("Miejscowość") == "Katowice"]
    wwa = miesieczne_srednie1424.loc[:, miesieczne_srednie1424.columns.get_level_values("Miejscowość") == "Warszawa"]
    wwa_srednie = wwa.mean(axis=1)
    kat_srednie = kat.mean(axis=1)
    srednie_po_stacjach = miesieczne_srednie.groupby(level="Miejscowość", axis=1).mean()
    return miesieczne_srednie1424, wwa_srednie, kat_srednie, srednie_po_stacjach

def dzienne_max_i_przekroczenia(df_pomiary, norma_dobowa):
    dzienne_max = df_pomiary.groupby([df_pomiary.index.year, df_pomiary.index.month, df_pomiary.index.day]).max()
    dzienne_max.index.names = ["Rok", "Miesiąc", "Dzień"]
    years = df_pomiary.index.year.unique()
    ile_dni_wiecej_normy = pd.DataFrame(index=years, columns=dzienne_max.columns)
    for year in years:
        df_year = dzienne_max.loc[year]
        ile_dni_wiecej_normy.loc[year] = (df_year > norma_dobowa).sum()
    return dzienne_max, ile_dni_wiecej_normy

def top_i_bottom_stacje(ile_dni_wiecej_normy, rok, ile_maxmin=3):
    mnnn = lambda x: x.nlargest(3).index.tolist()
    max3_stacje = (ile_dni_wiecej_normy.loc[rok]).sort_values(ascending=False).head(ile_maxmin)
    min3_stacje = (ile_dni_wiecej_normy.loc[rok]).sort_values(ascending=False).tail(ile_maxmin)
    wybrane_stacje = max3_stacje.index.tolist() + min3_stacje.index.tolist()
    ile_dni_wybrane_stacje = ile_dni_wiecej_normy[wybrane_stacje]
    return wybrane_stacje, ile_dni_wybrane_stacje
