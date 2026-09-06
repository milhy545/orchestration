from aiohttp import web

from .app import create_app


web.run_app(create_app(), host="0.0.0.0", port=7080)
