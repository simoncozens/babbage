import datetime
import json
from dataclasses import dataclass
import pprint
import re
from typing import List

import requests
from jinja2 import Environment, PackageLoader, select_autoescape
from websockets.asyncio.client import connect

from babbage.badge import Badge
from babbage.cards import Card
import babbage.cards as cards


@dataclass
class Section:
    type: str
    cards: List[Card]
    _hass: "HassDashboard"

    def __post_init__(self):
        self.cards = [self._hass.make_card(**card) for card in self.cards]


@dataclass
class SectionsView:
    title: str
    icon: str
    theme: str
    type: str
    sections: List[Section]
    badges: List[Badge]
    max_columns: int
    cards: List[Card]
    _hass: "HassDashboard"

    def __post_init__(self):
        self.sections = [
            Section(_hass=self._hass, **section) for section in self.sections
        ]
        self.badges = [Badge(_hass=self._hass, **badge) for badge in self.badges]
        self.cards = [self._hass.make_card(**card) for card in self.cards]


@dataclass
class PanelView:
    type: str
    cards: List[Card]
    icon: str
    _hass: "HassDashboard"
    path: str = ""

    def __post_init__(self):
        self.cards = [self._hass.make_card(**card) for card in self.cards]


class HassDashboard:
    def __init__(
        self, ha_url: str, access_token: str, url_path: str, debug: bool = False
    ):
        self.ha_url = ha_url
        self.access_token = access_token
        self.url_path = url_path
        self.debug = debug
        self.views = []
        self.states = []

    def _convert_views(self, views):
        view_objs = []
        for view in views:
            if view["type"] == "panel":
                view_objs.append(PanelView(_hass=self, **view))
            elif view["type"] == "sections":
                view_objs.append(SectionsView(_hass=self, **view))
            else:
                raise ValueError(f"Unknown view type: {view['type']}")
        return view_objs

    def make_card(self, **kwargs):
        type = kwargs.pop("type", "unknown")
        clsname = re.sub(r"\W+", "", type.title()) + "Card"
        if hasattr(cards, clsname):
            card = getattr(cards, clsname)(**kwargs)
        else:
            card = cards.UnknownCard(type=type, **kwargs)
        card._hass = self
        return card

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

    def render(self, view_index: int = 0, **kwargs):
        env = Environment(
            loader=PackageLoader("babbage", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        env.filters["format_date"] = (
            lambda x, fmt="%Y-%m-%d %H:%M:%S": datetime.datetime.fromisoformat(
                x
            ).strftime(fmt)
        )
        template = env.get_template("dashboard.html")
        view = self.views[view_index]
        return template.render(view=view, hass=self, debug=self.debug, **kwargs)

    def get_rest(self, url_path, content_type="application/json"):
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-type": content_type,
        }
        response = requests.get(f"http://{self.ha_url}{url_path}", headers=headers)
        response.raise_for_status()
        if content_type == "application/json":
            return response.json()
        return response.content

    def post_rest(self, url_path, data, content_type="application/json"):
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-type": content_type,
        }
        response = requests.post(
            f"http://{self.ha_url}{url_path}", json=data, headers=headers
        )
        response.raise_for_status()
        if content_type == "application/json":
            return response.json()
