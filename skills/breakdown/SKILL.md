---
name: breakdown
version: 0.1.0
description: >
  Zerlegt einen Beitrag (Transkript einer Video-Notiz, Markdown, PDF) in Einzelaussagen, stuft jede
  nach Art, Beleg und Reichweite ein und speichert die Zerlegung mit Wissensprofil in @Breakdown/,
  auf Wunsch mit Meta-Ebenen. Verwenden bei „Zerlege den Beitrag …", „Meta-Zerlegung …",
  „/breakdown …", „Wissensprofil von …".
---

# Zerlegung eines Beitrags

Der Skill zerlegt einen Beitrag in Einzelaussagen, stuft jede ein und speichert das Ergebnis als Markdown-Datei. Die Regeln und der Katalog stehen in **`regeln.md`** in diesem Ordner; lies sie bei jedem Aufruf vollständig, bevor du zerlegst. Gezählt wird nur mit dem Skript, nie geschätzt.

**Skript:** `python3 <Skill-Ordner>/scripts/breakdown.py <befehl> …`; `<Skill-Ordner>` ist der Ordner dieses Skills („Base directory for this skill"). Immer über `python3` aufrufen. Exit-Code 2 heißt: das Format einer Datei ist verletzt; die Ausgabe nennt Zeile und Grund.

**Fragen:** Jede Frage mit Optionen stellst du mit dem Auswahlwerkzeug; in Claude Code lädst du es bei Bedarf mit `ToolSearch` (`select:AskUserQuestion`). Ohne Auswahlwerkzeug stellst du dieselbe Frage als nummerierte Liste, die Empfehlung zuerst.

## Grenze: keine Rückfrage vor dem Schreiben

Eine **neue** Zerlegung schreibst du ohne Rückfrage: Der Auftrag „Zerlege den Beitrag" oder „Meta-Zerlegung" verlangt sie ausdrücklich und gilt als Bestätigung. Zu Beginn nennst du Zieldatei und Fassung der Regeln. Eine **vorhandene** Zerlegung ersetzt du nur nach Rückfrage. In `@Data/skill-breakdown/katalog.md` schreibst du nur nach einer Antwort des Users auf die Frage nach einer vorläufigen Art.

## Aufträge

| Auftrag | Beispiel | Wirkung |
|---|---|---|
| Grundzerlegung | `/breakdown @Video/03 …md`, „Zerlege den Beitrag …" | Grundzerlegung |
| Meta-Zerlegung | `/breakdown Meta-Zerlegung @Video/03 …md`, „Meta-Zerlegung von …" | Grundzerlegung und Meta-Ebenen |
| zweiter Durchlauf | „… mit zweitem Durchlauf", „… als Grunddokument" | dazu ein unabhängiger zweiter Durchlauf mit Vergleich |

Ein Grunddokument bekommt immer einen zweiten Durchlauf. Nennt der Auftrag keinen Beitrag oder ist der Pfad nicht eindeutig, frag nach dem Beitrag.

## Art des Beitrags

| Datei | Art | Fundstelle | Lesen |
|---|---|---|---|
| `.pdf` | PDF | Seite der Datei („S. 12") | mit dem Lesewerkzeug und `pages`, in Abschnitten zu 6 Seiten |
| `.md` mit Zeilen, die mit `[hh:mm:ss]` beginnen | Transkript | Zeitstempel („00:10:13") | als Text; ab etwa 8000 Wörtern in Abschnitten dieser Größe |
| andere `.md` | Markdown | Zeilennummer („Z. 42") | als Text mit Zeilennummern; ab etwa 8000 Wörtern in Abschnitten |

Andere Dateien nimmst du nicht an; nenne die drei Arten.

## Ablage

| Punkt | Regel |
|---|---|
| Projekt | der nächste Ordner mit `@/` oberhalb der Datei des Beitrags, auch wenn die Session woanders läuft; gibt es keinen, frag nach dem Zielprojekt und halte bis zur Antwort an |
| Vault-Root | vom Projekt aufwärts der erste Ordner mit `.aibos/workspace.yaml`, sonst der erste mit `aibos:` in `.aibos/config.yaml` |
| Zieldatei | `<projekt>/@Breakdown/NN <Name> — Zerlegung.md` mit Nummer und Name des Beitrags; ohne Nummer `<Name> — Zerlegung.md`, `<Name>` = Dateiname ohne Endung |
| Fassung der Regeln | die Zahl im Titel von `regeln.md` |
| Katalog-Erweiterung | die Namen aus `<vault-root>/@Data/skill-breakdown/katalog.md`, durch Komma getrennt; gibt es die Datei nicht, „keine" |

### Form der Zieldatei

Kopf im Memo-Stil, kein Frontmatter; die Feldnamen genau so:

```markdown
# <Name> — Zerlegung

**Datum:** YYYY-MM-DD
**Status:** Zerlegung
**Betrifft:** <Art des Beitrags, Autor oder Herkunft, bei einem Video die Adresse>
**Quelle:** `<Pfad des Beitrags relativ zum Projekt>`
**Regeln:** Zerlege- und Katalogregeln, Fassung <n>
**Katalog-Erweiterung:** <Arten> | keine
**Prüfsumme:** <Ausgabe von breakdown.py hash>
**Durchläufe:** 1

## Wissensprofil

## Aussagen

| Kennung | Sachverhalt | Fundstellen | Aussage | Art | Beleg | Reichweite | Kennzeichen |
|---|---|---|---|---|---|---|---|
| A001 | V01 | 00:00:26, 00:09:23 | <ein deutscher Satz> | Erfahrung | beobachtet | Einzelfall | – |

## Rahmen

| Kennung | Fundstelle | Inhalt |
|---|---|---|
| R01 | 00:00:19 | <kurz, was die Stelle enthält> |
```

- *Wissensprofil*, *Vorläufige Arten*, *Unsichere Stellen*, die Kopfzeile **Meta-Ebenen** und den Abschnitt *Vergleich* schreibt das Skript; du lässt *Wissensprofil* leer.
- *Kennzeichen*: `–`, `unsicher: "<Wortlaut des Originals>"`, `vorläufig` oder beide, durch `; ` getrennt.
- Ein senkrechter Strich im Text wird `\|`; keine Zeilenumbrüche in einer Zelle.
- *Rahmen* steht immer in der Datei, auch leer.

## Ablauf der Grundzerlegung

1. **Ziel bestimmen** nach *Ablage*.
2. **Vorhandene Zerlegung prüfen:** `breakdown.py check "<zieldatei>" "<beitrag>" <fassung>`.
   - `fehlt`: weiter mit 3.
   - `aktuell`: nichts neu zerlegen; das Profil aus der Datei melden. Bei „Meta-Zerlegung" weiter mit *Ablauf der Meta-Zerlegung*, sofern die Datei noch keine Meta-Ebenen hat.
   - `fassung <alt>` oder `geändert`: Datei und Grund nennen und fragen, ob ersetzt werden soll (Empfehlung: ersetzen). Ohne Ja anhalten.
3. **Beginn melden:** Zieldatei, Fassung der Regeln, Art des Beitrags, Zahl der Abschnitte. Keine Rückfrage (siehe *Grenze*).
4. **Lesen und zerlegen,** Abschnitt für Abschnitt nach `regeln.md`. Schreib nach jedem Abschnitt die Zeilen in eine **Arbeitsdatei** in einem temporären Ordner (in Claude Code im Scratchpad der Session), eine Zeile je Eintrag, Felder durch ` | `:
   - Aussage, 8 Felder: `A1 | V1 | <Fundstellen> | <Aussage> | <Art> | <Beleg> | <Reichweite> | <Kennzeichen>`
   - Rahmen, 4 Felder: `R1 | <Fundstelle> | Rahmen | <Inhalt>`

   Ein senkrechter Strich im Text wird `\|`. Kennungen dürfen vorläufig sein; `renumber` vergibt sie neu. Bei einem PDF merkst du dir die Zahl der Seiten (letzte gelesene Seite).
5. **Abgleich:** Wiederholungen über die Abschnittsgrenzen nach Z3 zusammenführen (weitere Fundstelle statt neuer Aussage), dann `breakdown.py renumber "<arbeitsdatei>"`.
6. **Datei schreiben:** `breakdown.py hash "<beitrag>"`, dann die Zieldatei nach *Form der Zieldatei*, mit den Zeilen der Arbeitsdatei als Tabellenzeilen (Rahmen-Zeilen ohne das Feld `Rahmen`). Ordner `@Breakdown/` anlegen, falls er fehlt. Erst jetzt entsteht die Zieldatei; bricht der Lauf vorher ab, bleibt nur die Arbeitsdatei.
7. **Zählen:** `breakdown.py profile "<zieldatei>" "<beitrag>"`, bei einem PDF mit `--seiten <n>`. Gibt es vorläufige Arten, trag in *Vorläufige Arten* je Art die Definition in einem Satz ein.
8. **Zweiter Durchlauf,** falls verlangt (unten).
9. **Commit,** wenn das Projekt ein Git-Repo ist: nur die Zieldatei, Nachricht „Zerlegung NN: <Name>" (ohne Nummer „Zerlegung: <Name>"). Nicht pushen. Ohne Git-Repo nicht committen und das melden.
10. **Meldung** (unten).
11. **Vorläufige Arten** entscheiden lassen (unten).

## Ablauf der Meta-Zerlegung

Über der Grundzerlegung bildest du Ebene für Ebene Meta-Aussagen nach `regeln.md`, M1 bis M5:

- Je Ebene ein Abschnitt `### Ebene <k>` unter `## Meta-Ebenen` (zwischen *Rahmen* und *Vergleich*) mit der Tabelle `| Kennung | Stützen | Meta-Aussage | Art |`; Kennungen `M<k>.01`, `M<k>.02`, …; Stützen sind Kennungen der Ebene darunter, durch Komma getrennt, mindestens zwei; Art ist eine Art des Katalogs oder `Thema`. Freie Arten gibt es hier nicht.
- Die nächste Ebene entsteht nur aus Meta-Aussagen, die kein Thema sind.
- Ende nach M5, in dieser Reihenfolge geprüft: *Kriterium* (alle Meta-Aussagen der Ebene sind Themen), *eine Aussage*, *keine Verbindung* (die leere Ebene wird nicht geschrieben), *Grenze* (Ebene 8).
- Unter die letzte Tabelle ein Satz, warum die Folge endete.
- Dann `breakdown.py profile "<zieldatei>" "<beitrag>" --ende "<Kriterium|eine Aussage|keine Verbindung|Grenze>"` (bei PDF mit `--seiten`), Commit und Meldung. Endete die Folge an der Grenze, sag das ausdrücklich.

## Zweiter Durchlauf

Starte einen Subagenten. Sein Auftrag nennt nur: den Pfad von `regeln.md`, den Pfad des Beitrags, die Arten der Katalog-Erweiterung, die Abschnittsgröße, das Format der Arbeitsdatei (Schritt 4) und eine **eigene** Ausgabedatei im temporären Ordner. Er nennt weder die Zieldatei noch deine Arbeitsdatei. Danach:

1. `breakdown.py renumber "<ausgabe des subagenten>"`;
2. `breakdown.py compare "<zieldatei>" "<ausgabe des subagenten>"` schreibt *Vergleich* und setzt **Durchläufe** auf 2;
3. die Ausgabedatei des Subagenten löschen.

Kennt der Host keine Subagenten, entfällt der zweite Durchlauf; sag das in der Meldung.

## Meldung am Ende

Pfad der Datei; Zahl der Aussagen, Sachverhalte und Rahmen-Zeilen; die drei häufigsten Arten mit Anteil; die vier Maße; Zahl der unsicheren Stellen; vorläufige Arten mit Name und Zahl der Aussagen; nach einer Meta-Zerlegung Zahl der Ebenen und Grund des Endes; nach einem zweiten Durchlauf das Urteil; ob committet wurde. Alle Zahlen aus der Ausgabe des Skripts.

## Vorläufige Arten

Frag je vorläufiger Art mit dem Auswahlwerkzeug: „<Name> — <Definition> (<n> Aussagen): annehmen oder ablehnen?"

- **Annehmen:** Trag die Art in `<vault-root>/@Data/skill-breakdown/katalog.md` ein (Ordner und Datei anlegen, falls sie fehlen) als Zeile der Tabelle `| Name | Definition | angenommen | erste Zerlegung |` mit Datum und Pfad der Zieldatei. Entferne in der Zieldatei bei ihren Aussagen das Kennzeichen `vorläufig` und ergänze die Art in **Katalog-Erweiterung**. Committe `katalog.md` allein im Repo der Vault-Root: „Katalog: Art <Name> angenommen".
- **Ablehnen:** Schlag für jede ihrer Aussagen die passendste Art aus `regeln.md` vor und trag sie ein; das Kennzeichen `vorläufig` entfällt.

Danach `breakdown.py profile …` erneut und die Zieldatei erneut committen.

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Beitrag fehlt oder ist keine angenommene Art | melden, nichts schreiben |
| Beitrag in keinem Projekt | nach dem Zielprojekt fragen |
| Projekt ohne Git-Repo | Datei schreiben, nicht committen, das melden |
| Abbruch mitten in der Zerlegung | die Arbeitsdatei bleibt im temporären Ordner; keine halbe Zieldatei |
| Skript endet mit Exit-Code 1 oder 2 | anhalten, die Ausgabe melden, nichts committen |

## Grenzen

- Schreib nur in `@Breakdown/` des Projekts des Beitrags, in den temporären Ordner und, nach einer Antwort des Users, in `@Data/skill-breakdown/katalog.md` an der Vault-Root; nie in dieses Paket.
- Push nicht. Ruf `aibos` nicht auf. Lies keine Webseiten.
- Vergleiche nicht mit einer Wissensbasis und urteile nicht über die Qualität eines Beitrags; die Maße stehen für sich.
