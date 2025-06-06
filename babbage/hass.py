import json
from dataclasses import dataclass
from typing import List

import requests
from jinja2 import Environment, PackageLoader, select_autoescape
from websockets.asyncio.client import connect

from babbage.badge import Badge
from babbage.cards import Card, make_card


@dataclass
class Section:
    type: str
    cards: List[Card]

    def __post_init__(self):
        self.cards = [make_card(**card) for card in self.cards]


@dataclass
class View:
    title: str
    icon: str
    theme: str
    type: str
    sections: List[Section]
    badges: List[Badge]
    max_columns: int
    cards: List[Card]

    def __post_init__(self):
        self.sections = [Section(**section) for section in self.sections]
        self.badges = [Badge(**badge) for badge in self.badges]
        self.cards = [make_card(**card) for card in self.cards]


class HassDashboard:
    def __init__(self, ha_url: str, access_token: str, url_path: str):
        self.ha_url = ha_url
        self.access_token = access_token
        self.url_path = url_path
        self.views = []
        self.states = []

    def _convert_views(self, views):
        return [View(**view) for view in views]

    async def fetch(self):
        async with connect(
            f"ws://{self.ha_url}/api/websocket", max_size=None
        ) as websocket:
            message = json.loads(await websocket.recv())
            assert message["type"] == "auth_required", "Expected auth_required message"
            await websocket.send(
                json.dumps({"type": "auth", "access_token": self.access_token})
            )
            message = json.loads(await websocket.recv())
            assert message["type"] == "auth_ok", "Expected auth_ok message"
            await websocket.send(
                json.dumps(
                    {"id": 1, "type": "lovelace/config", "url_path": self.url_path}
                )
            )
            message = json.loads(await websocket.recv())
            self.views = self._convert_views(message["result"]["views"])
            await websocket.send(json.dumps({"id": 2, "type": "get_states"}))
            message = json.loads(await websocket.recv())
            self.states = {x["entity_id"]: x for x in message["result"]}

    def render(self, view_index: int = 0):
        env = Environment(
            loader=PackageLoader("babbage", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("dashboard.html")
        view = self.views[view_index]
        return template.render(view=view, hass=self)

    def get_rest(self, url_path, content_type="application/json"):
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "content-type": content_type,
        }
        response = requests.get(f"http://{self.ha_url}{url_path}", headers=headers)
        response.raise_for_status()
        if content_type == "application/json":
            return response.json()
        return response.content
