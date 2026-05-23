# PLC Monitor Pro
## System Monitorowania i Wykrywania Anomalii Maszyn Przemysłowych

---

## Opis projektu

**PLC Monitor Pro** to desktopowa aplikacja napisana w Pythonie, która symuluje i monitoruje w czasie rzeczywistym cztery kanały pomiarowe maszyny przemysłowej (PLC):

| Kanał        | Jednostka | Zakres nominalny | Próg alarmu górny | Próg alarmu dolny |
|--------------|-----------|-----------------|-------------------|-------------------|
| Temperatura  | °C        | 67 – 77         | 90 °C             | 50 °C             |
| Ciśnienie    | bar       | 4,5 – 5,5       | 7,0 bar           | 2,5 bar           |
| Wibracje     | mm/s      | 1,4 – 2,6       | 5,0 mm/s          | 0,1 mm/s          |
| Prąd         | A         | 11,5 – 13,5     | 18,0 A            | 6,0 A             |

### Cel automatyzacji

Tradycyjny nadzór maszyn wymaga ciągłej obecności operatora i ręcznego odczytu wskazań.  
Aplikacja **zastępuje ten proces** poprzez:

- automatyczne odczytywanie i rejestrowanie danych co sekundę,
- natychmiastowe wykrywanie przekroczeń progów twardych,
- statystyczne wykrywanie subtelnych anomalii metodą **Z-score** (okno kroczące 60 próbek),
- zapisywanie wszystkich zdarzeń w lokalnej bazie danych **SQLite**,
- eksport danych do pliku **CSV** jednym kliknięciem.

---

## Technologie

| Technologia | Zastosowanie |
|-------------|--------------|
| Python 3.11+ | Język programowania |
| Tkinter      | Graficzny interfejs użytkownika (wbudowany w Python) |
| Matplotlib   | Wykresy czasu rzeczywistego osadzone w GUI |
| SQLite3      | Persystencja danych (wbudowany w Python) |
| NumPy        | Generowanie danych symulacyjnych |

---

## Wymagania systemowe

- **Python 3.11** lub nowszy (https://www.python.org/downloads/)
- System: Windows 10/11, macOS 12+, Linux (Ubuntu 22.04+)
- Biblioteki zewnętrzne: `matplotlib`, `numpy`

> **Tkinter** i **SQLite3** są wbudowane w standardową instalację Pythona – nie wymagają osobnej instalacji.

---

## Instalacja

### Krok 1 – Sprawdź wersję Pythona

```bash
python --version
```

Oczekiwany wynik: `Python 3.11.x` lub wyższy.

### Krok 2 – Przejdź do folderu projektu

```bash
cd ścieżka\do\folderu\plc
```

### Krok 3 – Zainstaluj zależności

```bash
# Standardowa instalacja
pip install -r requirements.txt

# Jeśli Python zainstalowany przez uv (Python 3.14+):
python3.14 -m pip install -r requirements.txt --break-system-packages
```

lub ręcznie:

```bash
python3.14 -m pip install matplotlib numpy --break-system-packages
```

---

## Uruchomienie

```bash
# Python w PATH:
python main.py

# Python 3.14 przez uv:
python3.14 main.py
```

Na Windows możesz też kliknąć dwukrotnie plik `main.py`, jeśli Python jest skojarzony z plikami `.py`.

---

## Obsługa aplikacji

### Zakładka 📊 Monitor

1. Kliknij przycisk **▶ START** – aplikacja zaczyna symulować odczyty co sekundę.
2. Cztery karty u góry pokazują bieżące wartości każdego czujnika.
3. Karty zmieniają kolor na **czerwony (ALARM)** przy wykryciu anomalii.
4. Wykresy liniowe pokazują ostatnie **120 sekund** danych.
5. Przerywane linie na wykresach oznaczają progi alarmowe:
   - **czerwona** = próg górny
   - **żółta** = próg dolny
6. Kliknij **■ STOP** aby wstrzymać monitoring.

### Zakładka ⚠ Alerty

- Lista wszystkich wykrytych anomalii posortowana od najnowszej.
- Kolory wierszy:
  - 🔴 Czerwony – przekroczenie progu górnego
  - 🟡 Żółty – spadek poniżej progu dolnego
  - 🟣 Fioletowy – anomalia statystyczna (Z-score)
- Przycisk **Wyczyść widok** czyści listę *tylko w widoku* (dane pozostają w bazie).

### Zakładka 📈 Statystyki

- Łączna liczba odczytów i anomalii w sesji.
- Wskaźnik procentowy anomalii.
- Wykres słupkowy: liczba anomalii dla każdego parametru.
- Statystyki odświeżają się automatycznie co 10 odczytów.

### Eksport danych

- **⬇ Eksport CSV** – zapisuje ostatnie 5000 odczytów do pliku CSV.
- **⬇ Eksport alerty** – zapisuje wszystkie anomalie do pliku CSV.

Oba pliki otwierają się w Excel / LibreOffice Calc.

---

## Struktura projektu

```
plc/
├── main.py               # Główna aplikacja (GUI Tkinter + Matplotlib)
├── data_simulator.py     # Symulator danych z czujników PLC
├── anomaly_detector.py   # Detekcja anomalii (progi + Z-score)
├── database.py           # Warstwa danych SQLite
├── requirements.txt      # Zależności Python
├── README.md             # Dokumentacja (ten plik)
└── machine_monitor.db    # Baza danych SQLite (tworzona automatycznie)
```

---

## Algorytm wykrywania anomalii

Detekcja działa dwupoziomowo:

**Poziom 1 – progi twarde:**
```
jeśli wartość > próg_górny  →  ALARM (przekroczenie górne)
jeśli wartość < próg_dolny  →  ALARM (przekroczenie dolne)
```

**Poziom 2 – Z-score (statystyczny, po zebraniu ≥ 20 próbek):**

$$Z = \frac{|x - \bar{x}|}{\sigma}$$

gdzie $\bar{x}$ i $\sigma$ obliczane są na oknie kroczącym 60 ostatnich próbek.  
Jeśli $Z > 3{,}5$ → anomalia statystyczna.

---



