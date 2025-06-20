import logging
from importlib import import_module

import anyio
from starlette.responses import Response

# Import dynamique du transport SSE du SDK
sse_mod = import_module("mcp.server.sse")
SseServerTransport = sse_mod.SseServerTransport

# Sauvegarde de la méthode d'origine
_original_connect_sse = SseServerTransport.connect_sse

# Ce patch intercepte BrokenResourceError pour éviter qu'une déconnexion
# brutale d'un client SSE ne coupe tout le serveur.


async def _safe_connect_sse(self, scope, receive, send):
    """Capture BrokenResourceError et renvoie 204."""
    try:
        return await _original_connect_sse(self, scope, receive, send)
    except anyio.BrokenResourceError:
        logging.warning("SSE client disconnected \u2013 BrokenResourceError handled")
        response = Response(status_code=204)
        await response(scope, receive, send)
        return


# Monkey-patch
SseServerTransport.connect_sse = _safe_connect_sse
