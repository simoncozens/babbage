import base64
import io
import json
import logging
import os
import time

from aiohttp import web

from babbage.hass import HassDashboard
from babbage.render import render_html

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DASHBOARD_INDEX = 0 # This will rotate, one day.

class Server:
    def __init__(self, config, host: str = "0.0.0.0", httpPort: int = 2300, debug: bool = False):
        self.config = config
        self.host = host
        self.httpPort = httpPort
        self.debug = debug
        self.hass = HassDashboard(config["ha_url"], config["access_token"], config["dashboard_name"])
    
    @property
    def refresh_rate(self) -> int:
        return self.config.get("refresh_rate", 500)

    def run(self) -> None:
        httpApp = web.Application()

        routes = [
            web.get("/api/display", self.displayHandler),
            web.post("/api/log", self.logHandler),
            web.get("/api/setup/", self.setupHandler),
            web.static('/', './static', show_index=True),
        ]
        httpApp.add_routes(routes)
        web.run_app(httpApp, host=self.host, port=self.httpPort)

    async def logHandler(self, request: web.Request) -> web.Response:
        kwargs = await request.json()
        logging.info(f"Logs {request.remote}: {kwargs}")
        # Post this back to HASS
        return web.Response(status=204)

    async def setupHandler(self, request: web.Request) -> web.Response:
        logging.info(
            f"Setup request from {request.remote}: {request.rel_url.query}"
        )
        # Dump all headers and request body
        logging.info(f"Headers: {request.headers}")
        logging.info(f"Body: {request.json() if request.can_read_body else 'No body'}")

        return web.Response(
            text=json.dumps({
                "api_key": "12345",
                "friendly_id": "ABC123",
                "iamge_url": "static/homeassistant.png",
                "message": "Setup successful",
            }), content_type="application/json"
        )

    async def displayHandler(
        self, request: web.Request
    ) -> web.Response:
        await self.hass.fetch()
        html = self.hass.render(DASHBOARD_INDEX)
        if self.debug:
            open("debug.html", "w").write(html)
        img = render_html(html)
        out_filename = f"{self.config['dashboard_name']}-{DASHBOARD_INDEX}.png"
        if request.rel_url.query.get("base_64") or request.headers.get("BASE64"):
            logger.info("Returning image as base64")
            with io.BytesIO() as output:
                img.save(output, format="png")
                base64_utf8_str = base64.b64encode(output.getvalue()).decode("utf-8")
            image_url = f"data:image/png;base64,{base64_utf8_str}"
        else:
            img.save("static/"+out_filename, format="png")
            image_url = f"http://{request.host}/{os.path.basename(out_filename)}"
        return web.Response(
            text=json.dumps({
                # Use a nonce to force TRMNL to reload the image
                "filename": str(time.time())+"-"+out_filename,
                "image_url": image_url,
                "image_url_timeout": 0,
                "reset_firmware": False,                
                "update_firmware": False,
                "refresh_rate": self.refresh_rate,

            }), content_type="application/json"
        )
 