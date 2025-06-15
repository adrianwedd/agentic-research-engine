#!/usr/bin/env python
"""Import the BrowseComp dataset into LangSmith."""
from services.tracing.langsmith_integration import configure_langsmith, import_dataset


def main() -> None:
    configure_langsmith("agentic-research-engine")
    import_dataset("benchmarks/browsecomp/dataset_v1.json", "BrowseComp")


if __name__ == "__main__":
    main()
