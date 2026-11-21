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

**Das Skript führt.** Die Grundzerlegung ist keine einzelne große Aufgabe, sondern eine Folge kleiner Teilaufgaben, die das Skript ausgibt und prüft: eine Einheit zerlegen, eine Gruppe von Aussagen einstufen, eine Gruppe von Kandidaten abgleichen. Du erledigst immer **nur die Teilaufgabe, die `next` ausgibt**, schreibst ihr Ergebnis in die genannte Datei und gibst es mit `submit` ab. Zerleg nie im Denken vor, was noch nicht ausgegeben ist, und schreib nie den ganzen Beitrag auf einmal.

**Skript:** `python3 <Skill-Ordner>/scripts/breakdown.py <befehl> …`; `<Skill-Ordner>` ist der Ordner dieses Skills („Base directory for this skill"). Immer über `python3` aufrufen. Exit-Code 2 heißt: das Format einer Datei oder Abgabe ist verletzt; die Ausgabe nennt Zeile und Grund. Exit-Code 3 heißt: eine Teilaufgabe wurde nach drei zurückgewiesenen Abgaben abgebrochen.

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

| Datei | Art | Fundstelle | Einheit (teilt das Skript) |
|---|---|---|---|
| `.pdf` | PDF | Seite der Datei („S. 12") | eine Seite; du liest sie mit dem Lesewerkzeug und `pages` |
| `.md` mit Zeilen, die mit `[hh:mm:ss]` beginnen | Transkript | Zeitstempel („00:10:13") | etwa 300 Wörter; `next` gibt den Text aus |
| andere `.md` | Markdown | Zeilennummer („Z. 42") | ein Abschnitt, höchstens etwa 300 Wörter; `next` gibt den Text mit Zeilennummern aus |

Andere Dateien nimmst du nicht an; nenne die drei Arten.

## Ablage

| Punkt | Regel |
|---|---|
| Projekt | der nächste Ordner mit `@/` oberhalb der Datei des Beitrags, auch wenn die Session woanders läuft; gibt es keinen, frag nach dem Zielprojekt und halte bis zur Antwort an |
| Vault-Root | vom Projekt aufwärts der erste Ordner mit `.aibos/workspace.yaml`, sonst der erste mit `aibos:` in `.aibos/config.yaml` |
| Zieldatei | `<projekt>/@Breakdown/NN <Name> — Zerlegung.md` mit Nummer und Name des Beitrags; ohne Nummer `<Name> — Zerlegung.md`, `<Name>` = Dateiname ohne Endung |
| Fassung der Regeln | die Zahl im Titel von `regeln.md` |
| Katalog-Erweiterung | die Namen aus `<vault-root>/@Data/skill-breakdown/katalog.md`, durch Komma getrennt; gibt es die Datei nicht oder lässt der Host das Lesen nicht zu, „keine" (das sagt die Meldung) |

### Form der Zieldatei

Die Zieldatei schreibt `breakdown.py assemble`: Kopf im Memo-Stil, kein Frontmatter, dann *Aussagen* und *Rahmen*. Du ergänzt danach nur **Betrifft** (Autor oder Herkunft, bei einem Video die Adresse). Zur Kontrolle die Form:

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

- *Wissensprofil*, *Vorläufige Arten*, *Unsichere Stellen*, die Kopfzeile **Meta-Ebenen** und den Abschnitt *Vergleich* schreibt das Skript.
- *Kennzeichen*: `–`, `unsicher: "<Wortlaut des Originals>"`, `vorläufig` oder beide, durch `; ` getrennt.
- *Rahmen* steht immer in der Datei, auch leer.

## Ablauf der Grundzerlegung

1. **Ziel bestimmen** nach *Ablage*.
2. **Vorhandene Zerlegung prüfen:** `breakdown.py check "<zieldatei>" "<beitrag>" <fassung>`.
   - `fehlt`: weiter mit 3.
   - `aktuell`: nichts neu zerlegen; das Profil aus der Datei melden. Bei „Meta-Zerlegung" weiter mit *Ablauf der Meta-Zerlegung*, sofern die Datei noch keine Meta-Ebenen hat.
   - `fassung <alt>` oder `geändert`: Datei und Grund nennen und fragen, ob ersetzt werden soll (Empfehlung: ersetzen). Ohne Ja anhalten.
3. **Teilen:** `breakdown.py split "<beitrag>" "<zieldatei>" --fassung <fassung> --katalog "<Katalog-Erweiterung>"` (ohne Erweiterung `--katalog keine`). Das Skript legt den **Arbeitsordner** `<projekt>/@Breakdown/.arbeit/<Name>/` an und nennt die Zahl der Einheiten. Gibt es ihn schon zum selben Stand, meldet es `Fortsetzen: …`; dann machst du dort weiter. Findet es bei einem PDF keine Seitenzahl, verlangt es `--seiten <n>`: lies dann nur die erste Seite und nimm die Seitenzahl, die das Lesewerkzeug nennt.
4. **Beginn melden:** Zieldatei, Fassung der Regeln, Art des Beitrags, Zahl der Einheiten. Keine Rückfrage (siehe *Grenze*).
5. **Schleife,** bis `next` `fertig` ausgibt:
   1. `breakdown.py next "<arbeitsordner>"` und genau die ausgegebene Teilaufgabe lesen;
   2. sie nach `regeln.md` erledigen: beim **Zerlegen** nur diese Einheit (Z1 bis Z11, nicht einstufen; Wiederholungen nur innerhalb der Einheit zusammenführen), beim **Einstufen** nur diese Aussagen nach dem Katalog, beim **Abgleichen** nur diese Paare nach Z3;
   3. das Ergebnis im angegebenen Format in die genannte Abgabedatei schreiben, eine Zeile je Eintrag; ein senkrechter Strich im Text wird `\|`;
   4. `breakdown.py submit "<arbeitsordner>"` und dessen **Fortschrittszeile unverändert ausgeben**, etwa „Zerlegen 3/10: 9 Aussagen, 1 Rahmen; zusammen 27 Aussagen".

   Endet `submit` mit Exit-Code 2, berichtige dieselbe Abgabe nach der Meldung und gib sie erneut ab. Endet es mit Exit-Code 3, halte an (*Fehlerfälle*). Denk nur über die offene Teilaufgabe nach; was danach kommt, gibt das Skript aus.
6. **Zusammenführen:** `breakdown.py assemble "<arbeitsordner>"` schreibt Kopf, *Aussagen* und *Rahmen* in die Zieldatei und legt `@Breakdown/` an, falls es fehlt. Dann **Betrifft** im Kopf ergänzen.
7. **Zählen:** `breakdown.py profile "<zieldatei>" "<beitrag>"`, bei einem PDF mit `--seiten <n>` (die Zahl der Einheiten aus Schritt 3). Gibt es vorläufige Arten, trag in *Vorläufige Arten* je Art die Definition in einem Satz ein.
8. **Zweiter Durchlauf,** falls verlangt (unten).
9. **Aufräumen und Commit:** `breakdown.py remove "<arbeitsordner>"`, dann, wenn das Projekt ein Git-Repo ist, nur die Zieldatei committen, Nachricht „Zerlegung NN: <Name>" (ohne Nummer „Zerlegung: <Name>"). Nicht pushen. Ohne Git-Repo nicht committen und das melden.
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

Starte einen Subagenten. Sein Auftrag nennt nur: den Pfad von `regeln.md`, den Pfad des Beitrags, die Arten der Katalog-Erweiterung, den Aufruf des Skripts mit dem Befehl `split … --zweiter` und die Schritte 3 und 5 dieses Ablaufs, zum Schluss `breakdown.py assemble "<sein arbeitsordner>"`. Er nennt weder die Zieldatei noch deinen Arbeitsordner. `assemble` schreibt beim zweiten Durchlauf die Datei `durchlauf.txt` in seinen Arbeitsordner. Danach:

1. `breakdown.py compare "<zieldatei>" "<arbeitsordner des subagenten>/durchlauf.txt"` schreibt *Vergleich* und setzt **Durchläufe** auf 2;
2. `breakdown.py remove "<arbeitsordner des subagenten>"`.

Kennt der Host keine Subagenten, entfällt der zweite Durchlauf; sag das in der Meldung.

## Meldung am Ende

Pfad der Datei; Zahl der Aussagen, Sachverhalte und Rahmen-Zeilen; Zahl der Einheiten und der zurückgewiesenen Abgaben (aus `breakdown.py status` vor dem Aufräumen); die drei häufigsten Arten mit Anteil; die vier Maße; Zahl der unsicheren Stellen; vorläufige Arten mit Name und Zahl der Aussagen; nach einer Meta-Zerlegung Zahl der Ebenen und Grund des Endes; nach einem zweiten Durchlauf das Urteil; ob committet wurde. Alle Zahlen aus der Ausgabe des Skripts.

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
| Abbruch mitten in der Zerlegung | der Arbeitsordner bleibt; ein neuer Auftrag zum selben Beitrag setzt mit `split` an der offenen Teilaufgabe fort; keine halbe Zieldatei |
| `submit` endet mit Exit-Code 2 | dieselbe Abgabe berichtigen und erneut abgeben |
| Skript endet mit Exit-Code 1 oder 3 | anhalten, die Ausgabe melden, den Arbeitsordner stehen lassen, nichts committen |

## Grenzen

- Schreib nur in `@Breakdown/` des Projekts des Beitrags (Zieldatei und Arbeitsordner) und, nach einer Antwort des Users, in `@Data/skill-breakdown/katalog.md` an der Vault-Root; nie in dieses Paket.
- Push nicht. Ruf `aibos` nicht auf. Lies keine Webseiten.
- Vergleiche nicht mit einer Wissensbasis und urteile nicht über die Qualität eines Beitrags; die Maße stehen für sich.
