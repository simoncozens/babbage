from functools import cached_property
from jinja2 import pass_environment
import markupsafe


class Card:
    _hass: "HassDashboard"
    entity = None
    value = None

    @pass_environment
    def render(self, jinja, hass, debug=False):
        classname = self.__class__.__name__
        template = jinja.get_template(f"{classname}.partial.html")
        return markupsafe.Markup(template.render(card=self, hass=hass, debug=debug))

    @property
    def id(self):
        return id(self)

    @property
    def attributes(self):
        if hasattr(self, "entity") and self.entity:
            state = self._hass.states.get(self.entity)
            if state:
                return state["attributes"]
        return self.value

    @property
    def state(self):
        if hasattr(self, "entity") and self.entity:
            state = self._hass.states.get(self.entity)
            if state:
                return state["state"]
        return self.value


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


class TileCard(Card):
    def __init__(self, **kwargs):
        self.type = kwargs.pop("type", "tile")
        self.entity = kwargs.pop("entity", None)
        self.icon = kwargs.pop("icon", "mdi:tile")
        self.name = kwargs.pop("name", None)
        self.value = kwargs.pop("value", None)
        self.unit = kwargs.pop("unit", "")

        self.kwargs = kwargs


class WeatherForecastCard(Card):
    STATES = {
        "clear-night": ("Clear, night", "mdi-weather-night"),
        "cloudy": ("Cloudy", "mdi-weather-cloudy"),
        "fog": ("Fog", "mdi-weather-fog"),
        "hail": ("Hail", "mdi-weather-hail"),
        "lightning": ("Lightning", "mdi-weather-lightning"),
        "partlycloudy": ("Partly cloudy", "mdi-weather-partly-cloudy"),
        "pouring": ("Pouring", "mdi-weather-pouring"),
        "rainy": ("Rainy", "mdi-weather-rainy"),
        "sunny": ("Sunny", "mdi-weather-sunny"),
        "snowy": ("Snowy", "mdi-weather-snowy"),
        "snowy-rainy": ("Snowy and rainy", "mdi-weather-snowy-rainy"),
        "windy": ("Windy", "mdi-weather-windy"),
        "windy-variant": ("Windy", "mdi-weather-windy-variant"),
        "exceptional": ("Exceptional", "mdi-alert"),
    }

    def __init__(self, **kwargs):
        self.entity = kwargs.pop("entity", None)
        self.show_current = kwargs.pop("show_current", True)
        self.show_forecast = kwargs.pop("show_forecast", True)
        self.forecast_type = kwargs.pop("forecast_type", "hourly")
        self.kwargs = kwargs

    @property
    def weather_name(self):
        return self.STATES.get(self.state, ("Unknown", "mdi-alert"))[0]

    def weather_icon(self, icon_for=None):
        return self.STATES.get(icon_for or self.state, ("", "mdi-alert"))[1]

    @property
    def forecast_high(self):
        f = self.forecast
        return max(h["temperature"] for h in f)

    @property
    def forecast_low(self):
        f = self.forecast
        return min(h["temperature"] for h in f)

    @cached_property
    def forecast(self):
        f = self._hass.post_rest(
            "/api/services/weather/get_forecasts?return_response",
            {
                "entity_id": self.entity,
                "type": self.forecast_type,
            },
        )
        return f["service_response"][self.entity]["forecast"]
