"""Lokaler Start (Windows, Linux, Mac):  python -m schnellcheck  [--port 8100]
Für den Betrieb im Internet stattdessen waitress verwenden (siehe schnellcheck/README.md)."""
import argparse
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from schnellcheck.web import app


class _Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _Leise(WSGIRequestHandler):
    def log_message(self, *args):  # keine Zugriffsprotokolle mit Pfaden/Adressen
        pass


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--host", default="127.0.0.1")
    a.add_argument("--port", type=int, default=8100)
    o = a.parse_args()
    print(f"KSK-Schnellcheck läuft: http://{o.host}:{o.port}  (Beenden mit Strg+C)")
    make_server(o.host, o.port, app, server_class=_Server, handler_class=_Leise).serve_forever()
