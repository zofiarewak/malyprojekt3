import pandas as pd
import requests
import zipfile
import io

def download_gios_archive(gios_archive_url:str, gios_id:str, filename:str) -> pd.DataFrame:
    """
        Pobiera archiwalne dane pomiarowe PM2.5 ze strony GIOŚ i zwraca je
        w postaci surowej tabeli danych.

        Funkcja pobiera archiwum ZIP ze strony z danymi, otwiera wskazany
        plik Excel (.xlsx) znajdujący się w archiwum i wczytuje go do
        obiektu pandas.DataFrame bez interpretacji nagłówków.

        Parameters
        ----------
        gios_archive_url : str
            Adres URL strony zawierającej archiwa danych GIOŚ
            (wspólny dla różnych lat i zasobów).
        gios_id : str
            Identyfikator konkretnego linku archiwum na stronie GIOŚ.
        filename : str
            Nazwa pliku Excel znajdującego się w archiwum ZIP,
            np. "*rok*_PM25_1g.xlsx".

        Returns
        -------
        pandas.DataFrame
            Surowe dane pomiarowe wczytane bez nagłówków,
            dokładnie w takiej postaci, w jakiej występują w pliku źródłowym.
        """
    response = requests.get(f"{gios_archive_url}{gios_id}")
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open(filename) as f:
            df = pd.read_excel(f, header=None, decimal=",")
    return df

def download_metadata(gios_archive_url:str,metadata_url_id:str) -> pd.DataFrame:
    """
    Pobiera plik metadanych GIOŚ i wczytuje go do obiektu pandas.DataFrame.

    Metadane zawierają m.in. aktualne i historyczne kody stacji oraz
    przypisanie stacji do miejscowości. Dane są pobierane bezpośrednio
    z pliku Excel dostępnego online.

    Parameters
    ----------
    gios_archive_url : str
        Adres URL strony zawierającej archiwa danych GIOŚ
    metadata_url_id : str
        Identyfikator linku prowadzącego do pliku metadanych.

    Returns
    -------
    pandas.DataFrame
        Tabela z metadanymi stacji pomiarowych wczytana z pliku Excel.
        W przypadku błędu wczytywania zwracane jest None.
    """
    # Pobranie metadanych
    url = f"{gios_archive_url}{metadata_url_id}"
    response = requests.get(url)
    response.raise_for_status()  # jeśli błąd HTTP, zatrzymaj

    try:
        df = pd.read_excel(io.BytesIO(response.content),engine='openpyxl')
        return df
    except Exception as e:
        print(f"Błąd przy wczytywaniu metadanych: {e}")
        return None

def zaktualizuj_nazwy_stacji(df:pd.DataFrame, metadane:pd.DataFrame) -> pd.DataFrame:
    """
        Aktualizuje kody stacji pomiarowych w surowych danych na podstawie metadanych.

        Funkcja tworzy mapowanie starych kodów stacji na ich aktualne odpowiedniki
        na podstawie tabeli metadanych i zmienia nazwy kolumn w surowym DataFrame.
        Operacja dotyczy wyłącznie nazw kolumn.

        Parameters
        ----------
        df : pandas.DataFrame
            Surowy DataFrame z danymi pomiarowymi, gdzie kolumny reprezentują
            kody stacji.
        metadane : pandas.DataFrame
            DataFrame z metadanymi zawierający aktualne oraz historyczne
            kody stacji.

        Returns
        -------
        pandas.DataFrame
            DataFrame z uaktualnionymi kodami stacji w nazwach kolumn.
        """
    # Teraz chcę zmienić kody stacji, tak aby były aktualne na podstawie pliku metadane:
    # Tworzę słownik kodów- będzie działał na zasadzie stary kod: nowy kod.
    # W ten sposób mogę potem łatwo aktualizować kody stacji.
    slownik_kodow = {}
    for _, row in metadane.iterrows():
        stary_kod = row['Stary Kod stacji \n(o ile inny od aktualnego)']
        nowy_kod = row["Kod stacji"]
        if pd.notna(stary_kod):
            # Starych kodów może być też kilka:
            stary_kod = stary_kod.split(",")
            for s in stary_kod:
                slownik_kodow[s] = nowy_kod

    df.rename(columns=slownik_kodow, inplace=True)
    return df

def ujednolic_dane(tabela:pd.DataFrame, metadane:pd.DataFrame) -> pd.DataFrame:
    """
        Czyści i ujednolica surowe dane pomiarowe do postaci analitycznej.

        Funkcja usuwa wiersze opisowe (np. jednostki, wskaźniki),
        ustawia właściwy wiersz jako nagłówek kolumn, ustawia datę
        pomiaru jako indeks oraz aktualizuje kody stacji na podstawie metadanych.

        Parameters
        ----------
        tabela : pandas.DataFrame
            Surowy DataFrame wczytany bezpośrednio z pliku Excel.
        metadane : pandas.DataFrame
            DataFrame z metadanymi stacji, wykorzystywany do aktualizacji
            kodów stacji.

        Returns
        -------
        pandas.DataFrame
            Ujednolicony DataFrame z
        """
    tabela = tabela.copy()
    tabela = tabela[~tabela.iloc[:,0].isin(['Wskaźnik','Czas uśredniania','Jednostka', 'Kod stanowiska', 'Nr'])]
    tabela.columns = tabela.iloc[0]
    tabela = tabela.drop(tabela.index[0]).reset_index(drop=True)
    tabela = tabela.rename(columns={"Kod stacji": "Data poboru danych"})
    tabela = tabela.set_index('Data poboru danych')
    tabela = zaktualizuj_nazwy_stacji(tabela,metadane)
    return tabela 

def wspolne_stacje(df_list:list[pd.DataFrame]) -> pd.Index:
    """
        Wyznacza zbiór stacji pomiarowych wspólnych dla wszystkich DataFrame’ów.

        Funkcja znajduje część wspólną nazw kolumn (kodów stacji)
        występujących we wszystkich przekazanych DataFrame’ach.

        Parameters
        ----------
        df_list : list of pandas.DataFrame
            Lista DataFrame’ów z danymi pomiarowymi dla różnych lat.

        Returns
        -------
        pandas.Index
            Indeks zawierający kody stacji obecne we wszystkich DataFrame’ach.
        """
    wsp = df_list[0].columns
    for df in df_list[1:]:
        wsp = wsp.intersection(df.columns)
    return wsp

def multiindex_funkcja(df:pd.DataFrame, metadane:pd.DataFrame, wsp_stacje:pd.Index) -> pd.DataFrame:
    """
        Tworzy dwupoziomowy indeks kolumn na podstawie kodu stacji i miejscowości.

        Na podstawie metadanych funkcja przypisuje każdej stacji nazwę miejscowości
        i ustawia kolumny DataFrame jako MultiIndex:
        (Kod stacji, Miejscowość).

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame z danymi pomiarowymi i kolumnami reprezentującymi kody stacji.
        metadane : pandas.DataFrame
            DataFrame z metadanymi stacji, zawierający m.in. miejscowości.
        wsp_stacje : pandas.Index
            Indeks zawierający kody stacji wspólne dla wszystkich analizowanych lat.

        Returns
        -------
        pandas.DataFrame
            DataFrame z kolumnami ustawionymi jako dwupoziomowy MultiIndex.
        """
    filt = metadane[metadane['Kod stacji'].isin(wsp_stacje)]
    tuples = list(zip(filt['Kod stacji'], filt['Miejscowość']))
    df.columns = pd.MultiIndex.from_tuples(tuples, names=("Kod stacji", "Miejscowość"))
    return df

def przesun_date(df:pd.DataFrame) -> pd.DataFrame:
    """
      Przesuwa datę pomiaru o jeden dzień wstecz dla pomiarów wykonanych o północy.

      Pomiar wykonany dokładnie o godzinie 00:00 jest interpretowany jako
      należący do dnia poprzedniego poprzez przesunięcie znacznika czasu
      o jedną sekundę wstecz.

      Parameters
      ----------
      df : pandas.DataFrame
          DataFrame z indeksem czasowym reprezentującym moment pomiaru.

      Returns
      -------
      pandas.DataFrame
          DataFrame z poprawionym indeksem czasowym.
      """
    df = df.copy()
    df.index = pd.to_datetime(df.index, errors="coerce",format="%Y-%m-%d %H:%M:%S")
    polnoc = df.index.hour == 0
    nowy_indeks = [t - pd.Timedelta(seconds=1) if h else t for t, h in zip(df.index, polnoc)]
    df.index = pd.DatetimeIndex(nowy_indeks)
    return df

def df_gotowy(raw_df_dict:dict[int:pd.DataFrame], metadane:pd.DataFrame) -> pd.DataFrame:
    """
    Tworzy końcowy DataFrame z danymi PM2.5 połączonymi dla wielu lat.

    Funkcja ujednolica surowe dane dla każdego roku, wybiera wspólne stacje,
    dodaje drugi poziom indeksu kolumn (miejscowość), koryguje daty pomiarów
    i łączy wszystkie lata w jeden spójny DataFrame.

    Parameters
    ----------
    raw_df_dict : dict[int, pandas.DataFrame]
        Słownik surowych danych w postaci {rok: DataFrame}.
    metadane : pandas.DataFrame
        DataFrame z metadanymi stacji pomiarowych.

    Returns
    -------
    pandas.DataFrame
        Gotowy DataFrame zawierający połączone dane ze wszystkich lat,
        z ujednoliconą strukturą i wielopoziomowym indeksem kolumn.
    """

    # sprowadzam slownik raw_data {rok:df} do listy [df] i ujednolicam każdy df
    ujednolicone_df_list = []
    for rok in raw_df_dict.keys():
        ujednolicone_df_list.append(ujednolic_dane(raw_df_dict[rok], metadane))

    wsp_st = wspolne_stacje(ujednolicone_df_list)
    df_list_wsp = [df[wsp_st] for df in ujednolicone_df_list]
    df_list_multi = [multiindex_funkcja(df, metadane, wsp_st) for df in df_list_wsp]
    df_gotowe = [przesun_date(df) for df in df_list_multi]
    return pd.concat(df_gotowe)