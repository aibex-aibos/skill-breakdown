# skill-breakdown

Zerlegt einen Beitrag (Transkript, Markdown, PDF) in Einzelaussagen, stuft sie nach Art, Beleg und Reichweite ein und speichert das Wissensprofil, auf Wunsch mit Meta-Ebenen.

Das Paket enthält den Skill `breakdown` für AIbex AIBOS.

## Wozu

Ein Wissensprofil zeigt, was in einem Beitrag tatsächlich an Wissen steckt: wie viele Aussagen er enthält, welcher Art sie sind (Erfahrung, Empfehlung, Kritik …), wie gut sie belegt sind und ob sie über den Einzelfall hinaus gelten. So lassen sich Beiträge vergleichen, etwa ein Erfahrungsbericht in einem Video mit einem Leitfaden.

## Voraussetzungen

- AIBOS v0.7; der Vault ist an diese Version gebunden.
- Python 3 ab 3.9, nur die Standardbibliothek.
- Claude Code: PDF-Dateien liest der Skill mit dem Lesewerkzeug des Hosts.

## Holen

```bash
aibos --fetch skill-breakdown
```

`aibos` liegt in der Regel nicht im `PATH`; aufrufen über den Weiterleiter `~/.aibos/bin/aibos`. Der Skill steht ab dem nächsten Chat bereit.

## Aufrufe

| Auftrag | Beispiel |
|---|---|
| Grundzerlegung | `/breakdown @Video/03 Building Real Software with Anthropic SDLC.md` oder „Zerlege den Beitrag @Video/03 …" |
| Meta-Zerlegung | `/breakdown Meta-Zerlegung @Video/03 …` |
| mit zweitem Durchlauf | „Zerlege @PDF/Leitfaden.pdf als Grunddokument" |

Angenommen werden PDF, Transkripte (Markdown mit Zeilen `[hh:mm:ss]`) und andere Markdown-Dateien.

## Wie der Skill arbeitet

Die Zerlegung ist keine einzige große Aufgabe an das Modell. Das Skript `scripts/breakdown.py` teilt den Beitrag in kleine Einheiten: eine PDF-Seite, etwa 300 Wörter Transkript oder einen Markdown-Abschnitt. Dann gibt es dem Modell die Teilaufgaben einzeln aus:

1. jede Einheit zerlegen;
2. die Aussagen in Gruppen von höchstens 20 einstufen;
3. je Einheit Wiederholungen gegenüber den früheren Einheiten abgleichen.

Nach jeder Abgabe prüft das Skript das Ergebnis und gibt eine Fortschrittszeile aus, etwa „Zerlegen 3/10: 9 Aussagen, 1 Rahmen; zusammen 27 Aussagen". Bricht ein Lauf ab, setzt ein neuer Auftrag an der offenen Teilaufgabe fort. Gezählt wird nur vom Skript.

Die Regeln und der Katalog stehen in `skills/breakdown/regeln.md`.

## Ablage

Das Ergebnis liegt im Projekt des Beitrags unter `@Breakdown/NN <Name> — Zerlegung.md`, mit Kopf, Wissensprofil, Tabellen der Aussagen und Rahmen-Zeilen, auf Wunsch Meta-Ebenen und Vergleich. Der Skill committet nur diese Datei und pusht nicht. Während der Arbeit liegt ein Arbeitsordner unter `@Breakdown/.arbeit/`; er wird am Ende entfernt.

Eine neue Zerlegung schreibt der Skill ohne Rückfrage, weil der Auftrag sie verlangt. Vor dem Ersetzen einer vorhandenen fragt er. Neue Arten, die im Katalog fehlen, nimmt er nach Rückfrage in `@Data/skill-breakdown/katalog.md` an der Vault-Root auf.

## Lizenz

Apache-2.0, siehe `LICENSE` und `NOTICE`. „AIbex" und „AIbex AIBOS" sind Marken der AIbex KG und fallen nicht unter die Lizenz.
