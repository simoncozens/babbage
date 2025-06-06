import json
import sys
from jinja2 import pass_environment
import markupsafe


class Card:
    @pass_environment
    def render(self, jinja, hass):
        classname = self.__class__.__name__
        template = jinja.get_template(f"{classname}.partial.html")
        return markupsafe.Markup(template.render(card=self, hass=hass))

    @property
    def id(self):
        return id(self)


class UnknownCard(Card):
    def __init__(self, **kwargs):
        self.type = kwargs.pop("type", "unknown")
        self.kwargs = kwargs


class GaugeCard(Card):
    def __init__(self, **kwargs):
        self.type = kwargs.pop("type", "gauge")
        self.entity = kwargs.pop("entity", None)
        self.unit = kwargs.pop("unit", "")
        self.min = kwargs.pop("min", 0)
        self.max = kwargs.pop("max", 100)
        self.value = kwargs.pop("value", 0)
        self.icon = kwargs.pop("icon", "mdi:gauge")
        self.name = kwargs.pop("name", None)
        self.needle = kwargs.pop("needle", False)
        self.kwargs = kwargs

    def state(self, hass):
        if self.entity:
            state = hass.states.get(self.entity)
            if state:
                return state["state"]
        return self.value


class TileCard(Card):
    def __init__(self, **kwargs):
        self.type = kwargs.pop("type", "tile")
        self.entity = kwargs.pop("entity", None)
        self.icon = kwargs.pop("icon", "mdi:tile")
        self.name = kwargs.pop("name", None)
        self.value = kwargs.pop("value", None)
        self.unit = kwargs.pop("unit", "")

        self.kwargs = kwargs

    def attributes(self, hass):
        if self.entity:
            state = hass.states.get(self.entity)
            if state:
                return state["attributes"]
        return self.value

    def state(self, hass):
        if self.entity:
            state = hass.states.get(self.entity)
            if state:
                return state["state"]
        return self.value


def make_card(**kwargs):
    type = kwargs.pop("type", "unknown")
    clsname = type.capitalize() + "Card"
    if hasattr(sys.modules[__name__], clsname):
        return getattr(sys.modules[__name__], clsname)(**kwargs)
    else:
        return UnknownCard(type=type, **kwargs)
