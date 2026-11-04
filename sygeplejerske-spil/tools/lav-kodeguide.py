"""Bygger docs/kodeguide.md ud fra referencerne [S1], [K3], [G5] osv. i src/.

Linjenumrene findes automatisk, så guiden passer til koden, også efter rettelser.
Kør:  python3 tools/lav-kodeguide.py
"""
import os, re

ROOT = os.path.join(os.path.dirname(__file__), '..')

# (ref, overskrift, vigtige navne i koden, forklaring)
INDEX = [
 ('S1','Design-tokens og tema','`:root`, `--mon-*`','Alle farver ligger som CSS-variabler ét sted. Resten af CSS\'en bruger kun variablerne, så tema og lys/mørk tilstand styres centralt.'),
 ('S2','Topbjælke','`.top`, `.chip`','Titel og små "chips" med runde, klokkeslæt, forsøg og spiller.'),
 ('S3','Top 5-ticker','`.ticker`, `.tk-track`, `@keyframes tk`','30 px bjælke, der ruller fra højre mod venstre. Indholdet ligger to gange, og animationen flytter det -50 %, så rulningen ser uendelig ud. Stopper ved mus-over og ved "reduceret bevægelse".'),
 ('S4','Nedtælling','`#timer`, `.on`, `.low`','Vandret bjælke, der skrumper på 15 sekunder og bliver rød til sidst.'),
 ('S5','De tre rammer','`main#game`, `@media`','Grid med monitor, kort og tegneserie. Under 1100 px flyttes tegneserien ned, under 760 px stables alt (mobil).'),
 ('S6','Kortet','`.card`','Info-, stress-, feedback-, game over- og slutkort.'),
 ('S7','Knapper','`.actions`, `.key`','De fire valg og de store "videre"-knapper.'),
 ('S8','Patientnavne og spørgsmål','`.pt`, `.opts`, `.side`','Farvede "piller" med stuenummer, knaprækker til forskningsspørgsmål og tegneserie-kolonnen.'),
 ('S9','Profilformular','`.field`','Felterne i profilen før vagten.'),
 ('H1','Sidestruktur','`#card`, `#actions`, `#ward`, `#side`','Tomme beholdere, som JavaScript fylder. Elementer findes med `$("id")`.'),
 ('H2','Ticker-HTML','`#ticker`, `#tkTrack`','Fyldes af `renderTicker()` [K13].'),
 ('H3','De tre rammer','`#monitor`, `#card`, `#side`','Monitor [K10], kort [K14] og tegneserie [K12].'),
 ('K1','Grundopsætning','`SECONDS`, `PATIENTS`, `ROUNDS`','15 sekunder pr. valg, de fire patienter og de fem runder.'),
 ('K2','Historietræet','`N`','Spillets indhold: 31 noder. Node-ID\'et er vejen hertil (`R3-AB`). Hver node har patienter `f`, `alarm`, `title`, `sit`, fire valg `c` (A, B, X1, X2) og feedback `fb`. Se [historier.md](historier.md).'),
 ('K3','Slutprofiler og slutninger','`PROFILES`, `ENDINGS`','Profil efter antal A-valg (0-5) og 32 slutninger med hele vejen som nøgle, fx `AABBA`.'),
 ('K4','Tegneserie-manuskript','`COMICS`','Tre paneler pr. node: `[venstre, højre, hvem taler, taleboble]`.'),
 ('K5','Farver, figurer, ur og svar','`PCOL`, `PEOPLE`, `ANCHOR`, `DRIVERS`, `BLAME`','Patientfarver, figurer, ur-ankre i minutter efter midnat (420 = 07.00) og svarmuligheder.'),
 ('K6','Tilstand','`player`, `profile`, `S`','Anonymt spiller-ID og profil i `localStorage`. `S` holder hele vagtens tilstand, bl.a. `S.phase`, `S.node`, `S.path`.'),
 ('K7','Datalaget','`Data.save()`, `google.script.run`','Broen fra browser til server. Kalder `logRow()` [G5]. Fejl ignoreres bevidst, så spillet aldrig går i stå.'),
 ('K8','Top 5 og ventende række','`loadHS()`, `flushPending()`','Henter top 5 fra `getHighscore()` [G7]. Et game over-valg gemmes først, når "hvem havde ansvaret?" er besvaret.'),
 ('K9','Ny spiller / nyt spil','`newPlayer()`, `newGame()`','Nyt anonymt ID og tom profil, eller nyt vagt-ID.'),
 ('K10','Patientmonitoren','`renderWard()`, `setVitals()`, `ecgTick()`, `beat()`','Fire stuer, puls og stress. EKG tegnes på `<canvas>` med `requestAnimationFrame`, hastigheden følger pulsen.'),
 ('K11','Hjælpefunktioner','`esc()`, `hl()`, `clockNow()`, `opts()`, `bindOpts()`','`esc()` beskytter mod HTML i tekst. `hl()` gør patientnavne til farvede piller. `clockNow()` regner klokken ud (06.50 + 5 min pr. kort).'),
 ('K12','Tegneserien som SVG','`person()`, `patientBed()`, `prop()`, `panel()`, `wrap()`','Figurer tegnes direkte som SVG. Ingen billedfiler. Talebobler ombrydes til højst 3 linjer.'),
 ('K13','Sidekolonne og ticker','`renderSide()`, `renderTicker()`','Viser tegneserien for den aktuelle node og bygger top 5.'),
 ('K14','render() – tilstandsmaskinen','`render()`, `goNode()`','Tegner skærmen ud fra `S.phase`: profile → start → info → stress → feedback/over → … → end.'),
 ('K15','Nedtællingen','`startTimer()`, `stopTimer()`','Måler svartid i ms og hæver pulsen. Tiden ude = `choose("timeout")` = game over.'),
 ('K16','Et valg','`row()`, `choose()`','Bygger én datarække. X1/X2/timeout = game over, A/B = feedback.'),
 ('K17','Bedømmelse og næste node','`rate()`','Tjekker at de tre spørgsmål er besvaret, gemmer og går videre til `R{runde+1}-{vej}` eller slutskærmen.'),
 ('K18','Små hændelser og opstart','`addEventListener`, `setInterval(loadHS)`','Mus over navn lyser stuen op, tasterne 1-4 vælger, klik på kaldenavn skifter profil. Første `render()` og top 5 hvert minut.'),
]
CODE = [
 ('G1','Opsætning og datamodel','`FOLDER_ID`, `SHEET_ID`, `KEY`, `COLS`','`COLS` er datamodellen: kolonnerne i hvert faneblad. Nye kolonner er sat bagerst, så gamle rækker passer.'),
 ('G2','doGet – web-appens dør','`doGet(e)`, `out_()`','Viser spillet, eller resultatsiden hvis `?side=resultater&noegle=…` er rigtig. HTML læses fra Drive ved hvert besøg, så rettelser slår igennem uden ny udrulning.'),
 ('G3','Læs fil fra Drive','`readFile_()`','Navne der ender på `_` er private og kan ikke kaldes fra browseren.'),
 ('G4','Faneblade','`sheet_()`','Finder eller opretter fanebladet og retter overskriftsrækken til `COLS`.'),
 ('G5','Gem én række','`logRow()`','Whitelist via `COLS`, tekst kortes til 300 tegn, `\'` foran `= + - @` (formel-injektion), `LockService` mod samtidige skrivninger.'),
 ('G6','Læs data','`rows_()`, `getData(key)`','Laver rækker om til objekter. Kun med den rigtige nøgle.'),
 ('G7','Top 5','`getHighscore()`','Tæller korrekte valg, spil og hele vagter pr. spiller. Returnerer kun kaldenavn og tal.'),
 ('G8','Opsæt ark','`opsaetArk()`','Køres manuelt fra editoren.'),
]
RES = [
 ('R1','Konstanter og hjælpere','`KEY`, `avg`, `f1`, `pct`','`%%KEY%%` og `%%GAME_URL%%` sættes ind af serveren [G2].'),
 ('R2','Hent data','`load()`','Kalder `getData()` [G6] hvert 15. sekund.'),
 ('R3','Saml pr. spiller','`players()`','Kobler Spillere, Valg og Slutninger via spiller-ID og regner gennemsnit ud.'),
 ('R4','Tegn siden','`render()`','Hver blok fylder én sektion.'),
 ('R5','System eller genvej pr. runde','','Andel A/B, svartid og stress pr. runde.'),
 ('R6','Efter baggrund','','Sammenligning af grupper.'),
 ('R7','Her døde flest + profiler','','Game over pr. node og fordeling af slutprofiler.'),
 ('R8','Beslutningsoplevelse','`DR`','Stress, sikkerhed, "hurtig og usikker" (under 5 sek. og sikkerhed 1-2) og hvad der styrede valget.'),
 ('R9','Ansvar, job og refleksion','`bars()`','Hvem fik skylden, job i plejen før/efter, sværeste dilemma, synsændring, fritekst.'),
 ('R10','Tabel pr. spiller','`cols`','Sortérbar tabel. Klik på række viser alle valg.'),
]

def lines(path, hdr):
    out = {}
    for i, l in enumerate(open(os.path.join(ROOT, path), encoding='utf8').read().split('\n'), 1):
        m = re.search(r'\[([SHKGR]\d+)\]', l)
        if m and i > hdr:
            out[m.group(1)] = i          # sidste linje, hvor taggen står først
    return out

def table(path, hdr, rows):
    ln = lines(path, hdr)
    t = '| Ref | Del | Navne i koden | Hvad sker der |\n|---|---|---|---|\n'
    for ref, title, names, txt in rows:
        n = ln.get(ref)
        link = f'[{ref}](../{path}#L{n})' if n else ref
        t += f'| {link} | **{title}**' + (f' (linje {n})' if n else '') + f' | {names} | {txt} |\n'
    return t

md = f"""# Kodeguide

Opslag fra dokumentationen til koden. Hvert afsnit i koden starter med en kommentar som `/* [K14] ... */`.
Klik på referencen for at hoppe direkte til linjen på GitHub, eller søg efter fx `[K14]` i filen.

> Filen er genereret af `tools/lav-kodeguide.py`, så linjenumrene altid passer.

**Bogstaverne betyder:** S = stil (CSS) · H = HTML · K = klient-JavaScript · G = Google Apps Script (server) · R = resultatsiden

## src/index.html – spillet

{table('src/index.html', 25, INDEX)}
## src/Code.gs – serveren

{table('src/Code.gs', 13, CODE)}
## src/Resultater.html – resultatsiden

{table('src/Resultater.html', 12, RES)}
## Sådan hænger det sammen: ét valg fra klik til regneark

```mermaid
sequenceDiagram
    participant Spiller
    participant Spil as index.html (browser)
    participant Server as Code.gs (Apps Script)
    participant Ark as Google Sheet
    Spiller->>Spil: klikker valg B
    Spil->>Spil: choose("B") [K16] måler svartid
    Spil->>Spil: render() viser feedback [K14]
    Spiller->>Spil: svarer stress, sikkerhed, styret
    Spil->>Spil: rate() [K17]
    Spil->>Server: google.script.run.logRow("Valg", række) [K7]
    Server->>Server: whitelist + rens tekst + lås [G5]
    Server->>Ark: appendRow
    Spil->>Spil: goNode("R3-AB") næste situation
```

## Typiske spørgsmål til eksamen, og hvor svaret står

| Spørgsmål | Kig her |
|---|---|
| Hvordan ved spillet, hvilken skærm der skal vises? | `S.phase` og `render()` [K6] [K14] |
| Hvordan er 32 slutninger bygget uden 32 filer? | Node-ID = vejen, `"R"+(runde+1)+"-"+S.path` i `rate()` [K2] [K17] |
| Hvordan kommer data fra telefonen til regnearket? | `Data.save` → `google.script.run` → `logRow` [K7] [G5] |
| Hvordan er spillerne anonyme? | Tilfældigt ID i `localStorage`, kun kaldenavn [K6] [K9] |
| Hvordan er data beskyttet? | Whitelist, 300 tegn, formel-injektion, `LockService`, nøgle til resultater [G5] [G2] [G6] |
| Hvorfor skal man ikke udrulle igen ved hver rettelse? | `readFile_()` læser HTML fra Drive ved hvert besøg [G2] [G3] |
| Hvordan bliver svartid og "hurtig og usikker" målt? | `S.t0` og `ms` i `choose()`, beregning i [R8] [K15] [K16] |
| Hvordan virker tickeren? | Indhold x2 + `translateX(-50%)` [S3] [K13] |
| Hvordan er tegneserien lavet? | SVG genereret i JavaScript fra `COMICS` [K4] [K12] |
| Hvordan hænger patientnavne og monitor sammen? | `hl()` og `mouseover` [K11] [K18] [K10] |
"""
open(os.path.join(ROOT, 'docs/kodeguide.md'), 'w', encoding='utf8').write(md)
print('ok', len(md))
