"""CLI configuration."""
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class Config:
    detail_level: str = "detailed"  # brief | detailed | executive
    days: int = 1
    repos: list[str] = field(default_factory=list)
    model_path: str | None = None  # path to GGUF model
    model_n_ctx: int = 4096
    export_format: str = "markdown"  # markdown | json
    output_path: str | None = None

    @classmethod
    def from_file(cls, path: str | Path = "~/.commitstory.json") -> "Config":
        p = Path(path).expanduser()
        if p.exists():
            data = json.loads(p.read_text())
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: str | Path = "~/.commitstory.json") -> None:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.__dict__, indent=2))
