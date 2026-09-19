# STL-ből SVG Terep Szeletelő — Felhasználói útmutató

Nagy teljesítményű Python eszköz 3D STL modellek (például digitális magasságmodellek, hegyvidéki terepek és építészeti modellek) 2D vízszintes keresztmetszetekre történő szeletelésére, rétegzett SVG vektorfájlok formájában exportálva.

Kifejezetten **lézervágáshoz**, **CNC maráshoz**, **rétegzett domborzati modellekhez** (rétegelt lemez, karton, akril) és **kartográfiai vektortervezéshez** tervezve.

---

## Tartalomjegyzék

1. [Főbb jellemzők](https://www.google.com/search?q=%2523f%25C5%2591bb-jellemz%25C5%2591k&utm_source=gemini)
2. [Telepítés és követelmények](https://www.google.com/search?q=%2523telep%25C3%25ADt%25C3%25A9s-%25C3%25A9s-k%25C3%25B6vetelm%25C3%25A9nyek&utm_source=gemini)
3. [Gyors útmutató](https://www.google.com/search?q=%2523gyors-%25C3%25BAtmutat%25C3%25B3&utm_source=gemini)
4. [A rétegek egymásra helyezésének működése](https://www.google.com/search?q=%2523a-r%25C3%25A9tegek-egym%25C3%25A1sra-helyez%25C3%25A9s%25C3%25A9nek-m%25C5%25B1k%25C3%25B6d%25C3%25A9se&utm_source=gemini)
* [Következő réteg illesztési segédvonalai (piros)](https://www.google.com/search?q=%25231-k%25C3%25B6vetkez%25C5%2591-r%25C3%25A9teg-illeszt%25C3%25A9si-seg%25C3%25A9dvonalai-piros&utm_source=gemini)
* [Vízfelület észlelése (kék)](https://www.google.com/search?q=%25232-v%25C3%25ADzfel%25C3%25BClet-%25C3%25A9szlel%25C3%25A9se-k%25C3%25A9k&utm_source=gemini)
* [Vágóvonalak (fekete)](https://www.google.com/search?q=%25233-v%25C3%25A1g%25C3%25B3vonalak-fekete&utm_source=gemini)


5. [Parancssori (CLI) kapcsolók áttekintése](https://www.google.com/search?q=%2523parancssori-cli-kapcsol%25C3%25B3k-%25C3%25A1ttekint%25C3%25A9se&utm_source=gemini)
6. [Gyakorlati használati példák](https://www.google.com/search?q=%2523gyakorlati-haszn%25C3%25A1lati-p%25C3%25A9ld%25C3%25A1k&utm_source=gemini)
* [1. példa: Fix lemezvastagság (lézervágás)](https://www.google.com/search?q=%25231-p%25C3%25A9lda-fix-lemezvastags%25C3%25A1g-l%25C3%25A9zerv%25C3%25A1g%25C3%25A1s&utm_source=gemini)
* [2. példa: Fix rétegszám címkékkel és egyesített előnézettel](https://www.google.com/search?q=%25232-p%25C3%25A9lda-fix-r%25C3%25A9tegsz%25C3%25A1m-c%25C3%25ADmk%25C3%25A9kkel-%25C3%25A9s-egyes%25C3%25ADtett-el%25C5%2591n%25C3%25A9zettel&utm_source=gemini)
* [3. példa: Egyedi vízszint és stílus](https://www.google.com/search?q=%25233-p%25C3%25A9lda-egyedi-v%25C3%25ADzszint-%25C3%25A9s-st%25C3%25ADlus&utm_source=gemini)
* [4. példa: Előkészítés lézeres CAM szoftverekhez (LightBurn, Glowforge stb.)](https://www.google.com/search?q=%25234-p%25C3%25A9lda-el%25C5%2591k%25C3%25A9sz%25C3%25ADt%25C3%25A9s-l%25C3%25A9zeres-cam-szoftverekhez-lightburn-glowforge-stb&utm_source=gemini)


7. [Használat Python modulként](https://www.google.com/search?q=%2523haszn%25C3%25A1lat-python-modulk%25C3%25A9nt&utm_source=gemini)
8. [Tippek és hibaelhárítás](https://www.google.com/search?q=%2523tippek-%25C3%25A9s-hibaelh%25C3%25A1r%25C3%25ADt%25C3%25A1s&utm_source=gemini)

---

## Főbb jellemzők

* **Egységes globális koordináta-rendszer**: Az összes létrehozott SVG fájl azonos `viewBox` értékkel és méretekkel rendelkezik. Az egymásra helyezett lapok 100%-os pontossággal illeszkednek, kézi igazítás nélkül.
* **Piros illesztési segédvonalak minden szeleten**: Minden réteg automatikusan tartalmazza a *felette* lévő réteg körvonalát piros színnel (`#FF0000`), így még az összeszerelés előtt megjelölhetők vagy gravírozhatók a pontos pozíciók a fizikai lemezen.
* **Vízfelületek kinyerése**: Automatikusan felismeri a sík vízfelületeket (folyók, tavak, tenger), és megrajzolja azok körvonalait/szigeteit a legalsó alapszeleten kék színnel (`#0066CC`).
* **Lézervágásra kész színleképezés**:
* **Fekete (`#000000`)**: Aktuális réteg vágóvonala.
* **Piros (`#FF0000`)**: Illesztési jelölővonal a következő réteghez.
* **Kék (`#0066CC`)**: Vízparti gravírozási/jelölési vonal.


* **Rugalmas szeletelési módok**: Szeletelés darabszám alapján (`-n 10`) vagy fizikai anyagvastagság szerint (`-s 3.0` 3 mm-es lemezekhez).
* **Even-Odd kitöltéskezelés**: Megfelelően kezeli az üreges terepeket, völgyeket, többcsúcsú szigeteket és tóhatárokat.
* **Egyesített vizualizáció**: Lehetőség van egy `all_slices.svg` fájl exportálására, amely az összes réteget egymásra helyezve, magassági színátmenettel ábrázolja.

---

## Telepítés és követelmények

A szeletelő futtatásához **Python 3.10+** verzió és három szabványos könyvtár szükséges:

```powershell
pip install trimesh shapely numpy

```

---

## Gyors útmutató

Nyissa meg a terminált abban a mappában, amely a `stl_slicer.py` fájlt és a kívánt STL fájlt tartalmazza:

```powershell
# Alapvető 10 réteges szeletelés (automatikusan megkeresi az STL fájlt a mappában)
python stl_slicer.py -n 10

# 15 réteg generálása feliratokkal és egyesített all_slices.svg előnézettel
python stl_slicer.py -n 15 --labels --combine

```

A kimeneti fájlok a `./slices/` mappába kerülnek mentésre.

---

## A rétegek egymásra helyezésének működése

Rétegzett 3D domborzati modellek készítésekor minden egyes SVG szelet szemantikus, különböző színű SVG csoportokba van strukturálva:

```
┌────────────────────────────────────────────────────────┐
│ SVG vászon (a viewBox a teljes modell befoglaló mérete)│
│                                                        │
│   [Kék  #0066CC]  Víz / Partvonal (csak az 1. rétegen) │
│   [Piros #FF0000] Következő réteg segédvonala (L+1)    │
│   [Fekete #000000] Vágóvonal (aktuális réteg kerülete) │
│                                                        │
└────────────────────────────────────────────────────────┘

```

### 1. Következő réteg illesztési segédvonalai (piros)

* Az 1. szeleten egy piros körvonal mutatja a 2. szelet pontos ragasztási helyét.
* A 2. szeleten egy piros körvonal mutatja a 3. szelet ragasztási helyét, és így tovább.
* A legfelső rétegről a segédvonal automatikusan elmarad, mivel arra már nem kerül újabb elem.
* **Lézeres munkafolyamat**: Állítsa a piros vonalat alacsony teljesítményű **vektorgravírozásra / karcolásra (Score)**.

### 2. Vízfelület észlelése (kék)

* A digitális domborzatmodellek (DEM) a vízfelületeket (például a Duna vonalát a `terrain-184734.stl` fájlban) általában a legalacsonyabb magasságú, egységes fennsíkként rögzítik.
* A parancsfájl a felületi normálisok és a magassági hisztogram elemzésével azonosítja a vízfelületeket.
* A **legalsó szeleten (alaplemezen)** a partvonalak és a belső szigetek (például a Szentendrei-sziget) kék színnel jelennek meg.
* **Lézeres munkafolyamat**: Állítsa a kék vonalat **gravírozásra (Engrave)** vagy enyhe **karcolásra (Score)**.

### 3. Vágóvonalak (fekete)

* Az aktuális réteg tényleges külső határa.
* **Lézeres munkafolyamat**: Állítsa a fekete vonalat teljes teljesítményű **vágásra (Cut)**.

---

## Parancssori (CLI) kapcsolók áttekintése

```powershell
python stl_slicer.py [stl_fájl] [kapcsolók]

```

### Általános és be-/kimeneti beállítások

| Argumentum | Alapértelmezett | Leírás |
| --- | --- | --- |
| `stl_file` | Első `.stl` a mappában | A bemeneti STL fájl elérési útja. Ha hiányzik, az első talált `.stl` fájlt használja. |
| `-o`, `--out-dir` | `slices` | A létrehozott SVG fájlok célmappája. |
| `--prefix` | STL fájlneve | Egyedi előtag az exportált fájlokhoz. |
| `--combine` | `False` | Egy `*_all_slices.svg` fájl exportálása is, amely az összes réteget egymásra helyezve tartalmazza. |
| `--labels` | `False` | Kiírja a réteg sorszámát és Z magasságát a bal felső margóra. |
| `--precision` | `3` | Koordináták tizedesjegyeinek száma az SVG `d="..."` útvonalakban (csökkenti a fájlméretet). |
| `--units` | `mm` | Mértékegység utótagja az SVG fejlécben (`width="...mm" height="...mm"`). |

### Szeletelési paraméterek

| Kapcsoló | Alapértelmezett | Leírás |
| --- | --- | --- |
| `-n`, `--slices` | `10` | Az előállítandó szeletek teljes száma. |
| `-s`, `--step` | `None` | Fix rétegvastagság Z egységekben (pl. `3.0` mm). Felülírja a `-n` értéket. |
| `--z-min` | Háló min Z | A legalacsonyabb Z koordináta, ahonnan a szeletelés indul. |
| `--z-max` | Háló max Z | A legmagasabb Z koordináta, ahol a szeletelés véget ér. |
| `--spacing` | `midpoint` | `midpoint`: A rétegek közepén vág át (legjobb fizikai rétegzéshez).<br>

<br>`linear`: Egyenletesen elosztott mintavételezés a tartományban. |
| `--margin` | `5.0` | Külső margó milliméterben a modell befoglaló kerete körül. |

### Illesztési segédvonal (következő szint) stílusa

| Kapcsoló | Alapértelmezett | Leírás |
| --- | --- | --- |
| `--next-stroke` | `#FF0000` | A következő szint illesztési körvonalának színe (hex vagy színnév). |
| `--next-stroke-width` | `0.35` | A következő szint illesztési körvonalának vonalvastagsága. |
| `--no-next-outline` | `False` | A piros, következő szintet jelölő körvonal teljes kikapcsolása. |

### Vízfelület stílusa

| Kapcsoló | Alapértelmezett | Leírás |
| --- | --- | --- |
| `--water-level` | `auto` | A víz szintjének magassági küszöbértéke. Lehet `'auto'` vagy lebegőpontos szám (pl. `5.5`). |
| `--water-stroke` | `#0066CC` | Vízfelületek körvonalának színe. |
| `--water-stroke-width` | `0.4` | Vízfelületek körvonalának vonalvastagsága. |
| `--water-fill` | `none` | Vízfelületek kitöltési színe (pl. `"#E3F2FD"` halványkékhez). |
| `--no-water` | `False` | A víz észlelésének és megjelenítésének kikapcsolása az alsó szeleten. |

### Vágóvonal és vászon stílusa

| Kapcsoló | Alapértelmezett | Leírás |
| --- | --- | --- |
| `--stroke` | `#000000` | Az aktuális réteg határvonalának színe (vágóvonal). |
| `--stroke-width` | `0.5` | Az aktuális réteg határvonalának vonalvastagsága. |
| `--fill` | `none` | Az aktuális réteg kitöltési színe. |
| `--no-flip-y` | `False` | Ne tükrözze az Y tengelyt (megőrzi a nyers 3D Descartes-féle koordinátákat). |
| `--raw-coords` | `False` | Ne tolja el az origót `(0, 0)` pontba; megtartja az eredeti STL koordinátákat. |

---

## Gyakorlati használati példák

### 1. példa: Fix lemezvastagság (lézervágás)

Amennyiben **3,0 mm-es rétegelt lemezt vagy MDF lapokat** használ, szeleteljen a pontos vastagság szerint:

```powershell
python stl_slicer.py terrain-184734.stl -s 3.0 --labels -o slices_3mm

```

### 2. példa: Fix rétegszám címkékkel és egyesített előnézettel

12 egyenletesen elosztott réteg készítése beágyazott rétegszövegekkel és `all_slices.svg` előnézettel:

```powershell
python stl_slicer.py -n 12 --labels --combine -o output_12layers

```

### 3. példa: Egyedi vízszint és stílus

A víz kitöltése az alsó szeleten világoskék árnyalattal, a folyó körvonalának ciánkékre állítása:

```powershell
python stl_slicer.py -n 10 --water-fill "#D0E8FF" --water-stroke "#0088DD" --combine

```

### 4. példa: Előkészítés lézeres CAM szoftverekhez (LightBurn, Glowforge stb.)

A lézerszoftverek a vonalszínek alapján rendelik hozzá a vágási paramétereket:

* **Fekete `#000000**` $\rightarrow$ Réteg vágása (Nagy teljesítmény, lassú sebesség)
* **Piros `#FF0000**` $\rightarrow$ Illesztési jelölés (Alacsony teljesítmény, nagy sebesség)
* **Kék `#0066CC**` $\rightarrow$ Víz gravírozása / karcolása (Közepes teljesítmény)

Használjon vékony vonalvastagságot a precíz vágáshoz:

```powershell
python stl_slicer.py -n 15 --stroke-width 0.1 --next-stroke-width 0.1 --water-stroke-width 0.1

```

---

## Használat Python modulként

A `slice_stl` függvény közvetlenül is importálható saját Python szkriptekbe vagy automatizált folyamatokba:

```python
from stl_slicer import slice_stl

saved_files = slice_stl(
    stl_path="terrain-184734.stl",
    num_slices=10,
    out_dir="my_slices",
    labels=True,
    combine=True,
    stroke="#000000",
    next_stroke="#FF0000",
    water_stroke="#0066CC",
    water_fill="#E3F2FD"
)

print(f"Létrehozva {len(saved_files)} szeletfájl.")

```

---

## Tippek és hibaelhárítás

1. **Miért négyszögletes az alsó szelet (1. réteg)?**
* A 3D terep STL fájlokban a domborzat alatt egy lapos, tömör talapzat / alaplemez található. Az 1. réteg ezen a tömör alapon halad át, így egy stabil alaplapot biztosít a modell felépítéséhez. Erre az alaplemezre kerül a Duna vízfelülete és a 2. réteg piros illesztési körvonala.


2. **Hogyan lehet csak a hegydomborzatot szeletelni (a talapzat kihagyásával)?**
* Ellenőrizze a szkript által kiírt hálóinformációkat. A `terrain-184734.stl` esetében a terep $Z \approx 5.1\,\text{mm}$ magasságban kezdődik.
* Ha csak az alaplap feletti részt szeretné szeletelni:
```powershell
python stl_slicer.py --z-min 5.2 -n 10

```




3. **SVG-k megnyitása vektorgrafikus szoftverekben (Inkscape / Illustrator)**:
* Mindegyik SVG csoportosított elemeket tartalmaz `id="layer_XX"`, `id="next_layer_guide"` és `id="water_bodies"` azonosítókkal.
* A **Rétegek és objektumok (Layers & Objects) panelen** egyetlen kattintással ki- és bekapcsolhatja vagy zárolhatja az illesztési segédvonalakat vagy a vízréteget.


4. **Fájlméretek**:
* Az alapértelmezett `--precision 3` beállítás a koordinátákat 3 tizedesjegyre kerekíti (1 mikronos pontosság mm-ben számolva), ami akár 70%-kal csökkenti az SVG fájlok méretét a nyers lebegőpontos értékekhez képest, miközben minden részletet megőriz.
