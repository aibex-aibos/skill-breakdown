# skill-breakdown 0.1.0 — Stand der Implementierung

Implementierungsplan: `MSZ-Zerlegung-Beitrag`, Memo 27, freigegeben in Memo 28; ab S6 nach Memo 39, freigegeben in Memo 40.

| # | Schritt | Stand | Ergebnis |
|---|---|---|---|
| S1 | Paket-Repo anlegen | ☑ | Manifest 0.1.0, LICENSE, NOTICE, Gerüst von README.md und SKILL.md |
| S2 | Holen mit Wegwerf-Kandidat prüfen | ☑ | v0.1.0-rc0 im Klon geholt: Skill breakdown 0.1.0 registriert und ausgerollt; Wegwerf-Projekt im Papierkorb |
| S3 | Skript breakdown.py und Testfälle T1–T8 | ☑ | breakdown.py mit fünf Befehlen; 14 Tests in MSZ tests/breakdown/ grün, T8 zählt die Probe am Playbook nach |
| S4 | regeln.md aus Spec 01 | ☑ | regeln.md = Spec 01 Fassung 5 ohne Frontmatter; 5 Zeilen angepasst (Titel, Einleitung, drei Verweise auf Specs) |
| S5 | SKILL.md nach Spec 03 und 05 | ☑ | Ablauf, Ablage, Meta-Zerlegung, zweiter Durchlauf, Meldung, vorläufige Arten, Fehlerfälle, Grenze nach R8 wörtlich |
| S6 | Skript: Ablauf führen (split, next, submit, status, assemble), Tests T9–T13 | ☑ | breakdown.py mit zehn Befehlen; 26 Tests in MSZ tests/breakdown/ grün (14 bisherige, 12 neue in test_ablauf.py); Festlegungen A91–A97 (Memo 41) |
| S7 | regeln.md auf Fassung 7 | ☑ | Titel Fassung 7, Z12 aus Spec 01 (Schlusssatz verweist auf Skript und SKILL.md statt auf Specs); 6 Zeilen weichen ab, wie bisher nur Verweise (Memo 42) |
| S8 | SKILL.md als Schleife nach Spec 03 | ☑ | Grundzerlegung als Schleife aus next/submit, assemble, remove; zweiter Durchlauf mit split --zweiter; Schritte 1–11 wie Spec 03; Befehl remove im Skript, 27 Tests grün (Memo 43) |
| S9 | Evals vorbereiten (erwartet.md, run.sh) | ☑ | drei erwartet.md (2, 8, 7 Kernaussagen), von iHux bestätigt; auswerten.py, run.sh (Memos 44, 45) |
| S10 | Stufe 1: Wegwerf-Kandidat, Evals, Kapitel mit 10 Minuten | ☑ | Kapitel in 202 s mit Abgleich; E-PDF und E-Markdown bestanden; E-Transkript 83,3 % (B12), von iHux so angenommen (Memos 48, 49) |
| S11 | README fertig, Paket prüfen | ☑ | README nach Spec 05; anja-pruefen ohne Befund, Grenze nach R8 als Ausnahme laut Paket-Spec (Memo 50) |
| S12 | Release-Kandidat v0.1.0-rc1 | ☑ | manifest 0.1.0-rc1, Tag v0.1.0-rc1 lokal (Memo 51) |
