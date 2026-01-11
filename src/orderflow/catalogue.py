"""Catalogue loader and access helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from orderflow.domain import CatalogueItem


@dataclass(frozen=True)
class Catalogue:
    """Represents a catalogue of available items."""

    items: Dict[str, CatalogueItem]

    @staticmethod
    def load(path: str | None) -> "Catalogue":
        """Load catalogue data from the provided path or default file."""

        if path is None:
            path = str(_default_catalogue_path())
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = {
            item["sku"].upper(): CatalogueItem(
                sku=item["sku"].upper(),
                name=item["name"],
                unit_price_pence=int(item["unit_price_pence"]),
            )
            for item in data.get("items", [])
        }
        return Catalogue(items=items)

    def get(self, sku: str) -> Optional[CatalogueItem]:
        """Retrieve a catalogue item by SKU."""

        return self.items.get(sku.upper())

    def has(self, sku: str) -> bool:
        """Check whether a SKU exists in the catalogue."""

        return sku.upper() in self.items


def _default_catalogue_path() -> Path:
    """Return the default catalogue path shipped with the package."""

    return Path(__file__).resolve().parents[2] / "data" / "catalogue.json"
