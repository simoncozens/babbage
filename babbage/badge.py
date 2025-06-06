import base64
from dataclasses import dataclass
import io
from typing import Optional
from PIL import Image


@dataclass
class Badge:
    type: str
    entity: str
    show_state: bool
    show_name: bool
    show_icon: bool
    show_entity_picture: bool
    color: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None

    def state(self, hass):
        if self.type != "entity":
            raise ValueError(f"Unsupported badge type: {self.type}")
        if self.entity in hass.states:
            return hass.states[self.entity]
        return None

    def entity_picture(self, hass):
        if state := self.state(hass):
            url = state.get("attributes", {}).get("entity_picture")
            png = hass.get_rest(url, content_type="image/png")
            img = Image.open(io.BytesIO(png))
            img = img.resize((32, 32)).convert("L")
            with io.BytesIO() as output:
                img.save(output, format="PNG")
                base64_utf8_str = base64.b64encode(output.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{base64_utf8_str}"

    def friendly_name(self, hass):
        if self.name:
            return self.name
        if state := self.state(hass):
            return state.get("attributes", {}).get("friendly_name", self.name)
        return self.name
