"""Test des Nutzers im Codespace (16.10.2026): Mistral antwortete „402 Payment Required“. Bei einem gesperrten Zugang
(401/402/403) nennt der Chat die Ursache statt „Bitte stellen Sie Ihre Frage erneut“; andere Modellfehler (auch 429 nach
den Wiederholungen, Befund M6) behalten den allgemeinen Text. Ohne Netz, Testdoppel."""
from __future__ import annotations

import unittest

from app import router
from app.llm.base import LLMFehlgeschlagen
from app.llm.fake import FakeLLM

FRAGE = "Wir sind eine Bäckerei und machen Werbung für unser eigenes Geschäft. 2026 haben wir 1.500 € gezahlt."


class _Gesperrt(FakeLLM):
    def __init__(self, status):
        super().__init__()
        self._status = status

    def extrahiere_fakten(self, *args, **kwargs):
        raise LLMFehlgeschlagen("Mistral-Aufruf: HTTP-Fehler (Testdoppel).", status=self._status)


class ZugangGesperrt(unittest.TestCase):
    def test_402_nennt_die_ursache(self):
        for status in (401, 402, 403):
            with self.subTest(status=status):
                a = router.bearbeite_frage(FRAGE, _Gesperrt(status))
                self.assertEqual(a.rueckfragen, [router.ZUGANG_GESPERRT_RUECKFRAGE])
                self.assertNotIn("erneut.", a.antwort)

    def test_andere_fehler_behalten_den_allgemeinen_text(self):
        for status in (429, 503, None):
            with self.subTest(status=status):
                a = router.bearbeite_frage(FRAGE, _Gesperrt(status))
                self.assertEqual(a.rueckfragen, [router.MODELLFEHLER_RUECKFRAGE])


if __name__ == "__main__":
    unittest.main()
