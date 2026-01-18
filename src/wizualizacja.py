import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def wykres_porownanie_miast(srednie_miast:pd.DataFrame, lata:list[int], miasta:list[str]) -> None:
    """
    Rysuje wykres porównujący średnie miesięczne stężenia PM2.5
    dla wybranych miast i lat.

    Funkcja przyjmuje DataFrame otrzymany z funkcji srednie_po_stacjach,
    w którym:
    - indeks wierszy jest dwupoziomowy: (Rok, Miesiąc),
    - kolumny odpowiadają miejscowościom.

    Na jednym wykresie rysowane są łamane linie przedstawiające
    zmiany średnich miesięcznych wartości PM2.5 w kolejnych miesiącach,
    osobno dla każdej kombinacji miasta i roku.

    Parameters
    ----------
    srednie_miast : pandas.DataFrame
        DataFrame ze średnimi miesięcznymi PM2.5 zagregowanymi
        po miejscowościach (wynik funkcji srednie_po_stacjach).
    lata : list of int
        Lista lat, które mają zostać uwzględnione na wykresie.
    miasta : list of str
        Lista nazw miejscowości, dla których mają zostać narysowane wykresy.

    Returns
    -------
    None
        Funkcja wyświetla wykres i nie zwraca żadnej wartości.
    """
    plt.figure(figsize=(12,8))

    for miasto in miasta:
        m = srednie_miast[miasto]
        for rok in lata:
            plt.plot(m.xs(rok, level='Rok').index, m.xs(rok, level='Rok').values,
             marker='*', label=f'{miasto} {rok}')

    plt.xlabel('Miesiąc')
    plt.ylabel('Średnia wartość PM2.5')
    plt.title('Średnie miesięczne stężenie PM2.5 w Katowicach i Warszawie')
    plt.xticks(range(1,13))
    plt.grid(True)
    plt.legend()
    plt.show()

def wykres_heatmap_srednie(srednie_po_miejscach:pd.DataFrame, lata:list[int]) -> None:
    """
    Rysuje zestaw wykresów typu heatmap przedstawiających
    średnie miesięczne stężenia PM2.5 dla wszystkich miejscowości.

    Funkcja przyjmuje DataFrame otrzymany z funkcji srednie_po_stacjach,
    w którym:
    - indeks wierszy ma dwa poziomy: (Rok, Miesiąc),
    - kolumny odpowiadają poszczególnym miejscowościom.

    Dla każdej miejscowości generowany jest osobny wykres heatmapy,
    gdzie:
    - oś X odpowiada miesiącom,
    - oś Y odpowiada latom,
    - kolor reprezentuje wartość średniego stężenia PM2.5.

    Wykresy są ułożone w macierzy 3 × m, gdzie m zależy od liczby miejscowości.

    Parameters
    ----------
    srednie_po_miejscach : pandas.DataFrame
        DataFrame ze średnimi miesięcznymi PM2.5 zagregowanymi
        po miejscowościach (wynik funkcji srednie_po_stacjach).
    lata : list of int
        Lista lat uwzględnianych na wykresach.

    Returns
    -------
    None
        Funkcja wyświetla zestaw wykresów heatmap i nie zwraca żadnej wartości.
    """
    miejscowosci = srednie_po_miejscach.columns.to_list()
    fig, axes = plt.subplots((len(miejscowosci)+2)//3, 3, figsize=(15, 20))
    fig.suptitle("Średnie miesięczne stężenie PM2.5 we wszystkich miejscowościach", fontsize=20)
    for nr, miasto in enumerate(miejscowosci):
        df_heat = pd.concat([srednie_po_miejscach.loc[y, miasto] for y in lata], axis=1).T
        df_heat.index = lata
        df_heat.columns.names = ['Miesiac']
        df_heat.index.names = ['Rok']
        y = nr//3
        x = nr%3
        hm = axes[y][x].imshow(df_heat, aspect='auto', vmin=0, vmax=80)
        axes[y][x].set_title(miasto)
        axes[y][x].set_xticks(range(12))
        axes[y][x].set_xticklabels(range(1,13))
        axes[y][x].set_yticks(range(len(lata)))
        axes[y][x].set_yticklabels(lata)
        axes[y][x].set_xlabel("Miesiąc")
        axes[y][x].set_ylabel("Rok")
        fig.colorbar(hm, ax=axes[y][x], fraction=0.046, pad=0.04)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    plt.show()

def wykres_przekroczenia(ile_dni_wybrane_stacje:pd.DataFrame, wybrane_stacje:list[str], lata:list[int], norma_dobowa:float) -> None:
    """
    Rysuje wykres słupkowy liczby dni z przekroczeniem normy PM2.5
    dla wybranych stacji i lat.

    Funkcja przyjmuje DataFrame będący wycinkiem wyniku funkcji
    dni_przekroczenia_normy (tj. dni_wiecej_normy[wybrane_stacje]).
    Na wykresie:
    - oś X - stacje pomiarowe,
    - oś Y przedstawia liczbę dni z przekroczeniem normy,
    - słupki są pogrupowane według lat.

    Parameters
    ----------
    ile_dni_wybrane_stacje : pandas.DataFrame
        DataFrame z liczbą dni przekroczeń normy PM2.5
        dla wybranych stacji i lat.
    wybrane_stacje : list
        Lista wybranych stacji (np. wynik funkcji wybierz_stacje_max_min).
    lata : list of int
        Lista lat, dla których rysowane są słupki.
    norma_dobowa : float
        Wartość dobowej normy PM2.5 użytej do obliczeń,
        wyświetlana w tytule wykresu.

    Returns
    -------
    None
        Funkcja wyświetla wykres słupkowy i nie zwraca żadnej wartości.
    """
    x = np.arange(len(wybrane_stacje))
    width = 0.2
    plt.figure(figsize=(10,6))
    plt.bar(x-width, ile_dni_wybrane_stacje.loc[lata[0]], width, color='red', label=lata[0])
    plt.bar(x, ile_dni_wybrane_stacje.loc[lata[1]], width, color='green', label=lata[1])
    plt.bar(x+width, ile_dni_wybrane_stacje.loc[lata[2]], width, color='blue', label=lata[2])
    plt.bar(x+2*width, ile_dni_wybrane_stacje.loc[lata[3]], width, color='purple', label=lata[3])
    plt.xticks(x, [stacja[0] for stacja in wybrane_stacje], rotation=30)
    plt.ylabel('Liczba dni z przekroczeniem normy PM2.5')
    plt.xlabel('Stacja')
    plt.legend()
    plt.title(f"Liczba dni z przekroczeniem normy dobowej = {norma_dobowa} µg/m³")
    plt.grid(True)

def plot_exceedence_by_voivodeship(df: pd.DataFrame, daily_norm: float) -> None:
    """
    Bar chart plotting number of days with PM2.5 exceedence by voivodeship.
    --------
    Parameters
        df: data frame with exceedence days grouped by voivodeship
        daily norm: threshold of daily norm of PM2.5 value
    --------
    Returns
    None
        Shows plotted bar chart
    """

    ax = df.plot(kind="bar", figsize=(14, 7))
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of exceedence days")
    ax.set_title(f"Days with PM2.5 above daily norm = {daily_norm} ug/m3 grouped by voivodeship")
    ax.grid(True, axis="y")

    plt.legend(title="Voivodeship", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()