# Mistral-Geschwindigkeitsmessung 2026-10-09

Entwurf. Nur erfundene Fragen. Unabhängig von der App (direkte API-Aufrufe).

Alle Modelle der Liste: codestral-2508, codestral-embed, codestral-embed-2505, codestral-latest, glm-5-2, labs-leanstral-1-5, labs-leanstral-1-5-1, magistral-medium-latest, magistral-small-latest, ministral-14b-2512, ministral-14b-latest, ministral-3b-2512, ministral-3b-latest, ministral-8b-2512, ministral-8b-latest, mistral-code-fim-latest, mistral-code-latest, mistral-embed, mistral-embed-2312, mistral-large-2512, mistral-large-4, mistral-large-4-0, mistral-large-latest, mistral-medium, mistral-medium-2604, mistral-medium-3, mistral-medium-3-5, mistral-medium-3.5, mistral-medium-latest, mistral-moderation-2603, mistral-ocr-2512, mistral-ocr-3, mistral-ocr-3-0, mistral-ocr-4, mistral-ocr-4-0, mistral-ocr-4-1, mistral-ocr-latest, mistral-small-2603, mistral-small-latest, mistral-vibe-cli-fast, mistral-vibe-cli-latest, mistral-vibe-cli-with-tools, voxtral-mini-2602, voxtral-mini-latest, voxtral-mini-realtime-2602, voxtral-mini-realtime-latest, voxtral-mini-transcribe-realtime-2602, voxtral-mini-tts-2603, voxtral-mini-tts-latest, voxtral-small-2507, voxtral-small-latest, zai-glm-5, zai-glm-5-2, zai-glm-5-3, zai-glm-latest

Getestete Modelle: magistral-medium-latest, magistral-small-latest, ministral-14b-2512, ministral-14b-latest, ministral-3b-2512, ministral-3b-latest, ministral-8b-2512, ministral-8b-latest, mistral-large-2512, mistral-large-4 (je 2 Durchläufe x 3 Fragen, Zeitgrenze 90 s)

magistral-medium-latest: Mittelwert-Median 0.8 s, längster 1.3 s, JSON richtig 6/6, Fehler 0
magistral-small-latest: Mittelwert-Median 0.8 s, längster 1.3 s, JSON richtig 6/6, Fehler 0
ministral-14b-2512: Mittelwert-Median 1.5 s, längster 2.4 s, JSON richtig 6/6, Fehler 0
ministral-14b-latest: Mittelwert-Median 1.4 s, längster 2.8 s, JSON richtig 6/6, Fehler 0
ministral-3b-2512: Mittelwert-Median 0.8 s, längster 1.2 s, JSON richtig 6/6, Fehler 0
ministral-3b-latest: Mittelwert-Median 0.7 s, längster 1.2 s, JSON richtig 6/6, Fehler 0
ministral-8b-2512: Mittelwert-Median 1.1 s, längster 2.4 s, JSON richtig 6/6, Fehler 0
ministral-8b-latest: Mittelwert-Median 1.4 s, längster 2.0 s, JSON richtig 6/6, Fehler 0
mistral-large-2512: Mittelwert-Median 1.1 s, längster 2.0 s, JSON richtig 6/6, Fehler 0
mistral-large-4: Mittelwert-Median 24.7 s, längster 33.8 s, JSON richtig 6/6, Fehler 0

| Modell | Dauer (Median) | längster | erstes Zeichen (Median) | JSON richtig | Fehler |
|---|---|---|---|---|---|
| ministral-3b-latest | 0.7 s | 1.2 s | 0.3 s | 6/6 | 0 |
| ministral-3b-2512 | 0.8 s | 1.2 s | 0.3 s | 6/6 | 0 |
| magistral-medium-latest | 0.8 s | 1.3 s | 0.3 s | 6/6 | 0 |
| magistral-small-latest | 0.8 s | 1.3 s | 0.4 s | 6/6 | 0 |
| ministral-8b-2512 | 1.1 s | 2.4 s | 0.3 s | 6/6 | 0 |
| mistral-large-2512 | 1.1 s | 2.0 s | 0.5 s | 6/6 | 0 |
| ministral-14b-latest | 1.4 s | 2.8 s | 0.3 s | 6/6 | 0 |
| ministral-8b-latest | 1.4 s | 2.0 s | 0.3 s | 6/6 | 0 |
| ministral-14b-2512 | 1.5 s | 2.4 s | 0.3 s | 6/6 | 0 |
| mistral-large-4 | 24.7 s | 33.8 s | 23.7 s | 6/6 | 0 |
