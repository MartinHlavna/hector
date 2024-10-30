<!-- omit in toc -->
# Pomoc pre Hector

V prvom rade, ďakujeme za váš čas a snahu priložiť ruku k dielu! ❤️

Všetky typy pomoci sú vítané. Pozrite si [obsah](#obsah) pre rôzne spôsoby, ako pomôcť, a podrobnosti o tom, ako s nimi tento projekt narába. Predtým, ako sa zapojíte, si prosím prečítajte príslušnú sekciu. Uľahčí to prácu nám, správcom, a zjednoduší zážitok pre všetkých zúčastnených. 🎉

> A ak sa vám projekt páči, ale jednoducho nemáte čas pomôcť, aj to je v poriadku. Existujú aj iné jednoduché spôsoby, ako podporiť projekt a ukázať svoju vďačnosť:
> - Ohodnoťte projekt hviezdičkou
> - Zdieľajte ho na sociálnych sieťach
> - Spomeňte projekt na miestnych stretnutiach a povedzte o ňom svojim priateľom/kolegom

<!-- omit in toc -->
## Obsah

- [Mám otázku](#mám-otázku)
- [Chcem pomôcť](#chcem-pomôcť)
- [Nahlasovanie chýb](#nahlasovanie-chýb)
- [Navrhovanie vylepšení](#navrhovanie-vylepšení)
- [Váš prvý commit](#váš-prvý-commit)
- [Zlepšovanie dokumentácie](#zlepšovanie-dokumentácie)
- [Štýlové príručky](#štýlové-príručky)
- [Commit message](#commit-message)

## Mám otázku

> Ak sa chcete niečo opýtať, predpokladáme, že ste si prečítali dostupnú [dokumentáciu](https://github.com/MartinHlavna/hector).

Predtým, ako položíte otázku, je najlepšie vyhľadať existujúce [tickety](https://github.com/MartinHlavna/hector/issues), ktoré by vám mohli pomôcť. Ak ste našli vhodný ticket a stále potrebujete objasnenie, môžete svoju otázku napísať tam.

Ak sa váam vhodný ticket nepodarilo nájsť:

- Otvorte nový [ticket](https://github.com/MartinHlavna/hector/issues/new).
- Poskytnite čo najviac kontextu o probléme.
- Uveďte verziu projektu a platformy (napr. Hector 0.10.0, Operačný systém Windows 10), v závislosti od toho, čo sa zdá byť relevantné.

Potom sa o problém čo najskôr postaráme.

## Chcem pomôcť

> ### Právne upozornenie <!-- omit in toc -->
> Keď prispievate do tohto projektu, musíte súhlasiť s tým, že ste autorom 100% obsahu, že máte potrebné práva k obsahu a že obsah, ktorý prispievate, môže byť poskytnutý pod licenciou projektu.

### Nahlasovanie chýb

<!-- omit in toc -->
#### Pred odoslaním hlásenia o chybe

Dobré hlásenie o chybe by nemalo ostatných nútiť, aby vás naháňali pre ďalšie informácie. Preto vás prosíme, aby ste dôkladne preskúmali, zhromaždili informácie a vo svojej správe podrobne opísali problém. Prosím, vykonajte vopred nasledujúce kroky, aby sme mohli čo najrýchlejšie opraviť akúkoľvek potenciálnu chybu.

- Uistite sa, že používate najnovšiu verziu.
- Zistite, či je váš problém skutočne chybou a a uistite sa, že ste si prečítali [dokumentáciu](https://github.com/MartinHlavna/hector). Ak hľadáte podporu, možno budete chcieť pozrieť [túto sekciu](#mám-otázku).
- Aby ste zistili, či iní používatelia nezažili (a potenciálne už nevyriešili) rovnaký problém, ktorý máte vy, skontrolujte, či už neexistuje hlásenie o chybe pre váš problém v [bug trackeri](https://github.com/MartinHlavna/hector/issues?q=label%3Abug).
- Zhromaždite informácie o chybe:
    - Váš vstup a výstup
    - OS, platforma a verzia (Windows, Linux, macOS,...)
    - Dokážete spoľahlivo reprodukovať problém?

<!-- omit in toc -->
#### Ako môžem odoslať dobré hlásenie o chybe?

> Nikdy nesmiete nahlasovať bezpečnostné problémy, zraniteľnosti alebo chyby vrátane citlivých informácií do sledovača problémov alebo verejne inde. Namiesto toho musia byť citlivé chyby zaslané e-mailom na <info@martinhlavna.sk>.

Na sledovanie chýb používame GitHub issues. Ak narazíte na problém s projektom:

- Otvorte nový [problém](https://github.com/MartinHlavna/hector/issues/new).
- Vysvetlite správanie, ktoré očakávate, a skutočné správanie.
- Prosím, poskytnite čo najviac kontextu a popíšte *reprodukčný manuál*, aby sme vedeli problém nasimulovať aj u nás. Bonusom je, ak sa vám podarí problém izolovať a vytvoriť jednoduchý testovací príklad.
- Poskytnite informácie, ktoré ste zhromaždili v predchádzajúcej sekcii.

Keď je problém odoslaný:

- Tím projektu problém primerane označí.
- Člen tímu sa pokúsi reprodukovať problém s poskytnutými krokmi. Ak neexistuje reprodukčný manuál alebo žiadny zrejmý spôsob, ako problém reprodukovať, tím vás požiada o reprodukčný manuál a označí problém ako `needs-repro`. Chyby so značkou `needs-repro` nebudú riešené, kým nebudú reprodukované.
- Ak tím dokáže reprodukovať problém, bude označený `needs-fix`, ako aj prípadne ďalšími značkami (ako napríklad `critical`), a problém bude ponechaný [na implementáciu](#váš-prvý-kódový-príspevok).

### Navrhovanie vylepšení

Táto sekcia vás prevedie podávaním návrhov na vylepšenia pre Hector, **vrátane úplne nových funkcií a drobných vylepšení existujúcej funkčnosti**. Nasledovanie týchto pokynov pomôže správcom a komunite pochopiť váš návrh a nájsť súvisiace návrhy.

<!-- omit in toc -->
#### Pred odoslaním návrhu na vylepšenie

- Uistite sa, že používate najnovšiu verziu.
- Dôkladne si prečítajte [dokumentáciu](https://github.com/MartinHlavna/hector) a zistite, či už nie je funkčnosť pokrytá, možno pomocou individuálnej konfigurácie.
- Vykonajte [vyhľadávanie](https://github.com/MartinHlavna/hector/issues), aby ste zistili, či už vylepšenie nebolo navrhnuté. Ak áno, pridajte komentár k existujúcemu problému namiesto otvárania nového.
- Zistite, či váš nápad zapadá do rozsahu a cieľov projektu. Je na vás, aby ste presvedčili vývojárov projektu o prínosoch tejto funkcie. Majte na pamäti, že chceme funkcie, ktoré budú užitočné pre väčšinu našich používateľov, a nielen pre malú podskupinu. Ak cielite iba na menšinu používateľov, zvážte napísanie doplnkovej knižnice/pluginu.

<!-- omit in toc -->
#### Ako môžem odoslať dobrý návrh na vylepšenie?

Návrhy na vylepšenia sú sledované ako [GitHub issues](https://github.com/MartinHlavna/hector/issues).

- Použite **jasný a výstižný názov** problému na identifikáciu návrhu.
- Poskytnite **krok za krokom popis navrhovaného vylepšenia** v čo najväčších detailoch.
- **Opíšte súčasné správanie** a **vysvetlite, aké správanie by ste očakávali namiesto toho** a prečo. V tomto bode môžete tiež uviesť, ktoré alternatívy pre vás nefungujú.
- Možno budete chcieť **zahrnúť snímky obrazovky a animované GIFy**, ktoré vám pomôžu demonštrovať kroky alebo poukázať na časť, ktorej sa návrh týka. Môžete použiť [tento nástroj](https://www.cockos.com/licecap/) na zaznamenanie GIFov na macOS a Windows, a [tento nástroj](https://github.com/colinkeenan/silentcast) alebo [tento nástroj](https://github.com/GNOME/byzanz) na Linuxe.
- **Vysvetlite, prečo by toto vylepšenie bolo užitočné** pre väčšinu používateľov Hectora. Možno budete chcieť poukázať aj na iné projekty, ktoré to vyriešili lepšie a mohli by poslúžiť ako inšpirácia.


### Váš prvý commit
Vytvorte fork repozitára, v ktorom naimplementujete váš kód a následne vytvorte pull request. Člen tímu sa postará o review a buď funckionalitu zamerguje, alebo s vami bude ďalej komunikovať.
V pull requeste uvedťe aj všetky issues, ktoré sú týmto kódom vyriešené.

Prosím, nikdy nezvyšujte v pull requestoch verziu programu. Verziu programu zvyšujeme zásadne pred releasom.
V prípade, že je to možné, snažte sa vašu funkcionalitu pokryť aj automatickými testami.

V prípade, že plánujete riešiť niektorý z problémov, ktoré sú nahlásené v bug trackeri, prosím oznámte nám to v tickete, nech viacero ľudí nerieši ten istý problém. Ak je ticket niekomu priradený, znamená to, že na ňom pracuje. Takýto ticket prosím neriešte.
### Zlepšovanie dokumentácie
Všetky návrhy na zlepšovanie dokumentácie prosím vytvárajte ako [GitHub issues](https://github.com/MartinHlavna/hector/issues).

## Štýlové príručky
### Commit message
Označenie commitov je preferované v angličite. V prípade, že commit rieši niektorý z problémov bug trackeri, mal by začínať číslom ticketu. V prípade, že plánujete riešiť viacero problémov, commitujte ich prosím zvlášť, aby bolo jednoduchšie identifikovať, čoho sa daná zmena týka.

<!-- omit in toc -->
## Contributing
Tento návod je založený na **contributing-gen**. [Vytvorte si vlastný](https://github.com/bttger/contributing-gen)!
