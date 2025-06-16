from __future__ import annotations

"""Utility for regenerating the OpenAPI specification."""

import importlib.util
import pathlib

import yaml

spec = importlib.util.spec_from_file_location(
    "openapi_app", pathlib.Path(__file__).with_name("openapi_app.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Dummy:
    def consolidate(self, memory_type, record):
        return "1"

    def retrieve(self, memory_type, query, limit=5):
        return []


app = module.create_app(Dummy())
path = pathlib.Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"
path.write_text(yaml.dump(app.openapi()))
print(f"Wrote {path}")
