[![Python application](https://github.com/MartinHlavna/hector/actions/workflows/python-app.yml/badge.svg)](https://github.com/MartinHlavna/hector/actions/workflows/python-app.yml)
[![GitHub Release](https://img.shields.io/github/v/release/MartinHlavna/hector?include_prereleases&sort=semver&display_name=release)](https://github.com/MartinHlavna/hector/releases/latest)

# Hector
![hector logo](https://github.com/MartinHlavna/hector/blob/main/images/hector-logo-white-bg.png?raw=true)
## O programe
Hector je jednoduchý nástroj pre autorov textov, ktorého cieľom je poskytnúť základnú štylistickú podporu. Je to plne konfigurovateľný nástroj, ktorý automaticky analyzuje a vyhodnocuje text. Cieľom programu nie je dodať zoznam problémov, ktoré má autor určite opraviť, ale len zvýrazniť potenciálne problematické časti. Konečné rozhodnutie je vždy na autorovi.
## Funkcie programu
### Zvýraznenie dlhých viet
Hector žltým podsvietením zvýrazňuje dlhé vety. Samotná dlhá veta problémom nie je, ale ak ich je veľa pokope, môže byť vhodné prerušiť to kratšou vetou. Rovnako však môže byť aj problémom aj to, ak je pokope priveľa krátkych viet bez prerušenia. 

Riešenie: Autor by sa mal snažiť o vhodnú kombináciu dlhých a krátkych viet, aby dostiahol vhodný rytmus textu.
### Štatistika výskytu slov
Hector v pravom paneli zobrazuje informáciu o počte výskytu daného slova.

Riešenie: Ak sa niektoré slovo opakuje výrazne veľakrát, autor môže zvážiť jeho nahradenie synonymami.
### Štatistika a zvýraznenie často sa opakujúcich slov
Hector v ľavom paneli zobrazuje slová, ktorá sa opakujú „blízko seba“. Na rozdiel od pravého panelu sú v tomto zozname iba slová, ktorých výskyty sú bliźšie, ako definovaná hodnota (napr. ak sa slovo zopakuje aspoň dvakrát v rozmedzí 100 znakov). Takýmto spôsobom dokáže hector identifikovať zhluky opakujúcich sa slov. Tieto slová sú zároveň zvýraznené. Po prejdení myšou nad takéto slovo sa v texte zvýrazania všetky jeho výskyty.

Riešenie: Nahradenie opakovaných slov synonymom, preformulovanie textu alebo doplnenie textu medzi jednotlivé výskyty.

#### Slová spojené spojovníkom
Slová spojené spojovníkom sú aktuálne považované za jeden token. Napr. tak a tik-tak berie momentálne ak dve rôzne slová. Bude treba v praxi overiť, čo je výhodnejšie.

### Zvýraznenie viacnásobnej medzery
Viacnásobná medzera je štandardne považovaná za zbytočnú. Hector ju automaticky zvýrazní načerveno.

Riešenie: Odstrániť viacnásobnú medzeru.

### Zvýraznenie viacnásobnej interpunkcie
Viacnásobná interpunkcia je štandardne považovaná za zbytočnú. Hector ju automaticky zvýrazní načerveno. Výnimkou je bežne používaná kombinácia ?! 

Riešenie: Odstrániť viacnásobnú interpunkciu.
### Zvýraznenie medzier na konci odstavcov
Medzery na konci odstavcov sú štandardne považované za zbytočné. Hector ich automaticky zvýrazní načerveno.

Riešenie: Odstrániť medzery na konci odstavcov.
### Štylistická zložitosť textu
Ďalšia informácia, ktorá má pomocný charakter je štylistická zložitosť textu, ktorá sa zobrazuje v spodnom status riadku vedľa informácií o dĺžke dokumentu.
Táto hodnota vychádza z výpočtu slovenského jazykovedca [Jozefa Mistríka](https://sk.wikipedia.org/wiki/Jozef_Mistr%C3%ADk). V jednej zo svojich [prác](https://www.juls.savba.sk/ediela/sr/1968/3/sr1968-3-lq.pdf) definoval vzorec, ktorým meral mieru zrozumiteľnosti textu na rozsahu (0,50). Hector zobrazuje v aplikácií jej „prevrátenú hodnotu“ (50 - Hodnota podľa p. Mistríka).

Nasledujúca tabuľka je odovdená od hodnôt v práci p. Mistríka na odkaze vyššie:

| Zložitosť | Popis                                                        |
|-----------|--------------------------------------------------------------|
| 0 až 9    | Veľmi ľahké texty. Najmä konverzačné a naratívne texty       |
| 10 až 19  | Priemerné, ľahko zrozumiteľné texty. Čítajú sa plynulo.      |
| 20 až 29  | Náročné, ale zrozumiteľné texty. Ide najmä o výkladové texty |
| 30 až 39  | Náročnejšie texty určené najmä na štúdium.                   |
| 40 až 50  | Texty na hranici zrozumiteľnosti                             |

Samozrejme, aj tieto hodnoty treba brať len veľmi orientačne. Lyrická próza bude mať napríklad prirozdene vyššiu zložitosť ako naratívny príbeh, rovnako ako môže mať na text vplyv aj subjektívny štýl autora, či žánru.

### Vyhľadávanie v texte
* Vpravo hore sa nachádza okno hľadať, ktoré je možné okrem kliknutia zafocusovať aj stlačením klávesovej skratky CTRL + F. Do editora sa dá vrátiť cez CTRL + E
* Kliknutím na šípku hore/dole, alebo klávesovou skratkou Shift + Enter /  Enter je moźné prechádzať po jednotlivých výskytoch textu
* Hľadanie neberie do úvay diakritiku, ani veľké a malé písmena

### Introspekcia
* Vľavo dole sa nachádza okno, v ktorom sa zobrazuje zvolené slovo v editore a jeho základný tvar
*  Spolu s ním sa zobrazuje slovný druh (POS tag)
*  Spolus ním sa zobrazuje aj funkcia vo vete (DEP tag)
*  Treba v praxi overiť, či sa zobrazujú dobre, pretože ich určuje pravdepodobnostný model
*  V prípade, že k základnému tvaru existujú synonymá, tak sa zobrazia aj tie

### Kontrola preklepov
* Program automaticky porovnáva slová voči slovníku a slová, ktoré v ňom nenájde zvýrazní
* Kvalita závisí od dostupných slovníkov

### Kontrola í/ý v niektorých prípadoch
* Program automaticky kontroluje, či je použité í v
    * Prídavnom mene, ktoré sa viaže na podstatné meno v nominatíve množného čísla v mužskom rode podľa vzoru pekný (napr. pekní chlapci)
    * Zámene, ktoré sa viaže na podstatné meno v nominatíve množného čísla v mužskom rode podľa vzoru pekný (napr. ľudia, ktorí)
* Program automaticky kontroluje, či je použité ý v
    * Prídavnom mene, ktoré sa viaže na podstatné meno v nominatíve jednotného čísla v mužskom rode podľa vzoru pekný (napr. pekný chlapec)
    * Zámene, ktoré sa viaže na podstatné meno v nominatíve jednotného čísla v mužskom rode podľa vzoru pekný (napr. človek, ktorý)

## Spustenie programu
### Spustenie z binárneho súboru
V prípade podporovaných platforiem sú k dispozícií kompletné spustiteľné [balíčky](https://github.com/MartinHlavna/hector/releases) vo forme binárnych súborov (napr. exe). 

### Spustenie zo zdrojového kódu
Kód bol testovaný s použitím python interpretera verzie 3.10.
```
# STIAHNUTIE ZDROJOVÝCH KÓDOV
git clone https://github.com/MartinHlavna/hector
# PRESUN DO NOVÉHO PRIEČINKA 
cd hector
# NAINŠTALOVANIE KNIŽNÍC
pip install -r requirements.txt
# SPUSTENIE PROGRAMU
python3 -m hector.py
```
### Pri prvom spustení
Od verzie 0.3.0 Hector pri spustení vytvára v priečinku, odkiaľ sa spúšta nasledovné podpriečinky:

```
data/                   --dáta aplikácie.
data/spacy-models/sk    --jazykový model pre spracovanie prirodzeného jazyka
```

Hector pri prvom štarte automaticky z internetu stiahne jazykový model a uloží ho do priečinka ```data/spacy-models/sk```
Pri uložení nastavení aplikácie sa uložia do súboru ```data/config.json```

Od verzie 0.5.0 Hector pri prvom štarte automaticky sťahuje slovníky
```
data/dictionary/sk-skspell     --slovenský slovník projektu skspell
data/dictionary/sk-líbreoffice --slovenský slovník projektu LibreOffice
```
## Technické informácie
### Spracovanie prirodzeného jazyka
Program využíva na identifikáciu slov a viet NLP prístup. Napriek tomu, že by sa dala táto úloha riešiť aj jednoduchšími metódami, zvolil som túto techniku najmä s ohľadom na budúce rozširovanie. [Model](https://github.com/MartinHlavna/hector-spacy-model), ktorý je použitý je natrénovaný na dátach z projektu [Slovak Universal Dependencies](https://universaldependencies.org/treebanks/sk_snk/index.html) (Licencia CC BY-SA 4.0).
### Slovníky
Program využíva synonymický slovník z projektu [LibreOffice](https://github.com/LibreOffice/dictionaries/tree/master/sk_SK) (Licencia GPLv2) a spelling slovník projektu [hunspell-sk](https://github.com/sk-spell/hunspell-sk) (Licencia MPLv2). 