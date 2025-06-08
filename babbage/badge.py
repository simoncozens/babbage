import base64
from dataclasses import dataclass
import io
from typing import Optional
from PIL import Image

from babbage.cards import Card


@dataclass
class Badge(Card):
    type: str
    show_state: bool
    show_name: bool
    show_icon: bool
    show_entity_picture: bool
    _hass: "HassDashboard"
    entity: None
    color: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None

    @property
    def entity_picture(self):
        if self.attributes:
            url = self.attributes.get("entity_picture")
            if url:
                png = self._hass.get_rest(url, content_type="image/png")
                img = Image.open(io.BytesIO(png))
                img = img.resize((32, 32)).convert("L")
                with io.BytesIO() as output:
                    img.save(output, format="PNG")
                    base64_utf8_str = base64.b64encode(output.getvalue()).decode(
                        "utf-8"
                    )
                return f"data:image/png;base64,{base64_utf8_str}"

    @property
    def friendly_name(self):
        if self.name:
            return self.name
        if self.attributes:
            return self.attributes.get("friendly_name", self.name)
        return self.name
