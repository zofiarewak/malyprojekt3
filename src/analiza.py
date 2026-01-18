import pandas as pd

def srednie_miesieczne(df:pd.DataFrame) -> pd.DataFrame:
    """
    Oblicza średnie miesięczne stężenia PM2.5 dla każdej stacji pomiarowej.

    Funkcja działa na gotowym DataFrame otrzymanym za pomocą funkcji df_gotowy.
    Dane są grupowane według roku i miesiąca na podstawie indeksu czasowego,
    a następnie liczona jest średnia wartość dla każdego miesiąca.

    Wynikowy DataFrame posiada:
    - dwupoziomowy indeks wierszy: (Rok, Miesiąc),
    - dwupoziomowy indeks kolumn: (Kod stacji, Miejscowość).

    Parameters
    ----------
    df : pandas.DataFrame
        Gotowy DataFrame z danymi pomiarowymi PM2.5,
        z indeksem czasowym oraz kolumnami w postaci MultiIndex
        (Kod stacji, Miejscowość).

    Returns
    -------
    pandas.DataFrame
        DataFrame zawierający średnie miesięczne wartości PM2.5
        dla każdej stacji i miejscowości.
    """
    df_pomiary = df.copy()
    df_pomiary = df_pomiary.apply(pd.to_numeric, errors="coerce")
    
    miesieczne_srednie = df_pomiary.groupby([df_pomiary.index.year, df_pomiary.index.month]).mean()
    miesieczne_srednie.index.names = ['Rok','Miesiąc']
    return miesieczne_srednie

def srednie_dla_miast(miesieczne_srednie:pd.DataFrame, miasto:str) -> pd.DataFrame:
    """
    Oblicza średnie miesięczne stężenia PM2.5 dla wybranej miejscowości.

    Funkcja przyjmuje DataFrame ze średnimi miesięcznymi (wynik funkcji
    srednie_miesieczne) i agreguje dane po wszystkich stacjach
    znajdujących się w danej miejscowości.

    Parameters
    ----------
    miesieczne_srednie : pandas.DataFrame
        DataFrame ze średnimi miesięcznymi PM2.5, z dwupoziomowym
        indeksem kolumn (Kod stacji, Miejscowość).
    miasto : str
        Nazwa miejscowości, dla której mają zostać obliczone średnie wartości.

    Returns
    -------
    pandas.DataFrame
        Jednokolumnowy DataFrame (Series w postaci DataFrame),
        w którym indeks stanowią (Rok, Miesiąc),
        a wartościami są średnie PM2.5 dla całej miejscowości.
    """
    sr_miasto = miesieczne_srednie.loc[:, miesieczne_srednie.columns.get_level_values("Miejscowość") == miasto]
    sr_miasto = sr_miasto.mean(axis=1)
    return sr_miasto 

def srednie_po_stacjach(miesieczne_srednie:pd.DataFrame) -> pd.DataFrame:
    """
    Oblicza średnie miesięczne stężenia PM2.5 zagregowane po miejscowościach.

    Funkcja przyjmuje DataFrame ze średnimi miesięcznymi (wynik funkcji
    srednie_miesieczne) i uśrednia wartości dla stacji należących
    do tej samej miejscowości.

    Parameters
    ----------
    miesieczne_srednie : pandas.DataFrame
        DataFrame ze średnimi miesięcznymi PM2.5,
        z dwupoziomowym indeksem kolumn (Kod stacji, Miejscowość).

    Returns
    -------
    pandas.DataFrame
        DataFrame, w którym kolumny odpowiadają miejscowościom,
        a wartości są średnimi PM2.5 dla danej miejscowości
        w poszczególnych miesiącach i latach.
    """
    return miesieczne_srednie.groupby(level="Miejscowość", axis=1).mean()

def dni_przekroczenia_normy(df_pomiary:pd.DataFrame, norma_dobowa:float, years:list[int]) -> pd.DataFrame:
    """
        Zlicza liczbę dni z przekroczeniem dobowej normy PM2.5 dla każdej stacji.

        Funkcja działa na gotowym DataFrame otrzymanym za pomocą funkcji df_gotowy.
        Najpierw obliczane są średnie dobowe, a następnie dla każdego roku
        zliczana jest liczba dni, w których średnia dobowa przekroczyła
        zadany próg normy.

        Parameters
        ----------
        df_pomiary : pandas.DataFrame
            Gotowy DataFrame z danymi pomiarowymi PM2.5,
            z indeksem czasowym oraz kolumnami w postaci MultiIndex
            (Kod stacji, Miejscowość).
        norma_dobowa : float
            Wartość dobowej normy PM2.5, powyżej której dzień
            uznawany jest za przekroczenie normy.
        years : list of int
            Lista lat, dla których ma zostać wykonane zliczanie przekroczeń.

        Returns
        -------
        pandas.DataFrame
            DataFrame, w którym:
            - wiersze odpowiadają latom,
            - kolumny to stacje (Kod stacji, Miejscowość),
            - wartości to liczba dni z przekroczeniem normy w danym roku.
        """
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


def wybierz_stacje_max_min(ile_dni_wiecej_normy:pd.DataFrame, rok:int, ile_maxmin=3) -> (list, pd.DataFrame):
    """
    Wybiera stacje z największą i najmniejszą liczbą dni z przekroczeniem normy.

    Funkcja działa na wyniku funkcji dni_przekroczenia_normy.

    Parameters
    ----------
    ile_dni_wiecej_normy : pandas.DataFrame
        DataFrame zwrócony przez funkcję dni_przekroczenia_normy.
    rok : int
        Rok, dla którego mają zostać wybrane stacje.
    ile_maxmin : int, optional
        Liczba stacji wybieranych z maksimum i minimum przekroczeń
        (domyślnie 3).

    Returns
    -------
    tuple
        Krotka zawierająca:
        - listę wybranych stacji (kody stacji z miejscowością),
        - DataFrame ograniczony do wybranych stacji.
    """
    max3 = ile_dni_wiecej_normy.loc[rok].sort_values(ascending=False).head(ile_maxmin)
    min3 = ile_dni_wiecej_normy.loc[rok].sort_values(ascending=False).tail(ile_maxmin)
    wybrane_stacje = max3.index.tolist() + min3.index.tolist()
    return wybrane_stacje, ile_dni_wiecej_normy[wybrane_stacje]

def overnorm_by_voivodeship(
        df: pd.DataFrame,
        metadata: pd.DataFrame,
        daily_norm: float,
        years: list[int],
        voivodeship_col: str = "Województwo"
) -> pd.DataFrame:
    """
    Counts number of days with daily mean PM2.5 value above norm,
    aggregated by voivodeship.
    Returns: DataFrame (index = years, columns = voivodeships)
    """

    df_num = df.apply(pd.to_numeric, errors="coerce")

    # dzienna średnia na stacje
    daily = df_num.resample("D").mean(numeric_only=True)
    # wartość bool dla przekroczenia średniej wartości
    exceed = daily > daily_norm

    # mapowanie każdej stacji na województwo
    station_codes = exceed.columns.get_level_values(0)
    station_to_voiv = metadata.set_index("Kod stacji")[voivodeship_col].to_dict()
    voiv = pd.Series(station_codes, index=exceed.columns).map(lambda s: station_to_voiv.get(s, "Unknown"))
    
    # dla każdego dnia i województwa sprawdza czy była choć jedna stacja z przekroczeniem
    exceed_voiv_day = exceed.groupby(voiv, axis=1).any()

    # zlicza liczbe dni z przekroczeniem w każdym roku
    out = exceed_voiv_day.groupby(exceed_voiv_day.index.year).sum()
    out = out.reindex(years, fill_value=0)
    out.index.name = "Year"
    out.columns.name = "Voivodeship"
    return out
