import pandas as pd
import requests
import zipfile
import io
import pytest
def download_gios_archive(gios_archive_url, gios_id, filename):
    response = requests.get(f"{gios_archive_url}{gios_id}")
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open(filename) as f:
            df = pd.read_excel(f, header=None)
    return df

def download_metadata(gios_archive_url,metadata_url_id):
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

def zaktualizuj_nazwy_stacji(df,metadane):
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

def ujednolic_dane(tabela,metadane):
    tabela = tabela.copy()
    tabela = tabela[~tabela.iloc[:,0].isin(['Wskaźnik','Czas uśredniania','Jednostka', 'Kod stanowiska', 'Nr'])]
    tabela.columns = tabela.iloc[0]
    tabela = tabela.drop(tabela.index[0]).reset_index(drop=True)
    tabela = tabela.rename(columns={"Kod stacji": "Data poboru danych"})
    tabela = tabela.set_index('Data poboru danych')
    tabela = zaktualizuj_nazwy_stacji(tabela,metadane)
    return tabela 

def wspolne_stacje(df_list):
    wsp = df_list[0].columns
    for df in df_list[1:]:
        wsp = wsp.intersection(df.columns)
    return wsp

def multiindex_funkcja(df, metadane, wsp_stacje):
    filt = metadane[metadane['Kod stacji'].isin(wsp_stacje)]
    tuples = list(zip(filt['Kod stacji'], filt['Miejscowość']))
    df.columns = pd.MultiIndex.from_tuples(tuples, names=("Kod stacji", "Miejscowość"))
    return df

def przesun_date(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index, errors="coerce",format="%Y-%m-%d %H:%M:%S")
    polnoc = df.index.hour == 0
    nowy_indeks = [t - pd.Timedelta(seconds=1) if h else t for t, h in zip(df.index, polnoc)]
    df.index = pd.DatetimeIndex(nowy_indeks)
    return df

def df_gotowy(df_list, metadane):
    wsp_st = wspolne_stacje(df_list)
    df_list_wsp = [df[wsp_st] for df in df_list]
    df_list_multi = [multiindex_funkcja(df, metadane, wsp_st) for df in df_list_wsp]
    df_gotowe = [przesun_date(df) for df in df_list_multi]
    return pd.concat(df_gotowe)