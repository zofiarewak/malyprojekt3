import pandas as pd
import requests
import zipfile
import io

GIOS_ARCHIVE_URL = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"
GIOS_URL_IDS = {2015:'AAA', 2018:'BBB', 2021:'CCC', 2024:'582'}
GIOS_PM25_FILE = {2015:'2015_PM25.xlsx', 2018:'2018_PM25.xlsx', 2021:'2021_PM25.xlsx', 2024:'2024_PM25.xlsx'}

def download_gios_archive(year, gios_id, filename):
    url = f"{GIOS_ARCHIVE_URL}{gios_id}"
    response = requests.get(url)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open(filename) as f:
            df = pd.read_excel(f, header=None)
    return df

def ujednolic_dane(df):
    df = df.copy()
    df = df[~df.iloc[:,0].isin(['Wskaźnik','Czas uśredniania','Jednostka', 'Kod stanowiska', 'Nr'])]
    df.columns = df.iloc[0]
    df = df.drop(df.index[0]).reset_index(drop=True)
    df = df.rename(columns={"Kod stacji": "Data poboru danych"})
    df = df.set_index('Data poboru danych')
    return df

def download_metadata(gios_archive_url, metadata_url_id):
    url = f"{gios_archive_url}{metadata_url_id}"
    response = requests.get(url)
    response.raise_for_status()
    df = pd.read_excel(io.BytesIO(response.content), header=None, engine='openpyxl')
    return df

def update_station_codes(df, metadata):
    slownik_kodow = {}
    for _, row in metadata.iterrows():
        stary_kod = row['Stary Kod stacji \n(o ile inny od aktualnego)']
        nowy_kod = row["Kod stacji"]
        if pd.notna(stary_kod):
            stary_kod = stary_kod.split(",")
            for s in stary_kod:
                slownik_kodow[s] = nowy_kod
    df.rename(columns=slownik_kodow, inplace=True)
    return df

