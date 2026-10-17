# RAG – Varianten mit Embeddings (Abruf-Güte)

Gleiche 299 gewerteten Testfälle, erste 5 Plätze der Relevanzliste. Auswahl auf denselben Testfällen = Anpassung an diese Fälle; nur als Messung lesen.

| Variante | Treffer | Quote | Erste Angabe | Gegenproben leer |
|---|---|---|---|---|
| Nur Stichwortsuche (ohne Embeddings) | 256/299 | 85.6 % | 79.9 % | 6/10 |
| Embeddings als eine Liste, Gewicht 1,0 | 239/299 | 79.9 % | 72.2 % | 6/10 |
| Embeddings als eine Liste, Gewicht 0,5 | 246/299 | 82.3 % | 75.3 % | 6/10 |
| Embeddings getrennt (Regeln/Quellen/nachrangig), Gewicht 1,0 | 249/299 | 83.3 % | 76.6 % | 6/10 |
| Embeddings getrennt, Gewicht 0,5 | 249/299 | 83.3 % | 77.6 % | 6/10 |
| Embeddings getrennt, Gewicht 0,3 | 253/299 | 84.6 % | 78.3 % | 6/10 |
