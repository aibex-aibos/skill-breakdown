# Zerlege- und Katalogregeln, Fassung 7

Die Regeln, nach denen der Skill `breakdown` einen Beitrag in Einzelaussagen zerlegt, jede Aussage einstuft und auf Wunsch die Meta-Zerlegung darüber bildet. Die Regeln gelten gleich für jeden Beitrag, auch für ein Grunddokument einer Wissensbasis. Eine gespeicherte Zerlegung nennt die Fassung, nach der sie entstand.

## Begriffe

| Begriff | Bedeutung |
|---|---|
| Beitrag | der Text, der zerlegt wird: Transkript eines Videos, Markdown-Dokument oder PDF |
| Aussage | genau eine prüfbare Behauptung des Beitrags, als vollständiger, für sich verständlicher Satz |
| Sachverhalt | das, worüber eine oder mehrere Aussagen etwas sagen; Aussagen zum selben Sachverhalt tragen dieselbe Sachverhalt-Kennung (Z3) |
| Rahmen | eine Stelle des Beitrags, die keine Aussage ist, aber zum Inhalt gehört (Z5) |
| Fundstelle | der Ort im Beitrag: Zeitstempel bei einem Transkript („00:10:13"), Seite der PDF-Datei („S. 12"), Zeilennummer bei Markdown („Z. 42") |
| Zerlegung | die Liste aller Aussagen und Rahmen-Zeilen eines Beitrags in der Reihenfolge des Textes |
| Wissensprofil | die Zerlegung mit Art, Beleg und Reichweite je Aussage, ausgezählt (siehe *Auszählung*) |
| Grundzerlegung | die Zerlegung nach Z1 bis Z12; Ebene 0 |
| Meta-Aussage | eine Aussage, die die Bedeutung mehrerer Aussagen der Ebene darunter zusammenfasst |
| Meta-Ebene | alle Meta-Aussagen über derselben Ebene; Ebene 1 liegt über der Grundzerlegung |
| Thema | eine Meta-Aussage, auf die keine Art des Katalogs mehr passt, weil sie nur noch nennt, worum es geht |

## Zerlegeregeln

**Z1 — Aussage.** Eine Aussage ist genau eine prüfbare Behauptung zum Thema des Beitrags. Sie wird als ein vollständiger deutscher Satz formuliert, der ohne den Text daneben verständlich ist; Bezüge wie „es" oder „das" werden aufgelöst.

**Z2 — Teilen.** Ein Satz mit mehreren Behauptungen, die unabhängig voneinander wahr oder falsch sein können, wird in mehrere Aussagen geteilt. Eine Aufzählung, deren Teile einzeln prüfbar sind („Produktmanager schreiben Anforderungen, Architekten den Entwurf"), wird geteilt; die Teile tragen dieselbe Sachverhalt-Kennung. Zusammen bleiben nur Beispiele, die dieselbe Behauptung veranschaulichen („etwa A, B oder C"). Z2 geht Z3 vor: Was unabhängig wahr oder falsch sein kann, wird nie zu einer Aussage zusammengezogen.

**Z3 — Wiederholung und Sachverhalt.** Wiederholt eine spätere Stelle dieselbe Behauptung, entsteht keine neue Aussage; die vorhandene Aussage bekommt die weitere Fundstelle, die erste zuerst. Das gilt auch für Merksätze, Vorspanne und Bildunterschriften, die nur wiederholen. Verschiedene Behauptungen zum selben Sachverhalt bleiben getrennte Aussagen und bekommen dieselbe Sachverhalt-Kennung. Fügt eine spätere Stelle einer schon gezählten Behauptung etwas hinzu, das für sich wahr oder falsch sein kann (etwa die Namen zu „drei Werkzeuge“), ist nur dieser Zusatz eine eigene Aussage mit derselben Sachverhalt-Kennung. Eine Aussage, die als einzige über ihren Sachverhalt spricht, hat eine eigene Kennung.

**Z4 — Reichweite bleibt.** Eine Aussage behält die Reichweite des Originals. Spricht der Autor von sich oder seinem Fall, nennt die Aussage ihn; spricht er allgemein, bleibt sie allgemein.

**Z5 — Rahmen.** Was zum Inhalt gehört, aber keine Behauptung zum Thema ist, wird nicht gestrichen, sondern als Rahmen-Zeile geführt: Begrüßung und Verabschiedung, Werbung, Ankündigungen ohne eigenen Inhalt, reine Verweise auf eine andere Stelle des Beitrags („siehe Stage 5"), bloße Beschreibung dessen, was gerade auf dem Bildschirm geschieht, Eigenschaften eines Beispielprodukts, Danksagungen. Eine zusammenhängende Stelle ergibt eine Rahmen-Zeile, nicht eine je Satz; eine Rahmen-Zeile setzt mindestens einen vollständigen Satz voraus. Wird eine Rahmen-Stelle von einer Aussage unterbrochen, ergibt jedes Teilstück eine eigene Zeile. Rahmen-Zeilen bekommen weder Art noch Beleg noch Reichweite und zählen nie als Aussage. Was ein Text zum Aufbau des Beitrags über den Gegenstand sagt („Dieser Schritt braucht keine Voraussetzung"), ist eine Aussage.

**Z6 — Erfahrung im Rahmen.** Was der Autor im Einzelfall getan hat und was dabei herauskam, ist eine Aussage; welche Eigenschaften das Beispielprodukt hat, ist Rahmen. Was das Werkzeug gerade auf dem Bildschirm tut („es lädt einen Skill", „es denkt nach", „es entwirft jetzt den Screen X"), ist Rahmen, solange der Autor nur mitliest. Es wird eine Aussage, sobald der Autor es kommentiert oder bewertet, ein Ergebnis oder eine Größe nennt („der Build lief 40 Minuten") oder daraus etwas über das Werkzeug ableitet („weil es kein Designsystem gab, nahm es meine Website").

**Z7 — Beispiele im Text.** Ein Codeblock, eine Beispieldatei oder ein Beispieldialog ergibt höchstens eine Aussage, nämlich was das Beispiel zeigt, und nur, wenn der Fließtext das nicht schon sagt. Die Einzelheiten des Beispiels fallen weg und werden nicht als Rahmen geführt; ein Beispiel im Text ist kein Beispielprodukt im Sinn von Z6. Erläuterungen im Fließtext zu einzelnen Zeilen eines Beispiels werden normal zerlegt.

**Z12 — Einheiten und Durchgänge.** Jeder Beitrag wird in kleinen Einheiten zerlegt, auch ein kurzer: ein PDF je Seite; ein Transkript zu etwa 300 Wörtern, geteilt an einer Zeilengrenze; ein Markdown-Dokument je Abschnitt an einer Überschrift, ein Abschnitt über 300 Wörter an der Absatzgrenze vor 300 Wörtern geteilt, ein Abschnitt unter 100 Wörtern mit dem folgenden zusammengelegt, solange zusammen höchstens 300 Wörter entstehen. Zerlegen (Z1 bis Z11) und Einstufen (Katalog) sind getrennte Durchgänge: Erst werden alle Einheiten zerlegt, dann die Aussagen in Gruppen von höchstens 20 eingestuft. Wiederholungen und gleiche Sachverhalte innerhalb einer Einheit werden beim Zerlegen zusammengeführt; über die Einheiten hinweg prüft danach das Modell je Einheit ab der zweiten ihre Aussagen gegen die früheren; danach werden die Kennungen neu vergeben. Teilen, Vorschlagen und Prüfen übernimmt das Skript `scripts/breakdown.py`; den Ablauf beschreibt `SKILL.md`.

**Z8 — Tabellen.** Jede Zelle wird wie Fließtext zerlegt. In Gegenüberstellungen zählen Aussagen über das alte Vorgehen ebenso wie Aussagen über das neue.

**Z9 — Körnung.** Im Zweifel so teilen, dass jede Aussage mit einer einzelnen Textstelle belegbar ist und ein Leser sie eindeutig mit Ja oder Nein prüfen kann. Nicht bis auf einzelne Wörter oder Attribute herunterteilen.

**Z10 — Unsichere Stellen.** Ist eine Stelle verstümmelt oder mehrdeutig (etwa ein fehlerhaftes Transkript), wird die Aussage nach bestem Verständnis formuliert und als *unsicher* gekennzeichnet, mit dem Wortlaut des Originals. Das Kennzeichen gilt nur, wenn der Sinn unsicher ist: wenn Wörter fehlen oder zwei Lesarten möglich sind. Ein offensichtlicher Hör- oder Schreibfehler mit eindeutigem Sinn wird ohne Kennzeichen berichtigt.

**Z11 — Was wegfällt.** Nur was nicht zum Inhalt gehört, fällt ganz weg: Kopf- und Fußzeilen, Seitenzahlen, Inhaltsverzeichnis, Linklisten, Füllwörter, Versprecher und Einwürfe ohne Inhalt, die kürzer sind als ein Satz („cool", „Wahnsinn").

## Katalog — Art

Jede Aussage bekommt genau eine Art. Art, Beleg und Reichweite sind voneinander unabhängig; jede Kombination ist erlaubt.

| Art | Was die Aussage sagt | Abgrenzung |
|---|---|---|
| Begriff | was etwas ist; legt eine Bedeutung fest | nicht: wie etwas abläuft |
| Beschreibung | wie etwas ist oder abläuft, allgemein gemeint; auch „im Verfahren X tut man Y", solange der Satz einen Ablauf wiedergibt | nicht: was der Autor im Einzelfall getan hat (Erfahrung) |
| Vorgehen | ein Schritt, eine Regel oder ein Werkzeug für einen Zweck, das der Leser anwenden kann; auch eine persönliche Arbeitsweise des Autors („ich mache vor jedem Commit ein Review"), dann mit Reichweite Einzelfall | ohne Sollen; mit „sollte", „besser", „empfiehlt" ist es eine Empfehlung |
| Empfehlung | was man tun oder lassen sollte, oft mit Bedingung | nicht: bloßes Urteil ohne Handlung (Bewertung) |
| Erfahrung | was im Einzelfall getan oder beobachtet wurde und was herauskam; auch eine Schwäche des Ergebnisses im Einzelfall; auch eine bloße Anzahl oder eine Schätzung („drei Werkzeuge", „würde Stunden kosten") | eine gemessene Größe ist ein Messwert |
| Messwert | eine im Einzelfall beobachtete Größe mit Einheit: Dauer, Menge, Kosten („40 Minuten", „1,5 Millionen Tokens") | nicht: bloße Anzahlen von Dingen, nicht: Schätzungen |
| Kritik | eine Schwäche, Grenze oder ein Risiko, die der Autor dem Vorgehen oder Werkzeug zuschreibt | eine Schwäche nur des Ergebnisses ist Erfahrung; ein negatives Urteil ohne benannte Schwäche ist Bewertung |
| Bewertung | ein Urteil (gut, wichtig, besser), das weder Handlung noch Schwäche benennt | |
| Offenes | etwas Unentschiedenes oder eine nicht genutzte Möglichkeit („noch nicht entschieden", „hätte auch … können") | zählt nicht als Wissen |
| Ziel | ein angestrebter oder erwarteter Zustand („die Zeit soll von Wochen auf Stunden sinken") | nennt er eine Handlung, ist es eine Empfehlung; ein bloßes Urteil ist Bewertung |

**Vorrang.** Passen zwei Arten, gilt die speziellere: Messwert vor Erfahrung; Kritik vor Bewertung und vor Erfahrung; Empfehlung vor Vorgehen und vor Bewertung; Offenes vor Erfahrung und vor Beschreibung; Empfehlung vor Ziel; Ziel vor Beschreibung und vor Bewertung.

**Freie Art.** Sie gilt nur in der Grundzerlegung; eine Meta-Aussage ohne passende Art ist ein Thema (M3). Gilt neben dem Katalog die Datei `@Data/skill-breakdown/katalog.md` an der Vault-Root, gehören ihre Arten zum Katalog. Passt keine Art, formuliert der Skill selbst eine: ein Name und ein Satz Definition. Sie wird als *vorläufig* gekennzeichnet und am Ende des Durchlaufs mit ihren Aussagen aufgelistet. Über die Aufnahme in den Katalog entscheidet der User. Bis dahin werden ihre Aussagen getrennt ausgezählt. Vor einer neuen Art prüft der Skill, ob eine schon vorgeschlagene vorläufige Art oder eine Art aus `katalog.md` passt. Was mit einer angenommenen Art geschieht, steht in `SKILL.md`.

## Katalog — Beleg

Jede Aussage bekommt genau einen Beleg. Maßgeblich ist nur, was der Beitrag an der Stelle sagt. Ob eine Aussage den Inhalt eines anderen Dokuments wiedergibt, stellt die Zerlegung nicht fest; das ist Sache des Vergleichs mit einer Wissensbasis.

| Beleg | Bedeutung |
|---|---|
| beobachtet | Der Autor stützt die Aussage auf etwas, das er selbst getan, gesehen oder gemessen hat, und nennt es an der Stelle oder im Satz unmittelbar daneben. Ein allgemeines Urteil, das sich nur pauschal auf den ganzen Versuch stützt, ist nicht beobachtet. |
| Quelle (genannt) | Der Autor nennt an der Stelle ein Dokument oder eine andere Quelle beim Namen oder verweist ausdrücklich darauf („im Playbook", „laut Kurs"). Eine einmalige Nennung am Anfang des Beitrags gilt nicht für spätere Stellen. |
| begründet | Der Autor nennt einen Grund, ohne eigene Beobachtung und ohne Quelle. |
| Quelle selbst | Der Beitrag trifft die Aussage als eigene Festlegung oder Vorgabe (Regelwerk, Norm, Herstellerdokumentation); er ist selbst die Quelle. |
| unbelegt | nichts davon |

**Vorrang.** Passen zwei Belege, gilt der stärkere, in dieser Reihenfolge: beobachtet, Quelle (genannt), begründet, Quelle selbst, unbelegt.

## Katalog — Reichweite

Jede Aussage bekommt genau eine Reichweite.

| Reichweite | Bedeutung |
|---|---|
| Einzelfall | Die Aussage gilt für das konkrete Projekt oder die Person des Autors. |
| übertragbar | Die Aussage ist so gemeint, dass sie auch für andere gilt. |

## Was eine Zeile der Zerlegung enthält

| Feld | Aussage | Rahmen-Zeile |
|---|---|---|
| Kennung | fortlaufend in der Reihenfolge des Textes | fortlaufend, eigene Zählung |
| Sachverhalt | Kennung des Sachverhalts (Z3) | keine |
| Fundstellen | eine oder mehrere, die erste zuerst | die Stelle |
| Text | die Aussage als Satz | kurz, was die Stelle enthält |
| Art, Beleg, Reichweite | je genau ein Wert | keine |
| Kennzeichen | *unsicher* mit Wortlaut (Z10), *vorläufig* bei freier Art | keine |

Dateiformat und Ablageort einer gespeicherten Zerlegung stehen in `SKILL.md`.

## Auszählung

- Gezählt werden die Aussagen und die Sachverhalte; beide Zahlen werden genannt.
- Das Wissensprofil nennt je Art, Beleg und Reichweite die Anzahl und den Anteil an den Aussagen. Für den Vergleich zweier Durchläufe oder zweier Beiträge gelten die Anteile, nicht die Anzahlen.
- Aussagen einer vorläufigen Art und Aussagen mit dem Kennzeichen *unsicher* werden zusätzlich getrennt genannt.
- Dazu nennt das Profil vier Maße. Sie beziehen sich auf die Aussagen der Grundzerlegung, nicht auf Sachverhalte und nicht auf Meta-Aussagen:

| Maß | Berechnung |
|---|---|
| Belegquote | Anteil der Aussagen mit Beleg beobachtet, Quelle (genannt) oder begründet an den Aussagen ohne Beleg *Quelle selbst* |
| Gehaltsquote | Anteil der Aussagen, deren Art weder Bewertung noch Offenes ist |
| Dichte | Aussagen je 1000 Wörter des Beitrags (Transkript, Markdown) bzw. je Seite (PDF); gezählt werden die Wörter des Inhalts ohne Zeitstempel, Einbettungen und Markup |
| Rahmenanteil | Anteil der Rahmen-Zeilen an allen Zeilen der Zerlegung (Aussagen und Rahmen) |

- Die Zerlegung leitet aus den Maßen kein Urteil über die Qualität ab und setzt keine Schwellen. Gezählt wird mit dem Skript `scripts/breakdown.py`, nicht vom Modell.

## Vergleich zweier Durchläufe

Läuft ein zweiter, unabhängiger Durchlauf, werden die Aussagen beider Durchläufe über ihre erste Fundstelle einander zugeordnet. Berichtet werden: die Zahl der Aussagen und Sachverhalte je Durchlauf, der Anteil der zugeordneten Aussagen mit derselben Art, demselben Beleg und derselben Reichweite, und die größte Abweichung der Anteile je Art.

Eine Zerlegung gilt als **stabil**, wenn die zugeordneten Aussagen zu mindestens 90 % dieselbe Art tragen und die Anteile je Art um höchstens 10 Prozentpunkte abweichen. Die Zahl der Aussagen wird genannt, ist aber kein Maßstab: Sie schwankte in den Proben um rund 10 %.

## Meta-Zerlegung

Die Meta-Zerlegung läuft nur auf ausdrücklichen Auftrag („Meta-Zerlegung"); sonst endet der Skill mit der Grundzerlegung. Sie setzt eine Grundzerlegung voraus und verwendet nur deren Aussagen, keine Rahmen-Zeilen.

**M1 — Meta-Aussage.** Eine Meta-Aussage fasst die Bedeutung von mindestens zwei Aussagen der Ebene darunter zusammen: was sie verbunden sagen, nicht ihre Aufzählung. Sie wird nach Z1 als ein vollständiger deutscher Satz formuliert.

**M2 — Stützen.** Jede Meta-Aussage nennt die Kennungen der Aussagen darunter, auf denen sie beruht. Eine Aussage kann mehrere Meta-Aussagen stützen. Eine Aussage muss keine stützen; Aussagen ohne Meta-Aussage bleiben *nicht aufgenommen*.

**M3 — Einstufung.** Eine Meta-Aussage bekommt eine Art des Katalogs, aber weder Beleg noch Reichweite. Passt keine Art, weil sie nur noch nennt, worum es geht, ist sie ein *Thema*.

**M4 — Nächste Ebene.** Die nächste Ebene wird nur aus den Meta-Aussagen gebildet, die kein Thema sind. Themen werden nicht weiter verdichtet.

**M5 — Ende.** Die Folge endet nach der ersten Ebene, für die einer dieser Fälle gilt, in dieser Reihenfolge geprüft:

| Ende | Fall |
|---|---|
| Kriterium | Alle Meta-Aussagen der Ebene sind Themen. |
| eine Aussage | Die Ebene hat nur noch eine Meta-Aussage, die kein Thema ist. |
| keine Verbindung | Aus der Ebene lässt sich keine Meta-Aussage mehr bilden, weil keine zwei Aussagen zusammen etwas sagen. Diese Ebene bleibt leer und wird nicht gezählt. |
| Grenze | Die Ebene ist Ebene 8. Der Skill meldet, dass die Folge an der Grenze endete. |

**M6 — Zählung.** Je Ebene werden gezählt: Meta-Aussagen, davon Themen, und Aussagen der Ebene darunter, die nicht aufgenommen sind. Die Meta-Zerlegung hat keinen zweiten Durchlauf und kein Urteil *stabil*.
