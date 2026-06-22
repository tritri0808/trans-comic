from dataclasses import dataclass

@dataclass
class Region:
    id: int
    polygon: list
    text: str
    translation: str = ""
    enabled: bool = True
    outline_color: str = "#00FF00"
    render_bg: bool = True
    render_outline: bool = True