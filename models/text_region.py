from dataclasses import dataclass

@dataclass
class TextRegion:
    id: int
    polygon: list
    text: str
    translated: str = ""