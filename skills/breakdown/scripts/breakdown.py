#!/usr/bin/env python3
"""breakdown.py — zählt und prüft Zerlegungen des Skills breakdown (skill-breakdown).

Befehle (Spec 04 im Konzeptprojekt MSZ-Zerlegung-Beitrag):
  hash     <beitrag>
  check    <zerlegung> <beitrag> <fassung>
  renumber <arbeitsdatei>
  profile  <zerlegung> <beitrag> [--seiten N] [--ende GRUND]
  compare  <zerlegung> <zweiter-durchlauf>

Nur Python 3 ab 3.9 mit der Standardbibliothek. Exit-Codes: 0 erfolgreich,
1 Fehler in Argumenten oder beim Lesen und Schreiben, 2 Format verletzt.
"""

import hashlib
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


BEFEHLE = {"hash": cmd_hash, "check": cmd_check, "renumber": cmd_renumber,
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
    except Fehler as e:
        sys.stderr.write("Fehler: %s\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
