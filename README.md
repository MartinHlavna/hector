[![Nuitka build](https://github.com/MartinHlavna/hector/actions/workflows/nuitka-build.yml/badge.svg)](https://github.com/MartinHlavna/hector/actions/workflows/nuitka-build.yml)
[![Python application](https://github.com/MartinHlavna/hector/actions/workflows/python-app.yml/badge.svg)](https://github.com/MartinHlavna/hector/actions/workflows/python-app.yml)
[![codecov](https://codecov.io/github/MartinHlavna/hector/graph/badge.svg?token=KO5BAQUVGP)](https://codecov.io/github/MartinHlavna/hector)
[![GitHub Release](https://img.shields.io/github/v/release/MartinHlavna/hector?include_prereleases&sort=semver&display_name=release)](https://github.com/MartinHlavna/hector/releases/latest)
![GitHub License](https://img.shields.io/github/license/MartinHlavna/hector)
![Static Badge](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)

# Hector

![hector logo](https://github.com/MartinHlavna/hector/blob/main/images/hector-logo-white-bg-socials.png?raw=true)
![hector screen](https://github.com/MartinHlavna/hector/blob/main/screenshots/hector.png?raw=true)

## HELP WANTED

Ak by sa niekto chcel aktívne zapojiť do projektu, momentálne by sa najviac hodilo, ak by niekto vedel otestovať a
dotiahnuť implementáciu na macOS.
Žiaľ, nemám k dispozícii zariadenie, na ktorom by som to vedel plnohodnotne otestovať.

Pre dalšie možnosti ako sa zapojiť si prečítajte [túto sekciu](CONTRIBUTING.md)

## NA STIAHNUTIE

Poznámka:
Ak má súbor v názve ```debug``` ide o ladiacu verziu. Momentálne sa to používa len pre windows. Ladiaca verzia otvára aj
konzolu z ktorej je možné v prípade chyby odčítať problém.

<!-- BEGIN DOWNLOAD LINKS -->
## Stable

**Najnovšia verzia:** [v.1.0.0-stable](https://github.com/MartinHlavna/hector/releases/tag/v.1.0.0-stable)

### Súbory:

| Súbor | Stiahnuť |
|------|----------|
| hector-linux-amd64.bin | [Stiahnuť](https://github.com/MartinHlavna/hector/releases/download/v.1.0.0-stable/hector-linux-amd64.bin) |
| hector-windows-amd64-debug.exe | [Stiahnuť](https://github.com/MartinHlavna/hector/releases/download/v.1.0.0-stable/hector-windows-amd64-debug.exe) |
| hector-windows-amd64.exe | [Stiahnuť](https://github.com/MartinHlavna/hector/releases/download/v.1.0.0-stable/hector-windows-amd64.exe) |

## Beta

**Najnovšia testovacia verzia:** [v.1.2.0-beta](https://github.com/MartinHlavna/hector/releases/tag/v.1.2.0-beta)

### Súbory:

| Súbor | Stiahnuť |
|------|----------|
| hector-linux-amd64.bin | [Download](https://github.com/MartinHlavna/hector/releases/download/v.1.2.0-beta/hector-linux-amd64.bin) |
| hector-windows-amd64-debug.exe | [Download](https://github.com/MartinHlavna/hector/releases/download/v.1.2.0-beta/hector-windows-amd64-debug.exe) |
| hector-windows-amd64.exe | [Download](https://github.com/MartinHlavna/hector/releases/download/v.1.2.0-beta/hector-windows-amd64.exe) |


<!-- END DOWNLOAD LINKS -->

## O programe

Hector je jednoduchý nástroj pre autorov textov, ktorého cieľom je poskytnúť základnú štylistickú podporu. Je to plne
konfigurovateľný nástroj, ktorý automaticky analyzuje a vyhodnocuje text. Cieľom programu nie je poskytnúť zoznam
problémov, ktoré má autor určite opraviť, ale len zvýrazniť potenciálne problematické časti. Konečné rozhodnutie je vždy
na autorovi.

### Aktuálny stav projektu

Aktuálna stable verzia je plnohodnotný nástroj pre finálne editovanie textu.

### Aktuálny cieľ projektu

V [ďalšej verzii](https://github.com/MartinHlavna/hector/milestone/3) programu sa chystá zavedenie projektov. Projekt
bude základným pracovným priestorom, v ktorom bude možné mať v jednotnom formáte informácie o svete, rôzne poviedky a
ich verzie, či dlhšie dielo rozdelené po kapitolách.

### Dlhodobý cieľ projektu

Z dlhodobého hľadiska je cieľom vytvoriť komplexný nástroj určený na písanie a editovanie beletristického textu. K
tomuto mǐľniku však vedie ešte dlhá cesta plná výziev.

## Funkcie programu

### [BETA] Projekt

Program umožnuje organizovať si prácu prostredníctvom projektov. Projekt umožnuje vytvoriť si jednotný pracovný priestor
pre dielo a umožnuje vytváranie viacerých textových súborov. Vďaka tomu je možné rozdeliť text po kapitolách, či
uchovávať informácie o postavcách a svete, ako separátne súbory.

Po štarte programu sa otvorí okno s výberom projektu. Je moźné zvoliť z posledných desiatich projektov,
načítať projekt zo súboru, alebo vytvoriť nový. Po spustení programu je možné projekt prepnúť sa do iného nedávneho
projektu, alebo otvorený projekt zavrieť, čím sa vrátite na obrazovku s výberom.

Funkcionalita je zatiať iba súčasťou testovej verzie.

### [BETA] Autosave

Textový súbor sa pri editovaní automaticky ukladá.

Funkcionalita je zatiať iba súčasťou testovej verzie.

### [BETA] Formátovanie textu
Hector umožnuje označiť bloky textu pomocou bold a italic tagov.

### Import súboru

Do Hectora je možné text načítať aj z ```.txt```, ```.docx```, ```.odt```, alebo ```.rtf``` súborov.

[BETA] V testovacej verzii sa načítaný text automaticky stáva súčasťou projektu. Je previazaný aj s pôvodným dokumentom,
z ktorého je možné pomocou menu, alebo stlačením ```CTRL + R``` načítať vźdy najnovší obsah.

### [BETA] Export súboru

Z hectora je možné exportovať ```.txt``` súbor.

Funkcionalita je zatiať iba súčasťou testovej verzie (technicky je táto možnosť aj súčasť stable verzie, ale je
označená, ako uloženie súboru).

Z hectora je možné exportovať ```.docx``` aj ```.rtf``` súbor, ktorý si zachová formátovanie nastavené z hectora. Pri
exporte sa na nastavenie odsadenia prvého riadku, či medzery medzi riadkami použije nastavenie z globálneho nastavenia
vzhľadu.

Statické parametre exportovaného dokumentu sú:
Riadkovanie: 1.2 násobok riakdu
Font textu: Arial

### Zvýraznenie dlhých viet

Hector automaticky zvýrazňuje dlhé vety. Samotná dlhá veta nie je problémom, ale ak ich je veľa pokope, môže byť vhodné
prerušiť ich kratšou vetou. Rovnako však môže byť problémom aj to, ak je pokope priveľa krátkych viet bez prerušenia.
Hector rozoznáva celkovo tri dĺžky viet:

| Dĺžka             | Zvýraznenie | Základné nastavenie               |
|-------------------|-------------|-----------------------------------|
| Krátka veta       | Žiadne      | Veta, ktorá je kratšia ako 8 slov | 
| Stredne dlhá veta | Žlté        | Veta, ktorá je dlhšia ako 8 slov  | 
| Dlhá veta         | Oranźové    | Veta, ktorá je dlhšia ako 16 slov | 

#### Možnosti prispôsobenia

| Nastavenie                                     | Význam                                                                                | Základná hodnota |
|------------------------------------------------|---------------------------------------------------------------------------------------|------------------|
| Zapnuté                                        | Umožňuje zapnúť alebo vypnúť funkcionalitu                                            | Zapnuté          | 
| Nepočítať slová kratšie ako X znakov           | Umožňuje určiť dĺžku slov, ktoré sa berú do úvahy v prípade vyhodnotenia dlhých viet. | 3 znaky          | 
| Veta je stredne dlhá, ak obsahuje aspoň X slov | Umožňuje určiť dĺžku stredne dlhej vety                                               | 8 slov           | 
| Veta je veľmi dlhá, ak obsahuje aspoň X slov   | Umožňuje určiť dĺžku dlhej vety                                                       | 16 slov          |

#### Odporúčanie

Autor by sa mal snažiť o vhodnú kombináciu dlhých a krátkych viet, aby dosiahol vhodný rytmus textu.

### Často použité slová

Hector v pravom paneli zobrazuje informáciu o počte výskytu daného slova. Prejdením myšou nad slovom sa v editore
zvýrazní. Kliknutím sa editor presunie na ďalší výskyt. Takýmto spôsobom je možné jednoducho hľadať problémové slová.

V prípade, že je v nastaveniach zapnutá voľba "používať základný tvar slova", program v pravom stĺpci zobrazuje základné
tvary slov. Napríklad budú všetky slová "ktorý", "ktorá", "ktoré" započítané ako výskyty slova "ktorý".

#### Možnosti prispôsobenia

| Nastavenie                     | Význam                                                                  | Základná hodnota |
|--------------------------------|-------------------------------------------------------------------------|------------------|
| Zapnuté                        | Umožňuje zapnúť alebo vypnúť funkcionalitu                              | Zapnuté          |
| Porovnávať základný tvar slova | Prísnejšie vyhodnocovanie, ktoré ignoruje skloňovanie a časovanie slova | Vypnuté          |
| Minimálna dĺžka slova          | Umožňuje určiť dĺžku slov, ktoré sa zobrazujú v pravom paneli.          | 3 znaky          |
| Minimálny počet opakovaní      | Slovo sa zobrazí v pravom paneli, len ak sa opakuje aspoň toľkokrát     | 10 opakovaní     |

#### Odporúčanie

Ak sa niektoré slovo opakuje výrazne veľakrát, autor môže zvážiť jeho nahradenie synonymami.

### Štatistika a zvýraznenie často sa opakujúcich slov

Hector v ľavom paneli zobrazuje slová, ktoré sa opakujú „blízko seba“. Na rozdiel od pravého panelu sú v tomto zozname
iba slová, ktorých výskyty sú bližšie ako definovaná hodnota (napr. ak sa slovo zopakuje aspoň dvakrát v rozmedzí 100
znakov). Takýmto spôsobom dokáže Hector identifikovať zhluky opakujúcich sa slov. Tieto slová sú zároveň zvýraznené.

Po prejdení myšou nad takéto slovo (buď v editore alebo v ľavom paneli) sa v texte zvýraznia všetky jeho výskyty.
Kliknutím sa editor presunie na daný výskyt smerom dopredu. Takýmto spôsobom je možné jednoducho hľadať problémové
slová.

Okrem samotných slov ľavý panel zobrazuje aj úseky, v ktorých sa slovo opakuje. Úseky sú zobrazené, len pokiaľ ich je
viac ako 1. Úseky sú zhluky opakovania rozdelené minimálnou medzerou medzi slovami. Prejdením myšou nad úsek sa
zvýraznia opakované slová len v danom úseku. Kliknutím na úsek sa editor nastaví na prvý výskyt v danom úseku.

V prípade, že je v nastaveniach zapnutá možnosť "porovnávať základný tvar slova", program používa základný tvar a voči
nemu aplikuje aj ostatné obmedzenia (napr. základný tvar slova "sú" je "byť". Ak je nastavená minimálna dĺžka slova 3
znaky, program zvýrazní aj kratšie výskyty).

#### Možnosti prispôsobenia

| Nastavenie                     | Význam                                                                                                      | Základná hodnota |
|--------------------------------|-------------------------------------------------------------------------------------------------------------|------------------|
| Zapnuté                        | Umožňuje zapnúť alebo vypnúť funkcionalitu                                                                  | Zapnuté          |
| Porovnávať základný tvar slova | Prísnejšie vyhodnocovanie, ktoré ignoruje skloňovanie a časovanie slova                                     | Vypnuté          |
| Minimálna dĺžka slova          | Umožňuje určiť dĺžku slov, ktoré sa zobrazujú v ľavom paneli.                                               | 3 znaky          |
| Minimálna vzdialenosť slov     | Požadovaná medzera medzi jednotlivými výskytmi rovnakého slova                                              | 100 slov         |
| Minimálny počet opakovaní      | Slovo sa zobrazí v ľavom paneli, len ak sa opakuje aspoň toľkokrát (berú sa do úvahy iba jednotlivé zhluky) | 3 opakovania     |

#### Odporúčanie

- Nahradiť opakované slová synonymami
- Preformulovať text
- Doplniť text medzi jednotlivé výskyty

#### Slová spojené spojovníkom

Slová spojené spojovníkom sú aktuálne považované za dva tokeny. Napríklad „tik-tak“ berie momentálne ako dve rôzne
slová. Bude treba v praxi overiť, čo je výhodnejšie.

### Zvýraznenie viacnásobnej medzery

Viacnásobná medzera je štandardne považovaná za zbytočnú. Hector ju automaticky zvýrazní načerveno.

#### Možnosti prispôsobenia

| Nastavenie | Význam                                     | Základná hodnota |
|------------|--------------------------------------------|------------------|
| Zapnuté    | Umožňuje zapnúť alebo vypnúť funkcionalitu | Zapnuté          |

#### Odporúčanie

Odstrániť viacnásobnú medzeru.

### Zvýraznenie viacnásobnej interpunkcie

Viacnásobná interpunkcia je štandardne považovaná za zbytočnú. Hector ju automaticky zvýrazní načerveno. Výnimkou je
bežne používaná kombinácia ?!

#### Možnosti prispôsobenia

| Nastavenie | Význam                                     | Základná hodnota |
|------------|--------------------------------------------|------------------|
| Zapnuté    | Umožňuje zapnúť alebo vypnúť funkcionalitu | Zapnuté          |

#### Odporúčanie

Odstrániť viacnásobnú interpunkciu.

### Zvýraznenie medzier na konci odstavcov

Medzery na konci odstavcov sú štandardne považované za zbytočné. Hector ich automaticky zvýrazní načerveno.

#### Možnosti prispôsobenia

| Nastavenie | Význam                                     | Základná hodnota |
|------------|--------------------------------------------|------------------|
| Zapnuté    | Umožňuje zapnúť alebo vypnúť funkcionalitu | Zapnuté          |

#### Odporúčanie

Odstrániť medzery na konci odstavcov.

### Kontrola gramatiky

#### Základná kontrola preklepov

- Program automaticky porovnáva slová voči slovníku a slová, ktoré v ňom nenájde, zvýrazní
- Kvalita závisí od dostupných slovníkov

#### Kontrola predložiek s/so a z/zo

- Program označí ako chybné použitie predložky **s/so** s iným pádom ako inštrumentálom
- Program označí ako chybné použitie predložky **z/zo** s iným pádom ako genitívom

#### Kontrola i/í pri použití zvratných zámen svoj, môj, tvoj, náš, váš

- Program označí ako chybný tvar mojim pri použití s inštrumentálom jednotného čísla (napr. S mojim psom)
- Program označí ako chybný tvar mojím pri použití s datívom množného čísla (napr. Daj mojím psom)
- Nie všetky tvary je možné skontrolovať. Z testovacej sady kontrola úspešne odhalí 11 zo 14 prípadov. Ďalšie
  spresňovanie už označuje ako chybné aj niektoré správne tvary
  viď [#67](https://github.com/MartinHlavna/hector/issues/67)

#### Kontrola spisovnosti

- Program označí ako chyby nasledovné výrazy:
    - môžte namiesto spisovného môžete
    - môžme namiesto spisovného môžeme
    - tohoto namiesto spisovného tohto
    - výraz chápať tomu namiesto spisovného chápeť to v rôznych variantoch (napr. chápem tomu, nechápem tomu, chápeš aj
      tomu, …)

#### Kontrola í/ý v niektorých prípadoch

- Program automaticky kontroluje, či je použité **í** v:
    - Prídavnom mene, ktoré sa viaže na podstatné meno v nominatíve množného čísla v mužskom rode podľa vzoru pekný (
      napr. pekní chlapci)
    - Zámene, ktoré sa viaže na podstatné meno v nominatíve množného čísla v mužskom rode podľa vzoru pekný (napr.
      ľudia, ktorí)
- Program automaticky kontroluje, či je použité **ý** v:
    - Prídavnom mene, ktoré sa viaže na podstatné meno v nominatíve jednotného čísla v mužskom rode podľa vzoru pekný (
      napr. pekný chlapec)
    - Zámene, ktoré sa viaže na podstatné meno v nominatíve jednotného čísla v mužskom rode podľa vzoru pekný (napr.
      človek, ktorý)

| Nastavenie | Význam                                     | Základná hodnota |
|------------|--------------------------------------------|------------------|
| Zapnuté    | Umožňuje zapnúť alebo vypnúť funkcionalitu | Zapnuté          |

#### Odporúčanie

- Opravovať gramatické chyby.
- Momentálne je viacero slov chybne označených ako preklepových, pretože kvalita open source slovníkov nedosahuje
  kvality komerčných riešení. V prípade, že ich chcete zlepšiť, odporúčam zapojiť sa do
  projektu [sk-spell](https://sk-spell.sk.cx/hunspell-sk).
- Vyhodnocovanie í/ý má momentálne tiež svoje limity. V prípade, že nájdete chybu,
  vytvorte [hlásenie chyby](https://github.com/MartinHlavna/hector/issues/new), alebo napíšte na info@martinhlavna.sk

### Kontrola úvodzoviek

Analyzuje použité úvodzovky a nájdené problémy zvýrazňuje červenou

* Použitie počítačových úvodzoviek namiesto správnych slovenských úvodzoviek
* Osamotené úvodzoky (väčšinou indikuje zbytočnú medzeru na jednej, alebo druhej strany)
* Správne použitie horných alebo spodných úvodzoviek

#### Možnosti prispôsobenia

| Nastavenie | Význam                                     | Základná hodnota |
|------------|--------------------------------------------|------------------|
| Zapnuté    | Umožňuje zapnúť alebo vypnúť funkcionalitu | Zapnuté          |

#### Odporúčanie

Všetky problémy by mal autor opraviť, ak na ne nemá špeciálny dôvod.

### Počet znakov, slov a normostrán

Hector v spodnom status riadku zobrazuje informačný počet znakov, slov a normostrán.

- Znaky sú počítané bez „Enterov“, tak ako to počíta aj MS Word, prípadne iné textové procesory. Webové formuláre môžu
  teda ukázať vyšší počet znakov.
- Normostrany sú počítané zaužívaným vzorcom 1800 znakov na normostranu.

### Štylistická zložitosť textu

Ďalšia informácia, ktorá má pomocný charakter, je štylistická zložitosť textu, ktorá sa zobrazuje v spodnom status
riadku vedľa informácií o dĺžke dokumentu. Táto hodnota vychádza z výpočtu slovenského
jazykovedca [Jozefa Mistríka](https://sk.wikipedia.org/wiki/Jozef_Mistr%C3%ADk). V jednej zo
svojich [prác](https://www.juls.savba.sk/ediela/sr/1968/3/sr1968-3-lq.pdf) definoval vzorec, ktorým meral mieru
zrozumiteľnosti textu na rozsahu (0,50). Hector zobrazuje v aplikácii jej „prevrátenú hodnotu“ (50 - hodnota podľa p.
Mistríka).

Nasledujúca tabuľka je odvodená od hodnôt v práci p. Mistríka na odkaze vyššie:

| Zložitosť | Popis                                                        |
|-----------|--------------------------------------------------------------|
| 0 až 9    | Veľmi ľahké texty. Najmä konverzačné a naratívne texty       |
| 10 až 19  | Priemerné, ľahko zrozumiteľné texty. Čítajú sa plynulo.      |
| 20 až 29  | Náročné, ale zrozumiteľné texty. Ide najmä o výkladové texty |
| 30 až 39  | Náročnejšie texty určené najmä na štúdium                    |
| 40 až 50  | Texty na hranici zrozumiteľnosti                             |

#### Odporúčanie

Samozrejme, aj tieto hodnoty treba brať len veľmi orientačne. Lyrická próza bude mať napríklad prirodzene vyššiu
zložitosť ako naratívny príbeh, rovnako ako môže mať na text vplyv aj subjektívny štýl autora či žánru.

### Vyhľadávanie v texte

- Vpravo hore sa nachádza okno hľadať, ktoré je možné okrem kliknutia aktivovať aj stlačením klávesovej skratky CTRL +
  F. Do editora sa dá vrátiť cez CTRL + E.
- Kliknutím na šípku hore/dole alebo klávesovou skratkou Shift + Enter / Enter je možné prechádzať po jednotlivých
  výskytoch textu.
- Hľadanie neberie do úvahy diakritiku ani veľké a malé písmená.

### Introspekcia

- Vľavo dole sa nachádza okno, v ktorom sa zobrazuje zvolené slovo v editore a jeho základný tvar.
- Spolu s ním sa zobrazuje slovný druh (POS tag).
- Spolu s ním sa zobrazuje aj funkcia vo vete (DEP tag).
- Treba v praxi overiť, či sa zobrazujú dobre, pretože ich určuje pravdepodobnostný model.
- V prípade, že k základnému tvaru existujú synonymá, tak sa zobrazia aj tie.

#### Odporúčanie

Okno má iba informačný charakter.

## Ďalšie nastavenia

| Nastavenie                                      | Význam                                                                                                                                                                                                                                                                          | Základná hodnota |
|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| Optimalizácia výkonu pri drobných zmenách textu | Ak má text aspoň 100 znakov a používateľ zmenil menej než 20 znakov, tak sa Hector snaží optimalizovať výkon tak, že analyzuje iba zmenenú časť textu. V prípade, že by došlo k neočakávaným problém je stále možnosť vynútiť plnú analýzu pomocou Upraviť -> Analyzovať všetko | Zapnuté          |

## Nastavenia vzhľadu

| Nastavenie                     | Význam                                                                                    | Základná hodnota |
|--------------------------------|-------------------------------------------------------------------------------------------|------------------|
| Odsadenie prvého riadku odseku | Veľkosť odsadenia prvého riadku v odseku. Zadaná hodnota je interpretovaná ako milimetre. | 7                |
| Medzera za odsekom             | Veľkosť odsadenia za odsekom. Zadaná hodnota je interpretovaná ako milimetre.             | 0                |

## Spustenie programu

### Spustenie z binárneho súboru

V prípade podporovaných platforiem sú k dispozícii kompletné
spustiteľné [balíčky](https://github.com/MartinHlavna/hector/releases) vo forme binárnych súborov (napr. exe). Program
stačí stiahnuť a skopírovať do vlastného priečinka.

### Spustenie zo zdrojového kódu (napr. pre účely vývoja)

Kód bol testovaný s použitím Python interpretera verzie 3.9, 3.10, 3.11 a 3.12. Odporúčaná verzia je 3.12.

#### Špeciálne kroky pre Linux (debian-based)

Nainštalovať balíčky:

```
sudo apt install -y autoconf libtool gettext autopoint cmake libcairo2-dev
```

Tiež je potrebné mať nainštalovanú podporu pre tkinter a dev v pythone (x prispôsobiť konkrétnej verzii)

```
sudo apt install -y python3.x-dev
sudo apt install -y python3.x-tk
```

#### Špeciálne kroky pre macOS

Nainštalovať balíčky:

```
brew install automake autoconf libtool
```

Následne možno pokračovať štandardne:

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

Od verzie 0.3.0 Hector pri spustení vytvára v priečinku, odkiaľ sa spúšťa, nasledovné podpriečinky:

```
data/                   -- dáta aplikácie
data/spacy-models/sk    -- jazykový model pre spracovanie prirodzeného jazyka
```

Hector pri prvom štarte automaticky z internetu stiahne jazykový model a uloží ho do priečinka `data/spacy-models/sk`.
Pri uložení nastavení aplikácie sa uložia do súboru `data/config.json`.

Od verzie 0.5.0 Hector pri prvom štarte automaticky sťahuje slovníky:

```
data/dictionary/sk-skspell     -- slovenský slovník projektu skspell
data/dictionary/sk-libreoffice -- slovenský slovník projektu LibreOffice
```

Od verzie 0.11.0 Hector pri prvom štarte automaticky sťahuje slovenský model
pre [MorphoDiTa](https://ufal.mff.cuni.cz/morphodita).:

```
data/morphodita     -- jazykový model pre spracovanie prirodzeného jazyka pomocou morfologického analyzátora MorphoDiTa
```

## Technické informácie

### Spracovanie prirodzeného jazyka

Program využíva na identifikáciu slov a viet NLP prístup. Napriek tomu, že by sa dala táto úloha riešiť aj jednoduchšími
metódami, zvolil som túto techniku najmä s ohľadom na budúce
rozširovanie. [Model](https://github.com/MartinHlavna/hector-spacy-model), ktorý je použitý, je natrénovaný na dátach z
projektu [Slovak Universal Dependencies](https://universaldependencies.org/treebanks/sk_snk/index.html) (Licencia CC
BY-SA 4.0).

Okrem toho program kombinuje výsledky spacy modelu aj s morfologickým
analyzátorom [MorphoDiTa](https://ufal.mff.cuni.cz/morphodita).

### Slovníky

Program využíva synonymický slovník z
projektu [LibreOffice](https://github.com/LibreOffice/dictionaries/tree/master/sk_SK) (Licencia GPLv2) a spelling
slovník projektu [hunspell-sk](https://github.com/sk-spell/hunspell-sk) (Licencia MPLv2).

### Ikony

Program využíva [FontAwesome](https://fontawesome.com/) (Licencia SIL OFL 1.1)