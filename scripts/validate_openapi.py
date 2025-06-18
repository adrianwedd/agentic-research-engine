import importlib.util
import pathlib

import yaml

root = pathlib.Path(__file__).resolve().parents[1]
spec_path = root / "docs" / "api" / "openapi.yaml"

spec = importlib.util.spec_from_file_location(
    "openapi_app", root / "services" / "ltm_service" / "openapi_app.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Dummy:
    def consolidate(self, memory_type, record):
        return "1"

    def retrieve(self, memory_type, query, limit=5):
        return []

    def semantic_consolidate(self, payload, fmt="jsonld"):
        return []


def main() -> int:
    app = module.create_app(Dummy())
    generated = app.openapi()
    existing = yaml.safe_load(spec_path.read_text())
    if generated != existing:
        print(
            "OpenAPI specification is outdated. Run 'python services/ltm_service/generate_spec.py'."
        )
        return 1
    print("OpenAPI specification is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
