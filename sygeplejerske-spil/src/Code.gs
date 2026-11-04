/*
================================================================================
  EN VAGT SOM SYGEPLEJERSKE · Code.gs  (serveren i Google Apps Script)
--------------------------------------------------------------------------------
  Apps Script er JavaScript, der kører hos Google. Denne fil gør tre ting:
    1. Viser spillet og resultatsiden som en web-app (doGet)        [G2]
    2. Gemmer hvert svar som en række i et Google Sheet (logRow)    [G5]
    3. Leverer data til resultatsiden og top 5 (getData, getHighscore) [G6][G7]
  Web-appen kører som ejeren (Ralf), så spillerne ikke skal logge ind og ikke får
  adgang til Sheetet. De kan kun kalde funktionerne nedenfor.
================================================================================
*/

/* [G1] OPSÆTNING. Mappe med HTML-filerne, Sheetet med data og den hemmelige nøgle,
   der beskytter resultatsiden. COLS er "datamodellen": kolonnerne i hvert faneblad.
   Nye kolonner er sat bagerst, så gamle rækker stadig passer.                    */
var FOLDER_ID = 'DIN_DRIVE_MAPPE_ID';   // id på Drive-mappen med index.html og Resultater.html
var SHEET_ID  = 'DIT_SHEET_ID';         // id på Google Sheetet, der samler data
var KEY       = 'SKIFT_MIG';            // hemmelig nøgle til resultatsiden. Aldrig i et offentligt repo!
var COLS = {
  Spillere: ['ts', 'player', 'nick', 'age', 'bg', 'desc', 'erfaring', 'interesse_foer', 'kendskab'],
  Valg: ['ts', 'player', 'nick', 'attempt', 'node', 'round', 'choice', 'outcome', 'ms', 'stress', 'game', 'sikkerhed', 'styret', 'ansvar'],
  Slutninger: ['ts', 'player', 'nick', 'attempt', 'path', 'profile', 'game', 'svaerest', 'synsaendring', 'interesse_efter', 'overrasket']
};

/* [G2] doGet kører, når nogen åbner linket. ?side=resultater&noegle=... giver
   resultatsiden (kun med rigtig nøgle), ellers spillet. HTML-filerne læses fra Drive
   ved hvert besøg, så en rettelse i index.html slår igennem med det samme. */
function doGet(e) {
  var p = (e && e.parameter) || {};
  var url = ScriptApp.getService().getUrl();
  if (p.side === 'resultater') {
    if (p.noegle !== KEY) return HtmlService.createHtmlOutput('<p style="font-family:sans-serif;padding:24px">Forkert nøgle.</p>');
    var html = readFile_('Resultater.html').replace(/%%GAME_URL%%/g, url).replace(/%%KEY%%/g, KEY);
    return out_(html, 'Resultater – En vagt som sygeplejerske');
  }
  return out_(readFile_('index.html'), 'En vagt som sygeplejerske');
}

function out_(html, title) {
  return HtmlService.createHtmlOutput(html)
    .setTitle(title)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/* [G3] Læser en fil fra Drive-mappen. Navne der ender på _ er private i Apps Script
   og kan ikke kaldes fra browseren. */
function readFile_(name) {
  var it = DriveApp.getFolderById(FOLDER_ID).getFilesByName(name);
  if (!it.hasNext()) throw new Error('Mangler filen ' + name + ' i mappen');
  return it.next().getBlob().getDataAsString('UTF-8');
}

/* [G4] Finder (eller opretter) et faneblad og sørger for, at overskriftsrækken
   matcher COLS. */
function sheet_(name) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.setFrozenRows(1);
  }
  var cols = COLS[name];
  var head = sh.getRange(1, 1, 1, cols.length).getValues()[0];
  if (head.join('|') !== cols.join('|')) sh.getRange(1, 1, 1, cols.length).setValues([cols]);
  return sh;
}

/* [G5] GEMMER ÉN RÆKKE. Kaldes fra spillet via google.script.run.
   - Kun kendte faneblade og kolonner accepteres (whitelist via COLS).
   - Tekst forkortes til 300 tegn.
   - Tekst der starter med = + - @ får en ' foran, så ingen kan sende en formel ind
     i regnearket (beskyttelse mod "formula injection").
   - LockService sikrer, at to spillere, der svarer samtidig, ikke overskriver
     hinandens række. */
function logRow(name, row) {
  if (!COLS[name]) throw new Error('Ukendt ark');
  var values = COLS[name].map(function (c) {
    var v = row ? row[c] : '';
    if (v === undefined || v === null) return '';
    if (typeof v === 'number') return v;
    v = String(v).slice(0, 300);
    if (/^[=+\-@]/.test(v)) v = "'" + v;
    return v;
  });
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try { sheet_(name).appendRow(values); } finally { lock.releaseLock(); }
  return true;
}

/* [G6] rows_ læser et faneblad og laver hver række om til et objekt {kolonne: værdi}.
   getData returnerer alle tre faneblade, men kun med den rigtige nøgle. */
function rows_(name) {
  var v = sheet_(name).getDataRange().getValues();
  var head = v.shift() || [];
  return v.map(function (r) {
    var o = {};
    head.forEach(function (c, i) { var x = r[i]; o[c] = (x instanceof Date) ? x.toISOString() : x; });
    return o;
  });
}

function getData(key) {
  if (key !== KEY) throw new Error('Forkert nøgle');
  var res = {};
  Object.keys(COLS).forEach(function (n) { res[n] = rows_(n); });
  return res;
}

/* [G7] TOP 5. Grupperer alle valg pr. spiller og tæller:
   korrekte = valg der førte videre, spil = antal forskellige vagter,
   gennemfoert = antal hele vagter. Sorteres efter korrekte svar.
   Returnerer kun kaldenavn og tal, ingen profiloplysninger. */
function getHighscore() {
  var by = {};
  rows_('Valg').forEach(function (r) {
    if (!r.player) return;
    var p = by[r.player] || (by[r.player] = { nick: r.nick || '?', games: {}, korrekte: 0, gennemfoert: 0 });
    p.games[r.game || ('a' + r.attempt)] = 1;
    if (r.outcome === 'videre') p.korrekte++;
  });
  rows_('Slutninger').forEach(function (r) { if (by[r.player]) by[r.player].gennemfoert++; });
  return Object.keys(by).map(function (k) {
    var p = by[k];
    return { nick: String(p.nick).slice(0, 24), spil: Object.keys(p.games).length, korrekte: p.korrekte, gennemfoert: p.gennemfoert };
  }).sort(function (a, b) { return b.korrekte - a.korrekte || b.gennemfoert - a.gennemfoert || a.spil - b.spil; }).slice(0, 5);
}

/* [G8] Hjælpefunktion, der køres manuelt fra editoren for at oprette/opdatere fanebladene. */
function opsaetArk() {
  Object.keys(COLS).forEach(function (n) { sheet_(n); });
}
