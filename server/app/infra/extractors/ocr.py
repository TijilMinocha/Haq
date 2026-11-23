from dataclasses import dataclass


@dataclass(frozen=True)
class OcrWord:
    text: str
    confidence: float
    left: int
    width: int

    @property
    def center(self) -> float:
        return self.left + self.width / 2


@dataclass(frozen=True)
class OcrLine:
    words: tuple[OcrWord, ...]

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


@dataclass(frozen=True)
class OcrPage:
    lines: tuple[OcrLine, ...]

    @property
    def confidence(self) -> float:
        confs = [w.confidence for line in self.lines for w in line.words]
        return sum(confs) / len(confs) if confs else 0.0

    @classmethod
    def from_text(cls, text: str, confidence: float = 0.9) -> "OcrPage":
        """Builds a page from plain text, giving each word an even column position."""
        lines = []
        for raw in text.splitlines():
            words, col = [], 0
            for token in raw.split(" "):
                if token:
                    words.append(OcrWord(token, confidence, col * 10, len(token) * 10))
                col += len(token) + 1
            if words:
                lines.append(OcrLine(tuple(words)))
        return cls(tuple(lines))
