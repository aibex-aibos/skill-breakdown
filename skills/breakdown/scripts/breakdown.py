#!/usr/bin/env python3
"""breakdown.py — führt den Ablauf, zählt und prüft Zerlegungen des Skills breakdown (skill-breakdown).

Befehle (Spec 04 im Konzeptprojekt MSZ-Zerlegung-Beitrag):
  split    <beitrag> <zieldatei> [--fassung N] [--katalog A,B] [--zweiter] [--einheit K] [--seiten N]
  next     <arbeitsordner>
  submit   <arbeitsordner>
  status   <arbeitsordner>
  assemble <arbeitsordner> [<ausgabe>]
  hash     <beitrag>
  check    <zerlegung> <beitrag> <fassung>
  renumber <arbeitsdatei>
  profile  <zerlegung> <beitrag> [--seiten N] [--ende GRUND]
  compare  <zerlegung> <zweiter-durchlauf>

Nur Python 3 ab 3.9 mit der Standardbibliothek. Exit-Codes: 0 erfolgreich,
1 Fehler in Argumenten oder beim Lesen und Schreiben, 2 Format verletzt,
3 Teilaufgabe nach drei zurückgewiesenen Abgaben abgebrochen.
"""

import datetime
import hashlib
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from decimal import Decimal, ROUND_HALF_UP

ARTEN = ["Begriff", "Beschreibung", "Vorgehen", "Empfehlung", "Erfahrung",
         "Messwert", "Kritik", "Bewertung", "Offenes", "Ziel"]
BELEGE = ["beobachtet", "Quelle (genannt)", "begründet", "Quelle selbst", "unbelegt"]
REICHWEITEN = ["Einzelfall", "übertragbar"]
BELEGT = {"beobachtet", "Quelle (genannt)", "begründet"}
OHNE_GEHALT = {"Bewertung", "Offenes"}
STAMP = re.compile(r"^\[\d\d:\d\d:\d\d\]\s*")
MAX_EBENEN = 8


class FormatFehler(Exception):
    pass


class Fehler(Exception):
    pass


class Abbruch(Exception):
    pass


# ---------------------------------------------------------------- Hilfen

def lesen(pfad):
    try:
        with open(pfad, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise Fehler("kann %s nicht lesen: %s" % (pfad, e.strerror))


def schreiben(pfad, text):
    try:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise Fehler("kann %s nicht schreiben: %s" % (pfad, e.strerror))


def prozent(teil, ganz):
    """Anteil in Prozent, eine Nachkommastelle, halb auf, Dezimalkomma."""
    if ganz == 0:
        return "–"
    wert = (Decimal(teil) * 100 / Decimal(ganz)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return ("%s %%" % wert).replace(".", ",")


def prozentwert(teil, ganz):
    if ganz == 0:
        return Decimal(0)
    return (Decimal(teil) * 100 / Decimal(ganz)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def zahl(wert):
    return str(wert.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)).replace(".", ",")


def zellen(zeile):
    """Teilt eine Tabellenzeile `| a | b |` an nicht maskierten Strichen."""
    inhalt = zeile.strip()
    if inhalt.startswith("|"):
        inhalt = inhalt[1:]
    if inhalt.endswith("|") and not inhalt.endswith("\\|"):
        inhalt = inhalt[:-1]
    teile = re.split(r"(?<!\\)\|", inhalt)
    return [t.strip().replace("\\|", "|") for t in teile]


def maskieren(text):
    return text.replace("|", "\\|")


def felder(zeile):
    """Teilt eine Zeile der Arbeitsdatei an ` | `, nicht an `\\|`."""
    teile = re.split(r"(?<!\\) \| ", zeile.rstrip("\n"))
    return [t.strip().replace("\\|", "|") for t in teile]


def art_des_beitrags(pfad, text):
    if pfad.lower().endswith(".pdf"):
        return "pdf"
    for zeile in text.splitlines():
        if STAMP.match(zeile):
            return "transkript"
    return "markdown"


# ---------------------------------------------------------------- Wörter

WORT = re.compile(r"[^\W_]", re.UNICODE)


def woerter_zaehlen(text, art):
    zeilen = text.splitlines()
    if art == "transkript":
        rein = [STAMP.sub("", z) for z in zeilen if STAMP.match(z)]
    else:
        rein = []
        im_kopf = True
        im_code = False
        for i, z in enumerate(zeilen):
            if z.strip().startswith("```"):
                im_code = not im_code
                continue
            if im_code:
                continue
            if im_kopf:
                if (i == 0 and z.startswith("# ")) or re.match(r"^\*\*[^*]+:\*\*", z) or not z.strip():
                    continue
                im_kopf = False
            rein.append(z)
    anzahl = 0
    for z in rein:
        z = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", z)
        z = re.sub(r"https?://\S+", " ", z)
        z = re.sub(r"[#*_`>|]", " ", z)
        anzahl += sum(1 for w in z.split() if WORT.search(w))
    return anzahl


# ---------------------------------------------------------------- Zerlegung lesen

class Zerlegung:
    def __init__(self, pfad):
        self.pfad = pfad
        self.text = lesen(pfad)
        self.zeilen = self.text.splitlines()
        self.kopf = self._kopf()
        self.aussagen = []
        self.rahmen = []
        self.ebenen = OrderedDict()
        self.vorlaeufig_def = {}
        self._tabellen()

    def _kopf(self):
        kopf = OrderedDict()
        for z in self.zeilen:
            if z.startswith("## "):
                break
            m = re.match(r"^\*\*([^*]+):\*\*\s*(.*)$", z)
            if m:
                kopf[m.group(1)] = m.group(2).strip()
        return kopf

    def zusatzarten(self):
        wert = self.kopf.get("Katalog-Erweiterung", "keine")
        if not wert or wert == "keine":
            return set()
        return {a.strip() for a in wert.split(",") if a.strip()}

    def _tabellen(self):
        abschnitt = None
        ebene = None
        for nr, z in enumerate(self.zeilen, 1):
            if z.startswith("## "):
                abschnitt = z[3:].strip()
                ebene = None
                continue
            if z.startswith("### ") and abschnitt == "Meta-Ebenen":
                m = re.match(r"^### Ebene (\d+)\s*$", z)
                if not m:
                    raise FormatFehler("Zeile %d: Überschrift einer Meta-Ebene muss „### Ebene <k>“ sein" % nr)
                ebene = int(m.group(1))
                self.ebenen[ebene] = []
                continue
            if not z.startswith("|") or re.match(r"^\|\s*:?-", z):
                continue
            folgende = self.zeilen[nr] if nr < len(self.zeilen) else ""
            if re.match(r"^\|\s*:?-", folgende):
                continue  # Kopfzeile einer Tabelle
            c = zellen(z)
            if abschnitt == "Aussagen":
                if len(c) != 8:
                    raise FormatFehler("Zeile %d: Aussage braucht 8 Felder, hat %d" % (nr, len(c)))
                self.aussagen.append((nr, c))
            elif abschnitt == "Rahmen":
                if len(c) != 3:
                    raise FormatFehler("Zeile %d: Rahmen-Zeile braucht 3 Felder, hat %d" % (nr, len(c)))
                self.rahmen.append((nr, c))
            elif abschnitt == "Meta-Ebenen" and ebene is not None:
                if len(c) != 4:
                    raise FormatFehler("Zeile %d: Meta-Aussage braucht 4 Felder, hat %d" % (nr, len(c)))
                self.ebenen[ebene].append((nr, c))
            elif abschnitt == "Vorläufige Arten":
                if len(c) >= 2:
                    self.vorlaeufig_def[c[0]] = c[1]

    def pruefen(self):
        bekannt = set(ARTEN) | self.zusatzarten()
        for nr, c in self.aussagen:
            kenn, _, _, _, art, beleg, reich, zeichen = c
            if not re.match(r"^A\d{3,}$", kenn):
                raise FormatFehler("Zeile %d: Kennung %r" % (nr, kenn))
            if not re.match(r"^V\d{2,}$", c[1]):
                raise FormatFehler("Zeile %d: Sachverhalt %r" % (nr, c[1]))
            if art not in bekannt and "vorläufig" not in zeichen:
                raise FormatFehler("Zeile %d: unbekannte Art %r" % (nr, art))
            if beleg not in BELEGE:
                raise FormatFehler("Zeile %d: unbekannter Beleg %r" % (nr, beleg))
            if reich not in REICHWEITEN:
                raise FormatFehler("Zeile %d: unbekannte Reichweite %r" % (nr, reich))
        unten = {c[0] for _, c in self.aussagen}
        for k, liste in self.ebenen.items():
            if k > MAX_EBENEN:
                raise FormatFehler("Ebene %d: mehr als %d Meta-Ebenen" % (k, MAX_EBENEN))
            for nr, c in liste:
                kenn, stuetzen, _, art = c
                if not re.match(r"^M%d\.\d{2,}$" % k, kenn):
                    raise FormatFehler("Zeile %d: Kennung %r passt nicht zu Ebene %d" % (nr, kenn, k))
                s = [x.strip() for x in stuetzen.split(",") if x.strip()]
                if len(s) < 2:
                    raise FormatFehler("Zeile %d: %s braucht mindestens zwei Stützen" % (nr, kenn))
                fehlend = [x for x in s if x not in unten]
                if fehlend:
                    raise FormatFehler("Zeile %d: Stützen ohne Aussage darunter: %s" % (nr, ", ".join(fehlend)))
                if art not in bekannt and art != "Thema":
                    raise FormatFehler("Zeile %d: unbekannte Art %r" % (nr, art))
            unten = {c[0] for _, c in liste if c[3] != "Thema"}


# ---------------------------------------------------------------- Abschnitte ersetzen

def abschnitt_setzen(text, titel, inhalt, vor=None):
    """Ersetzt `## titel` bis zur nächsten `## `-Überschrift; fehlt er, wird er vor `vor` eingefügt.
    Ist inhalt None, wird der Abschnitt entfernt."""
    zeilen = text.split("\n")
    start = None
    for i, z in enumerate(zeilen):
        if z.strip() == "## " + titel:
            start = i
            break
    if start is not None:
        ende = len(zeilen)
        for j in range(start + 1, len(zeilen)):
            if zeilen[j].startswith("## "):
                ende = j
                break
        neu = [] if inhalt is None else ["## " + titel, ""] + inhalt.rstrip("\n").split("\n") + [""]
        zeilen = zeilen[:start] + neu + zeilen[ende:]
        return "\n".join(zeilen)
    if inhalt is None:
        return text
    pos = len(zeilen)
    if vor:
        for v in vor:
            for i, z in enumerate(zeilen):
                if z.strip() == "## " + v:
                    pos = i
                    break
            if pos != len(zeilen):
                break
    block = ["## " + titel, ""] + inhalt.rstrip("\n").split("\n") + [""]
    zeilen = zeilen[:pos] + block + zeilen[pos:]
    return "\n".join(zeilen)


def kopf_setzen(text, feld, wert):
    zeilen = text.split("\n")
    muster = re.compile(r"^\*\*%s:\*\*" % re.escape(feld))
    letzte = None
    for i, z in enumerate(zeilen):
        if z.startswith("## "):
            break
        if muster.match(z):
            zeilen[i] = "**%s:** %s" % (feld, wert)
            return "\n".join(zeilen)
        if re.match(r"^\*\*[^*]+:\*\*", z):
            letzte = i
    if letzte is None:
        raise Fehler("kein Kopf in der Zerlegung")
    zeilen.insert(letzte + 1, "**%s:** %s" % (feld, wert))
    return "\n".join(zeilen)


def tabelle(kopf, zeilen):
    aus = ["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
    for z in zeilen:
        aus.append("| " + " | ".join(maskieren(str(x)) for x in z) + " |")
    return "\n".join(aus)


# ---------------------------------------------------------------- Befehle

def cmd_hash(args):
    if len(args) != 1:
        raise Fehler("hash <beitrag>")
    try:
        with open(args[0], "rb") as f:
            print(hashlib.sha256(f.read()).hexdigest()[:12])
    except OSError as e:
        raise Fehler("kann %s nicht lesen: %s" % (args[0], e.strerror))


def cmd_check(args):
    if len(args) != 3:
        raise Fehler("check <zerlegung> <beitrag> <fassung>")
    zerl, beitrag, fassung = args
    if not os.path.exists(zerl):
        print("fehlt")
        return
    z = Zerlegung(zerl)
    m = re.search(r"Fassung\s+(\S+)", z.kopf.get("Regeln", ""))
    alt = m.group(1) if m else "?"
    if alt != str(fassung):
        print("fassung %s" % alt)
        return
    with open(beitrag, "rb") as f:
        summe = hashlib.sha256(f.read()).hexdigest()[:12]
    print("aktuell" if z.kopf.get("Prüfsumme", "") == summe else "geändert")


def cmd_renumber(args):
    if len(args) != 1:
        raise Fehler("renumber <arbeitsdatei>")
    pfad = args[0]
    eintraege = []
    for nr, z in enumerate(lesen(pfad).splitlines(), 1):
        if not z.strip():
            continue
        f = felder(z)
        if len(f) == 8:
            eintraege.append(("A", nr, f))
        elif len(f) == 4 and f[2] == "Rahmen":
            eintraege.append(("R", nr, f))
        else:
            raise FormatFehler("Zeile %d: %d Felder; erwartet 8 (Aussage) oder 4 (Rahmen)" % (nr, len(f)))
    na = sum(1 for e in eintraege if e[0] == "A")
    nr_ = sum(1 for e in eintraege if e[0] == "R")
    v_alt = OrderedDict()
    for t, _, f in eintraege:
        if t == "A" and f[1] not in v_alt:
            v_alt[f[1]] = len(v_alt) + 1
    wa, wv, wr = max(3, len(str(na))), max(2, len(str(len(v_alt)))), max(2, len(str(nr_)))
    aus, ia, ir = [], 0, 0
    for t, _, f in eintraege:
        if t == "A":
            ia += 1
            f = ["A%0*d" % (wa, ia), "V%0*d" % (wv, v_alt[f[1]])] + f[2:]
        else:
            ir += 1
            f = ["R%0*d" % (wr, ir)] + f[1:]
        aus.append(" | ".join(maskieren(x) for x in f))
    schreiben(pfad, "\n".join(aus) + "\n")
    print("Aussagen %d, Sachverhalte %d, Rahmen-Zeilen %d" % (na, len(v_alt), nr_))


def profil_inhalt(z, woerter, seiten):
    n = len(z.aussagen)
    sachverhalte = len({c[1] for _, c in z.aussagen})
    r = len(z.rahmen)
    arten = Counter(c[4] for _, c in z.aussagen)
    belege = Counter(c[5] for _, c in z.aussagen)
    reich = Counter(c[6] for _, c in z.aussagen)
    reihenfolge = ARTEN + sorted(a for a in arten if a not in ARTEN)
    teile = [tabelle(["Zählung", "Anzahl"], [["Aussagen", n], ["Sachverhalte", sachverhalte], ["Rahmen-Zeilen", r]])]
    teile.append("### Art\n\n" + tabelle(["Art", "Anzahl", "Anteil"],
                 [[a, arten[a], prozent(arten[a], n)] for a in reihenfolge if arten[a]]))
    teile.append("### Beleg\n\n" + tabelle(["Beleg", "Anzahl", "Anteil"],
                 [[b, belege[b], prozent(belege[b], n)] for b in BELEGE if belege[b]]))
    teile.append("### Reichweite\n\n" + tabelle(["Reichweite", "Anzahl", "Anteil"],
                 [[x, reich[x], prozent(reich[x], n)] for x in REICHWEITEN if reich[x]]))
    nenner = n - belege["Quelle selbst"]
    belegt = sum(belege[b] for b in BELEGT)
    gehalt = n - sum(arten[a] for a in OHNE_GEHALT)
    if seiten is not None:
        dichte = (zahl(Decimal(n) / Decimal(seiten)) + " je Seite") if seiten else "–"
        grund = "%d Seiten" % seiten
    else:
        dichte = (zahl(Decimal(n) * 1000 / Decimal(woerter)) + " je 1000 Wörter") if woerter else "–"
        grund = "%d Wörter" % woerter
    masse = [
        ["Belegquote", prozent(belegt, nenner), "%d von %d Aussagen ohne „Quelle selbst“" % (belegt, nenner)],
        ["Gehaltsquote", prozent(gehalt, n), "%d von %d Aussagen" % (gehalt, n)],
        ["Dichte", dichte, grund],
        ["Rahmenanteil", prozent(r, n + r), "%d von %d Zeilen" % (r, n + r)],
    ]
    teile.append("### Maße\n\n" + tabelle(["Maß", "Wert", "Grundlage"], masse))
    werte = {"Belegquote": masse[0][1], "Gehaltsquote": masse[1][1], "Dichte": dichte, "Rahmenanteil": masse[3][1]}
    return "\n\n".join(teile), (n, sachverhalte, r, werte)


def cmd_profile(args):
    seiten, ende, rest = None, None, []
    i = 0
    while i < len(args):
        if args[i] == "--seiten" and i + 1 < len(args):
            try:
                seiten = int(args[i + 1])
            except ValueError:
                raise Fehler("--seiten braucht eine Zahl")
            i += 2
        elif args[i] == "--ende" and i + 1 < len(args):
            ende = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    if len(rest) != 2:
        raise Fehler("profile <zerlegung> <beitrag> [--seiten N] [--ende GRUND]")
    zerl, beitrag = rest
    z = Zerlegung(zerl)
    z.pruefen()
    art = art_des_beitrags(beitrag, "" if beitrag.lower().endswith(".pdf") else lesen(beitrag))
    if art == "pdf" and seiten is None:
        raise Fehler("bei einem PDF braucht profile --seiten")
    woerter = 0 if art == "pdf" else woerter_zaehlen(lesen(beitrag), art)
    inhalt, (n, v, r, werte) = profil_inhalt(z, woerter, seiten if art == "pdf" else None)
    text = z.text
    text = abschnitt_setzen(text, "Wissensprofil", inhalt, vor=["Vorläufige Arten", "Unsichere Stellen", "Aussagen"])
    vorl = OrderedDict()
    for _, c in z.aussagen:
        if "vorläufig" in c[7]:
            vorl.setdefault(c[4], []).append(c[0])
    text = abschnitt_setzen(text, "Vorläufige Arten",
                            tabelle(["Name", "Definition", "Aussagen"],
                                    [[a, z.vorlaeufig_def.get(a, ""), ", ".join(k)] for a, k in vorl.items()])
                            if vorl else None, vor=["Unsichere Stellen", "Aussagen"])
    unsicher = []
    for _, c in z.aussagen:
        m = re.search(r"unsicher:\s*(.+?)(?:;\s*vorläufig)?$", c[7])
        if m:
            unsicher.append([c[0], m.group(1).strip()])
        elif "unsicher" in c[7]:
            unsicher.append([c[0], ""])
    text = abschnitt_setzen(text, "Unsichere Stellen",
                            tabelle(["Aussage", "Wortlaut des Originals"], unsicher) if unsicher else None,
                            vor=["Aussagen"])
    if z.ebenen:
        text = meta_zaehlen(text, z)
        alt = re.search(r"\(Ende:\s*([^)]+)\)", z.kopf.get("Meta-Ebenen", ""))
        grund = ende or (alt.group(1) if alt else None)
        if not grund:
            raise Fehler("Meta-Ebenen vorhanden: profile braucht --ende <Grund>")
        text = kopf_setzen(text, "Meta-Ebenen", "%d (Ende: %s)" % (len(z.ebenen), grund))
    schreiben(zerl, text)
    print("Aussagen %d, Sachverhalte %d, Rahmen-Zeilen %d; Belegquote %s, Gehaltsquote %s, Dichte %s, Rahmenanteil %s"
          % (n, v, r, werte["Belegquote"], werte["Gehaltsquote"], werte["Dichte"], werte["Rahmenanteil"]))


def meta_zaehlen(text, z):
    unten = [c[0] for _, c in z.aussagen]
    zeilen = text.split("\n")
    for k, liste in z.ebenen.items():
        gestuetzt = set()
        for _, c in liste:
            gestuetzt.update(x.strip() for x in c[1].split(",") if x.strip())
        themen = sum(1 for _, c in liste if c[3] == "Thema")
        nicht = sum(1 for u in unten if u not in gestuetzt)
        satz = "Meta-Aussagen: %d, davon Themen: %d; nicht aufgenommen aus der Ebene darunter: %d" % (len(liste), themen, nicht)
        for i, zl in enumerate(zeilen):
            if zl.strip() == "### Ebene %d" % k:
                j = i + 1
                while j < len(zeilen) and not zeilen[j].strip():
                    j += 1
                if j < len(zeilen) and zeilen[j].startswith("Meta-Aussagen:"):
                    zeilen[j] = satz
                else:
                    zeilen[i + 1:i + 1] = ["", satz]
                break
        unten = [c[0] for _, c in liste if c[3] != "Thema"]
    return "\n".join(zeilen)


def cmd_compare(args):
    if len(args) != 2:
        raise Fehler("compare <zerlegung> <zweiter-durchlauf>")
    zerl, zweiter = args
    z = Zerlegung(zerl)
    z.pruefen()
    eins = [c for _, c in z.aussagen]
    zwei = []
    for nr, zl in enumerate(lesen(zweiter).splitlines(), 1):
        if not zl.strip():
            continue
        f = felder(zl)
        if len(f) == 8:
            zwei.append(f)
        elif not (len(f) == 4 and f[2] == "Rahmen"):
            raise FormatFehler("%s, Zeile %d: %d Felder" % (zweiter, nr, len(f)))

    def erste(c):
        return c[2].split(",")[0].strip()

    def eindeutig(liste):
        z_ = Counter(erste(c) for c in liste)
        return {erste(c): c for c in liste if z_[erste(c)] == 1}

    e1, e2 = eindeutig(eins), eindeutig(zwei)
    gemeinsam = [k for k in e1 if k in e2]
    m = len(gemeinsam)
    art = sum(1 for k in gemeinsam if e1[k][4] == e2[k][4])
    beleg = sum(1 for k in gemeinsam if e1[k][5] == e2[k][5])
    reich = sum(1 for k in gemeinsam if e1[k][6] == e2[k][6])
    a1, a2 = Counter(c[4] for c in eins), Counter(c[4] for c in zwei)
    abw = Decimal(0)
    for a in set(a1) | set(a2):
        d = abs(prozentwert(a1[a], len(eins)) - prozentwert(a2[a], len(zwei)))
        abw = max(abw, d)
    quote = prozentwert(art, m)
    stabil = m > 0 and quote >= 90 and abw <= 10
    urteil = "stabil" if stabil else "nicht stabil"
    v1, v2 = len({c[1] for c in eins}), len({c[1] for c in zwei})
    teile = [tabelle(["Merkmal", "Durchlauf 1", "Durchlauf 2"],
                     [["Aussagen", len(eins), len(zwei)], ["Sachverhalte", v1, v2]])]
    teile.append(tabelle(["Übereinstimmung", "Wert"], [
        ["zugeordnete Aussagen (gleiche erste Fundstelle)", m],
        ["gleiche Art", "%d (%s)" % (art, prozent(art, m))],
        ["gleicher Beleg", "%d (%s)" % (beleg, prozent(beleg, m))],
        ["gleiche Reichweite", "%d (%s)" % (reich, prozent(reich, m))],
        ["größte Abweichung der Anteile je Art", zahl(abw) + " Prozentpunkte"],
    ]))
    teile.append("**Urteil:** %s" % urteil)
    abweichend = [[e1[k][0], k, e1[k][4], e2[k][4]] for k in gemeinsam if e1[k][4] != e2[k][4]]
    if abweichend:
        teile.append("Stellen mit abweichender Art:\n\n" +
                     tabelle(["Aussage", "Fundstelle", "Durchlauf 1", "Durchlauf 2"], abweichend))
    text = abschnitt_setzen(z.text, "Vergleich", "\n\n".join(teile))
    text = kopf_setzen(text, "Durchläufe", "2 (mit Vergleich)")
    schreiben(zerl, text)
    print("%s: gleiche Art %s, größte Abweichung %s Prozentpunkte" % (urteil, prozent(art, m), zahl(abw)))


# ---------------------------------------------------------------- Ablauf führen (Spec 04, *Ablauf führen*)

EINHEIT_WOERTER = 300
KLEIN_WOERTER = 100
GRUPPE_EINSTUFEN = 20
GRUPPE_ABGLEICH = 10
SCHWELLE_KANDIDAT = Decimal("0.5")
MAX_FEHLVERSUCHE = 3
FUNKTIONSWOERTER = set("""
aber alle allem allen aller alles also auch auf aus bei beim beide beiden bereits bis bisher dabei dadurch
dafür dagegen daher damit danach dann daran darauf darin darum darüber dass dein deine dem den denen denn der
deren des dessen dich dies diese diesem diesen dieser dieses doch dort durch eben eine einem einen einer eines
einige einmal etwa etwas euch euer für gegen gibt habe haben hat hatte hätte hier hinter ihm ihn ihnen ihr ihre
ihrem ihren ihrer immer indem jede jedem jeden jeder jedes jedoch jene kann kein keine keinem keinen keiner können
könnte machen macht mehr mein meine mich mit muss müssen nach nicht nichts noch nur oder ohne schon sehr sein
seine seinem seinen seiner seit selbst sich sie sind soll sollen sollte sondern sowie über ohne unter viel viele
vom von vor wann warum was weil welche welchem welchen welcher welches wenn werden wer wie wieder will wird wo
wurde wurden würde zum zur zwar zwischen this that with from have what when they them their there about into
""".split())
DURCHGAENGE = ["zerlegen", "einstufen", "abgleichen"]
NAMEN = {"zerlegen": "Zerlegen", "einstufen": "Einstufen", "abgleichen": "Abgleichen"}


def projekt_von(pfad):
    d = os.path.dirname(os.path.abspath(pfad))
    while True:
        if os.path.isdir(os.path.join(d, "@")):
            return d
        oben = os.path.dirname(d)
        if oben == d:
            return None
        d = oben


def pruefsumme(pfad):
    try:
        with open(pfad, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError as e:
        raise Fehler("kann %s nicht lesen: %s" % (pfad, e.strerror))


def pdf_seiten(pfad):
    try:
        with open(pfad, "rb") as f:
            daten = f.read()
    except OSError as e:
        raise Fehler("kann %s nicht lesen: %s" % (pfad, e.strerror))
    return len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", daten))


def zeile_woerter(z):
    z = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", z)
    z = re.sub(r"https?://\S+", " ", z)
    z = re.sub(r"[#*_`>|]", " ", z)
    return sum(1 for w in z.split() if WORT.search(w))


def einheiten_transkript(text):
    einheiten, akt, n = [], [], 0
    for z in text.splitlines():
        if not STAMP.match(z):
            continue
        akt.append(z)
        n += zeile_woerter(STAMP.sub("", z))
        if n >= EINHEIT_WOERTER:
            einheiten.append(akt)
            akt, n = [], 0
    if akt:
        einheiten.append(akt)
    aus = []
    for zeilen in einheiten:
        marken = [re.match(r"^\[(\d\d:\d\d:\d\d)\]", z).group(1) for z in zeilen]
        bereich = marken[0] if len(marken) == 1 else "%s–%s" % (marken[0], marken[-1])
        aus.append({"bereich": bereich, "marken": marken, "text": "\n".join(zeilen)})
    return aus


def einheiten_markdown(text):
    zeilen = text.splitlines()
    nummern = []  # (nr, zeile, woerter, ueberschrift)
    im_kopf, im_code = True, False
    for i, z in enumerate(zeilen, 1):
        if im_kopf:
            if (i == 1 and z.startswith("# ")) or re.match(r"^\*\*[^*]+:\*\*", z) or not z.strip():
                continue
            im_kopf = False
        if z.strip().startswith("```"):
            im_code = not im_code
            nummern.append((i, z, 0, False))
            continue
        ueber = (not im_code) and bool(re.match(r"^#{1,6}\s", z))
        nummern.append((i, z, 0 if im_code else zeile_woerter(z), ueber))
    abschnitte, akt = [], []
    for e in nummern:
        if e[3] and akt:
            abschnitte.append(akt)
            akt = []
        akt.append(e)
    if akt:
        abschnitte.append(akt)
    teile = []
    for ab in abschnitte:
        if sum(e[2] for e in ab) <= EINHEIT_WOERTER:
            teile.append(ab)
            continue
        absaetze, a = [], []
        for e in ab:
            a.append(e)
            if not e[1].strip():
                absaetze.append(a)
                a = []
        if a:
            absaetze.append(a)
        stueck = []
        for a in absaetze:
            w = sum(e[2] for e in a)
            if stueck and sum(e[2] for e in stueck) + w > EINHEIT_WOERTER:
                teile.append(stueck)
                stueck = []
            stueck = stueck + a
        if stueck:
            teile.append(stueck)
    teile = [t for t in teile if any(e[1].strip() for e in t)]
    zusammen, i = [], 0
    while i < len(teile):
        t = teile[i]
        while (sum(e[2] for e in t) < KLEIN_WOERTER and i + 1 < len(teile)
               and sum(e[2] for e in t) + sum(e[2] for e in teile[i + 1]) <= EINHEIT_WOERTER):
            i += 1
            t = t + teile[i]
        zusammen.append(t)
        i += 1
    aus = []
    for t in zusammen:
        while t and not t[-1][1].strip():
            t = t[:-1]
        von, bis = t[0][0], t[-1][0]
        bereich = "Z. %d" % von if von == bis else "Z. %d–%d" % (von, bis)
        aus.append({"bereich": bereich, "von": von, "bis": bis,
                    "text": "\n".join("Z. %d: %s" % (e[0], e[1]) for e in t)})
    return aus


def arbeitsordner_fuer(zieldatei, zweiter):
    name = os.path.splitext(os.path.basename(zieldatei))[0] + (" — 2" if zweiter else "")
    return os.path.join(os.path.dirname(os.path.abspath(zieldatei)), ".arbeit", name)


def zustand_lesen(ordner):
    pfad = os.path.join(ordner, "zustand.json")
    if not os.path.exists(pfad):
        raise Fehler("kein Arbeitsordner: %s fehlt" % pfad)
    try:
        return json.loads(lesen(pfad))
    except ValueError:
        raise Fehler("%s ist kein gültiges JSON" % pfad)


def zustand_schreiben(ordner, z):
    schreiben(os.path.join(ordner, "zustand.json"), json.dumps(z, ensure_ascii=False, indent=1) + "\n")


def gruppen(liste, groesse):
    return [liste[i:i + groesse] for i in range(0, len(liste), groesse)]


def aufgaben(z, phase):
    if phase == "zerlegen":
        return len(z["einheiten"])
    if phase == "einstufen":
        return len(gruppen(z["aussagen"], GRUPPE_EINSTUFEN))
    if phase == "abgleichen":
        return len(gruppen(z["kandidaten"], GRUPPE_ABGLEICH))
    return 0


def offene_aufgabe(z):
    """(phase, index) der offenen Teilaufgabe oder ("fertig", 0)."""
    phase, idx = z["phase"], z["index"]
    while phase != "fertig" and idx >= aufgaben(z, phase):
        phase = DURCHGAENGE[DURCHGAENGE.index(phase) + 1] if phase != "abgleichen" else "fertig"
        idx = 0
        if phase == "abgleichen":
            z["kandidaten"] = kandidaten(z)
    z["phase"], z["index"] = phase, idx
    return phase, idx


def abgabe_datei(ordner, phase, idx):
    kurz = {"zerlegen": "E", "einstufen": "G", "abgleichen": "K"}[phase]
    return os.path.join(ordner, "abgaben", "%s-%s%02d.txt" % (phase, kurz, idx + 1))


def inhaltswoerter(text):
    return {w for w in re.findall(r"[^\W\d_]+", text.lower()) if len(w) >= 4 and w not in FUNKTIONSWOERTER}


def kandidaten(z):
    a = z["aussagen"]
    w = [inhaltswoerter(x["text"]) for x in a]
    paare = []
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i]["einheit"] == a[j]["einheit"] or not w[i] or not w[j]:
                continue
            if Decimal(len(w[i] & w[j])) / Decimal(len(w[i] | w[j])) >= SCHWELLE_KANDIDAT:
                paare.append([i, j])
    return paare


def cmd_split(args):
    opt = {"--fassung": None, "--katalog": "", "--einheit": None, "--seiten": None}
    zweiter, rest, i = False, [], 0
    while i < len(args):
        if args[i] in opt and i + 1 < len(args):
            opt[args[i]] = args[i + 1]
            i += 2
        elif args[i] == "--zweiter":
            zweiter = True
            i += 1
        else:
            rest.append(args[i])
            i += 1
    if len(rest) != 2:
        raise Fehler("split <beitrag> <zieldatei> [--fassung N] [--katalog A,B] [--zweiter] [--einheit K] [--seiten N]")
    beitrag, ziel = os.path.abspath(rest[0]), os.path.abspath(rest[1])
    if not os.path.isfile(beitrag):
        raise Fehler("Beitrag fehlt: %s" % beitrag)
    fassung = opt["--fassung"] or "7"
    summe = pruefsumme(beitrag)
    ordner = arbeitsordner_fuer(ziel, zweiter)
    if os.path.exists(os.path.join(ordner, "zustand.json")):
        z = zustand_lesen(ordner)
        if z["pruefsumme"] != summe or str(z["fassung"]) != str(fassung):
            raise Fehler("Arbeitsordner %s gehört zu einem anderen Stand (Prüfsumme oder Fassung); erst entfernen" % ordner)
        phase, idx = offene_aufgabe(z)
        zustand_schreiben(ordner, z)
        print("Fortsetzen: %s" % (aufgabe_titel(z, phase, idx) if phase != "fertig" else "fertig"))
        return
    text = "" if beitrag.lower().endswith(".pdf") else lesen(beitrag)
    art = art_des_beitrags(beitrag, text)
    if art == "pdf":
        seiten = int(opt["--seiten"]) if opt["--seiten"] else pdf_seiten(beitrag)
        if not seiten:
            raise Fehler("Seitenzahl des PDF nicht gefunden; split mit --seiten <n> aufrufen")
        einheiten = [{"bereich": "S. %d" % s, "seite": s} for s in range(1, seiten + 1)]
    elif art == "transkript":
        einheiten = einheiten_transkript(text)
    else:
        einheiten = einheiten_markdown(text)
    if not einheiten:
        raise Fehler("der Beitrag hat keinen Inhalt zum Zerlegen")
    if opt["--einheit"]:
        k = int(opt["--einheit"])
        if not 1 <= k <= len(einheiten):
            raise Fehler("--einheit %d: der Beitrag hat %d Einheiten" % (k, len(einheiten)))
        einheiten = [einheiten[k - 1]]
    for n, e in enumerate(einheiten, 1):
        e["nr"] = n
    katalog = [a.strip() for a in opt["--katalog"].split(",") if a.strip() and a.strip() != "keine"]
    os.makedirs(os.path.join(ordner, "abgaben"), exist_ok=True)
    os.makedirs(os.path.join(ordner, "einheiten"), exist_ok=True)
    for e in einheiten:
        if "text" in e:
            schreiben(os.path.join(ordner, "einheiten", "E%02d.txt" % e["nr"]), e["text"] + "\n")
    z = {"beitrag": beitrag, "zieldatei": ziel, "art": art, "pruefsumme": summe, "fassung": str(fassung),
         "katalog": katalog, "zweiter": zweiter, "einheiten": einheiten, "phase": "zerlegen", "index": 0,
         "aussagen": [], "rahmen": [], "kandidaten": [], "entscheidungen": [], "fehlversuche": {},
         "zurueckgewiesen": 0, "fortschritt": []}
    zustand_schreiben(ordner, z)
    print("Einheiten: %d (%s); Arbeitsordner: %s" % (len(einheiten), art, ordner))


def aufgabe_titel(z, phase, idx):
    n = aufgaben(z, phase)
    if phase == "zerlegen":
        return "Zerlegen · Einheit %d von %d (%s)" % (idx + 1, n, z["einheiten"][idx]["bereich"])
    if phase == "einstufen":
        return "Einstufen · Gruppe %d von %d" % (idx + 1, n)
    return "Abgleichen · Gruppe %d von %d" % (idx + 1, n)


def cmd_next(args):
    if len(args) != 1:
        raise Fehler("next <arbeitsordner>")
    ordner = os.path.abspath(args[0])
    z = zustand_lesen(ordner)
    phase, idx = offene_aufgabe(z)
    zustand_schreiben(ordner, z)
    if phase == "fertig":
        print("fertig")
        return
    datei = abgabe_datei(ordner, phase, idx)
    aus = [aufgabe_titel(z, phase, idx), ""]
    if phase == "zerlegen":
        e = z["einheiten"][idx]
        aus.append("Auftrag: Zerlege nur diese Einheit nach regeln.md, Z1 bis Z11. Nicht einstufen. "
                   "Wiederholungen innerhalb der Einheit zusammenführen; über die Einheit hinaus nichts vorwegnehmen. "
                   "Nicht im Denken vorzerlegen, was noch nicht ausgegeben ist.")
        aus.append("")
        if z["art"] == "pdf":
            aus.append("Eingabe: Lies Seite %d der Datei %s mit dem Lesewerkzeug (nur diese Seite)." % (e["seite"], z["beitrag"]))
            fund = "S. %d" % e["seite"]
        else:
            aus.append("Eingabe:")
            aus.append(e["text"])
            fund = "Zeitstempel ohne Klammern, z. B. 00:10:13" if z["art"] == "transkript" else "Z. <Zeilennummer>"
        aus += ["", "Abgabe: eine Zeile je Eintrag in %s" % datei,
                "  <Fundstellen> | <s> | <Aussage> | <Kennzeichen>",
                "  Rahmen | <Fundstelle> | <Inhalt>",
                "  Fundstellen: %s, mehrere durch Komma, die erste zuerst; <s>: Sachverhalt in dieser Einheit (s1, s2, …);" % fund,
                "  Kennzeichen: – oder unsicher: \"<Wortlaut des Originals>\"; ohne Inhalt: eine Zeile leer"]
    elif phase == "einstufen":
        gr = gruppen(z["aussagen"], GRUPPE_EINSTUFEN)[idx]
        bekannt = ARTEN + z["katalog"]
        aus.append("Auftrag: Stufe jede Aussage nach dem Katalog in regeln.md ein: Art, Beleg, Reichweite.")
        aus += ["", "Eingabe:"]
        for a in gr:
            aus.append("%s | %s | %s" % (a["id"], a["fundstellen"], a["text"]))
        aus += ["", "Abgabe: eine Zeile je Aussage in %s" % datei,
                "  <Kennung> | <Art> | <Beleg> | <Reichweite>",
                "  Art: %s; eine neue Art als vorläufig: <Name>" % ", ".join(bekannt),
                "  Beleg: %s" % ", ".join(BELEGE),
                "  Reichweite: %s" % ", ".join(REICHWEITEN)]
    else:
        gr = gruppen(z["kandidaten"], GRUPPE_ABGLEICH)[idx]
        aus.append("Auftrag: Entscheide je Paar nach regeln.md, Z3: gleich (dieselbe Behauptung, Wiederholung), "
                   "sachverhalt (verschiedene Behauptungen zum selben Sachverhalt) oder verschieden.")
        aus += ["", "Eingabe:"]
        for k, (i, j) in enumerate(gr, idx * GRUPPE_ABGLEICH + 1):
            a, b = z["aussagen"][i], z["aussagen"][j]
            aus.append("p%02d: %s (%s) %s  ⟷  %s (%s) %s" % (k, a["id"], a["fundstellen"], a["text"],
                                                          b["id"], b["fundstellen"], b["text"]))
        aus += ["", "Abgabe: eine Zeile je Paar in %s" % datei, "  <Paar> | gleich|sachverhalt|verschieden"]
    aus += ["", "Dann: breakdown.py submit \"%s\"" % ordner]
    print("\n".join(aus))


def fundstellen_pruefen(z, e, fundstellen, nr):
    teile = [f.strip() for f in fundstellen.split(",") if f.strip()]
    if not teile:
        raise FormatFehler("Zeile %d: keine Fundstelle" % nr)
    aus = []
    for f in teile:
        if z["art"] == "pdf":
            m = re.match(r"^S\.\s*(\d+)$", f)
            if not m or int(m.group(1)) != e["seite"]:
                raise FormatFehler("Zeile %d: Fundstelle %r liegt nicht in der Einheit (S. %d)" % (nr, f, e["seite"]))
            aus.append("S. %d" % e["seite"])
        elif z["art"] == "transkript":
            g = f.strip("[]")
            if g not in e["marken"]:
                raise FormatFehler("Zeile %d: Fundstelle %r liegt nicht in der Einheit (%s)" % (nr, f, e["bereich"]))
            aus.append(g)
        else:
            m = re.match(r"^Z\.\s*(\d+)$", f)
            if not m or not e["von"] <= int(m.group(1)) <= e["bis"]:
                raise FormatFehler("Zeile %d: Fundstelle %r liegt nicht in der Einheit (%s)" % (nr, f, e["bereich"]))
            aus.append("Z. %s" % m.group(1))
    return ", ".join(aus)


def abgabe_zerlegen(z, idx, text):
    e = z["einheiten"][idx]
    zeilen = [(n, l) for n, l in enumerate(text.splitlines(), 1) if l.strip()]
    if not zeilen:
        raise FormatFehler("Abgabe ist leer; ohne Inhalt eine Zeile leer schreiben")
    if len(zeilen) == 1 and zeilen[0][1].strip() == "leer":
        return [], []
    aussagen, rahmen = [], []
    for nr, l in zeilen:
        f = felder(l)
        if f[0] == "Rahmen":
            if len(f) != 3:
                raise FormatFehler("Zeile %d: Rahmen braucht 3 Felder, hat %d" % (nr, len(f)))
            rahmen.append({"einheit": e["nr"], "fundstelle": fundstellen_pruefen(z, e, f[1], nr), "inhalt": f[2]})
            continue
        if len(f) != 4:
            raise FormatFehler("Zeile %d: Aussage braucht 4 Felder (<Fundstellen> | <s> | <Aussage> | <Kennzeichen>), hat %d" % (nr, len(f)))
        fund, s, satz, zeichen = f
        if not re.match(r"^s\d+$", s):
            raise FormatFehler("Zeile %d: Sachverhalt %r; erwartet s1, s2, …" % (nr, s))
        if not satz:
            raise FormatFehler("Zeile %d: Aussage ist leer" % nr)
        if zeichen in ("-", "–", ""):
            zeichen = "–"
        elif not re.match(r'^unsicher:\s*".*"$', zeichen):
            raise FormatFehler("Zeile %d: Kennzeichen %r; erwartet – oder unsicher: \"…\"" % (nr, zeichen))
        aussagen.append({"einheit": e["nr"], "fundstellen": fundstellen_pruefen(z, e, fund, nr),
                         "s": "E%d-%s" % (e["nr"], s), "text": satz, "zeichen": zeichen})
    return aussagen, rahmen


def abgabe_einstufen(z, idx, text):
    gr = gruppen(z["aussagen"], GRUPPE_EINSTUFEN)[idx]
    ids = {a["id"] for a in gr}
    bekannt = set(ARTEN) | set(z["katalog"])
    gesehen = {}
    for nr, l in enumerate(text.splitlines(), 1):
        if not l.strip():
            continue
        f = felder(l)
        if len(f) != 4:
            raise FormatFehler("Zeile %d: braucht 4 Felder (<Kennung> | <Art> | <Beleg> | <Reichweite>), hat %d" % (nr, len(f)))
        kenn, art, beleg, reich = f
        if kenn not in ids:
            raise FormatFehler("Zeile %d: Kennung %r gehört nicht zu dieser Gruppe" % (nr, kenn))
        if kenn in gesehen:
            raise FormatFehler("Zeile %d: Kennung %s doppelt" % (nr, kenn))
        vorl = False
        m = re.match(r"^vorläufig:\s*(.+)$", art)
        if m:
            art, vorl = m.group(1).strip(), True
        elif art not in bekannt:
            raise FormatFehler("Zeile %d: unbekannte Art %r" % (nr, art))
        if beleg not in BELEGE:
            raise FormatFehler("Zeile %d: unbekannter Beleg %r" % (nr, beleg))
        if reich not in REICHWEITEN:
            raise FormatFehler("Zeile %d: unbekannte Reichweite %r" % (nr, reich))
        gesehen[kenn] = (art, beleg, reich, vorl)
    fehlend = [a["id"] for a in gr if a["id"] not in gesehen]
    if fehlend:
        raise FormatFehler("es fehlen Kennungen: %s" % ", ".join(fehlend))
    return gesehen


def abgabe_abgleichen(z, idx, text):
    erwartet = ["p%02d" % k for k in range(idx * GRUPPE_ABGLEICH + 1,
                                           idx * GRUPPE_ABGLEICH + len(gruppen(z["kandidaten"], GRUPPE_ABGLEICH)[idx]) + 1)]
    gesehen = {}
    for nr, l in enumerate(text.splitlines(), 1):
        if not l.strip():
            continue
        f = felder(l)
        if len(f) != 2:
            raise FormatFehler("Zeile %d: braucht 2 Felder (<Paar> | <Entscheidung>), hat %d" % (nr, len(f)))
        if f[0] not in erwartet:
            raise FormatFehler("Zeile %d: Paar %r gehört nicht zu dieser Gruppe" % (nr, f[0]))
        if f[0] in gesehen:
            raise FormatFehler("Zeile %d: Paar %s doppelt" % (nr, f[0]))
        if f[1] not in ("gleich", "sachverhalt", "verschieden"):
            raise FormatFehler("Zeile %d: Entscheidung %r; erwartet gleich, sachverhalt oder verschieden" % (nr, f[1]))
        gesehen[f[0]] = f[1]
    fehlend = [p for p in erwartet if p not in gesehen]
    if fehlend:
        raise FormatFehler("es fehlen Paare: %s" % ", ".join(fehlend))
    return gesehen


def cmd_submit(args):
    if len(args) != 1:
        raise Fehler("submit <arbeitsordner>")
    ordner = os.path.abspath(args[0])
    z = zustand_lesen(ordner)
    phase, idx = offene_aufgabe(z)
    if phase == "fertig":
        raise Fehler("keine offene Teilaufgabe; weiter mit assemble")
    datei = abgabe_datei(ordner, phase, idx)
    schluessel = os.path.basename(datei)
    try:
        if not os.path.exists(datei):
            raise FormatFehler("Abgabedatei fehlt: %s" % datei)
        text = lesen(datei)
        if phase == "zerlegen":
            neu, rahmen = abgabe_zerlegen(z, idx, text)
            start = len(z["aussagen"])
            for k, a in enumerate(neu, start + 1):
                a["id"] = "a%03d" % k
            z["aussagen"] += neu
            z["rahmen"] += rahmen
            zeile = "Zerlegen %d/%d: %d Aussagen, %d Rahmen; zusammen %d Aussagen" % (
                idx + 1, aufgaben(z, phase), len(neu), len(rahmen), len(z["aussagen"]))
        elif phase == "einstufen":
            werte = abgabe_einstufen(z, idx, text)
            for a in z["aussagen"]:
                if a["id"] in werte:
                    a["art"], a["beleg"], a["reich"], vorl = werte[a["id"]]
                    if vorl and "vorläufig" not in a["zeichen"]:
                        a["zeichen"] = "vorläufig" if a["zeichen"] == "–" else a["zeichen"] + "; vorläufig"
            fertig = sum(1 for a in z["aussagen"] if "art" in a)
            zeile = "Einstufen %d/%d: %d Aussagen eingestuft; zusammen %d von %d" % (
                idx + 1, aufgaben(z, phase), len(werte), fertig, len(z["aussagen"]))
        else:
            ent = abgabe_abgleichen(z, idx, text)
            for p, wert in ent.items():
                i, j = z["kandidaten"][int(p[1:]) - 1]
                z["entscheidungen"].append([i, j, wert])
            c = Counter(ent.values())
            zeile = "Abgleichen %d/%d: %d gleich, %d Sachverhalt, %d verschieden" % (
                idx + 1, aufgaben(z, phase), c["gleich"], c["sachverhalt"], c["verschieden"])
    except FormatFehler as e:
        z["fehlversuche"][schluessel] = z["fehlversuche"].get(schluessel, 0) + 1
        z["zurueckgewiesen"] += 1
        zustand_schreiben(ordner, z)
        if z["fehlversuche"][schluessel] >= MAX_FEHLVERSUCHE:
            raise Abbruch("%s nach %d zurückgewiesenen Abgaben abgebrochen; zuletzt: %s"
                          % (aufgabe_titel(z, phase, idx), MAX_FEHLVERSUCHE, e))
        raise FormatFehler("%s zurückgewiesen (%d von %d): %s" % (
            aufgabe_titel(z, phase, idx), z["fehlversuche"][schluessel], MAX_FEHLVERSUCHE, e))
    z["index"] = idx + 1
    z["fortschritt"].append(zeile)
    naechste, nidx = offene_aufgabe(z)
    if naechste != phase:
        zeile += "; weiter: %s" % ("assemble" if naechste == "fertig" else "%s (%d)" % (NAMEN[naechste], aufgaben(z, naechste)))
    zustand_schreiben(ordner, z)
    print(zeile)


def cmd_status(args):
    if len(args) != 1:
        raise Fehler("status <arbeitsordner>")
    z = zustand_lesen(os.path.abspath(args[0]))
    phase, idx = offene_aufgabe(z)
    for p in DURCHGAENGE:
        n = aufgaben(z, p) if (p != "abgleichen" or phase in ("abgleichen", "fertig")) else None
        if p == phase:
            erledigt = idx
        elif phase == "fertig" or DURCHGAENGE.index(p) < DURCHGAENGE.index(phase):
            erledigt = n
        else:
            erledigt = 0
        print("%s: %s/%s" % (NAMEN[p], erledigt, "?" if n is None else n))
    print("Aussagen: %d, Rahmen: %d, zurückgewiesene Abgaben: %d" % (len(z["aussagen"]), len(z["rahmen"]), z["zurueckgewiesen"]))
    print("offen: %s" % ("assemble" if phase == "fertig" else aufgabe_titel(z, phase, idx)))


def zusammenfuehren(z):
    """Aussagen nach Abgleich: (liste in Textreihenfolge, Sachverhalt-Schlüssel je Aussage)."""
    a = z["aussagen"]
    eltern = {x["s"]: x["s"] for x in a}

    def wurzel(s):
        while eltern[s] != s:
            eltern[s] = eltern[eltern[s]]
            s = eltern[s]
        return s

    weg = {}
    for i, j, wert in z["entscheidungen"]:
        if wert in ("gleich", "sachverhalt"):
            r1, r2 = wurzel(a[i]["s"]), wurzel(a[j]["s"])
            if r1 != r2:
                eltern[r2] = r1
        if wert == "gleich":
            weg[j] = i
    fund = {k: [f.strip() for f in x["fundstellen"].split(",")] for k, x in enumerate(a)}

    def ziel(k):
        while k in weg:
            k = weg[k]
        return k

    for j in sorted(weg):
        t = ziel(j)
        for f in fund[j]:
            if f not in fund[t]:
                fund[t].append(f)
    aus = []
    for k, x in enumerate(a):
        if k in weg:
            continue
        aus.append((x, ", ".join(fund[k]), wurzel(x["s"])))
    return aus


def cmd_assemble(args):
    if len(args) not in (1, 2):
        raise Fehler("assemble <arbeitsordner> [<ausgabe>]")
    ordner = os.path.abspath(args[0])
    z = zustand_lesen(ordner)
    phase, idx = offene_aufgabe(z)
    if phase != "fertig":
        raise Fehler("noch offen: %s" % aufgabe_titel(z, phase, idx))
    liste = zusammenfuehren(z)
    v_nr = OrderedDict()
    for _, _, s in liste:
        v_nr.setdefault(s, len(v_nr) + 1)
    na, nv, nr_ = len(liste), len(v_nr), len(z["rahmen"])
    wa, wv, wr = max(3, len(str(na))), max(2, len(str(nv))), max(2, len(str(nr_)))
    zeilen_a = [["A%0*d" % (wa, k), "V%0*d" % (wv, v_nr[s]), fund, x["text"], x["art"], x["beleg"], x["reich"], x["zeichen"]]
                for k, (x, fund, s) in enumerate(liste, 1)]
    zeilen_r = [["R%0*d" % (wr, k), r["fundstelle"], r["inhalt"]] for k, r in enumerate(z["rahmen"], 1)]
    if z["zweiter"] or (len(args) == 2 and not args[1].endswith(".md")):
        ziel = args[1] if len(args) == 2 else os.path.join(ordner, "durchlauf.txt")
        aus = [" | ".join(maskieren(str(f)) for f in r) for r in zeilen_a]
        aus += [" | ".join(maskieren(str(f)) for f in [r[0], r[1], "Rahmen", r[2]]) for r in zeilen_r]
        schreiben(ziel, "\n".join(aus) + "\n")
    else:
        ziel = args[1] if len(args) == 2 else z["zieldatei"]
        name = os.path.splitext(os.path.basename(ziel))[0]
        projekt = projekt_von(z["beitrag"])
        quelle = os.path.relpath(z["beitrag"], projekt) if projekt else z["beitrag"]
        betrifft = {"pdf": "PDF", "transkript": "Transkript", "markdown": "Markdown-Dokument"}[z["art"]]
        kopf = ["# %s" % name, "",
                "**Datum:** %s" % datetime.date.today().isoformat(),
                "**Status:** Zerlegung",
                "**Betrifft:** %s" % betrifft,
                "**Quelle:** `%s`" % quelle,
                "**Regeln:** Zerlege- und Katalogregeln, Fassung %s" % z["fassung"],
                "**Katalog-Erweiterung:** %s" % (", ".join(z["katalog"]) or "keine"),
                "**Prüfsumme:** %s" % z["pruefsumme"],
                "**Durchläufe:** 1", ""]
        text = "\n".join(kopf) + "\n## Aussagen\n\n" + tabelle(
            ["Kennung", "Sachverhalt", "Fundstellen", "Aussage", "Art", "Beleg", "Reichweite", "Kennzeichen"], zeilen_a)
        text += "\n\n## Rahmen\n\n" + tabelle(["Kennung", "Fundstelle", "Inhalt"], zeilen_r) + "\n"
        d = os.path.dirname(os.path.abspath(ziel))
        os.makedirs(d, exist_ok=True)
        schreiben(ziel, text)
    print("Aussagen %d, Sachverhalte %d, Rahmen-Zeilen %d; geschrieben: %s" % (na, nv, nr_, ziel))


BEFEHLE = {"split": cmd_split, "next": cmd_next, "submit": cmd_submit, "status": cmd_status,
           "assemble": cmd_assemble, "hash": cmd_hash, "check": cmd_check, "renumber": cmd_renumber,
           "profile": cmd_profile, "compare": cmd_compare}


def main(argv):
    if len(argv) < 2 or argv[1] not in BEFEHLE:
        sys.stderr.write("Aufruf: breakdown.py {%s} …\n" % "|".join(BEFEHLE))
        return 1
    try:
        BEFEHLE[argv[1]](argv[2:])
    except FormatFehler as e:
        sys.stderr.write("Format: %s\n" % e)
        return 2
    except Abbruch as e:
        sys.stderr.write("Abbruch: %s\n" % e)
        return 3
    except Fehler as e:
        sys.stderr.write("Fehler: %s\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
