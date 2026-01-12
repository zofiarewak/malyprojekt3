import pandas as pd
import requests
import zipfile
import io

gios_archive_url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"
gios_url_ids = {2015: 'XXX', 2018: 'YYY', 2021: 'ZZZ', 2024: '582'}  # podmień X/Y/Z na odpowiednie id
gios_pm25_file = {2015: '2015_PM2.5_1g.xlsx', 2018: '2018_PM2.5_1g.xlsx',
                  2021: '2021_PM2.5_1g.xlsx', 2024: '2024_PM25_1g.xlsx'}

def download_gios_archive(year, gios_id, filename):
    response = requests.get(f"{gios_archive_url}{gios_id}")
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open(filename) as f:
            df = pd.read_excel(f, header=None)
    return df

def ujednolic_dane(tabela):
    tabela = tabela.copy()
    tabela = tabela[~tabela.iloc[:,0].isin(['Wskaźnik','Czas uśredniania','Jednostka', 'Kod stanowiska', 'Nr'])]
    tabela.columns = tabela.iloc[0]
    tabela = tabela.drop(tabela.index[0]).reset_index(drop=True)
    tabela = tabela.rename(columns={"Kod stacji": "Data poboru danych"})
    tabela = tabela.set_index('Data poboru danych')
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
    polnoc = df.index.hour == 0
    nowy_indeks = pd.Series(df.index)
    nowy_indeks[polnoc] = nowy_indeks[polnoc] - pd.Timedelta(days=1)
    df.index = pd.DatetimeIndex(nowy_indeks)
    return df

def przygotuj_df_gotowy(df_list, metadane):
    wsp_st = wspolne_stacje(df_list)
    df_list_wsp = [df[wsp_st] for df in df_list]
    df_list_multi = [multiindex_funkcja(df, metadane, wsp_st) for df in df_list_wsp]
    df_gotowe = [przesun_date(df) for df in df_list_multi]
    return pd.concat(df_gotowe)

