def pytest_collection_modifyitems(config, items):
    for item in items:
        if (
            not item.get_closest_marker("core")
            and not item.get_closest_marker("integration")
            and not item.get_closest_marker("optional")
        ):
            item.add_marker("integration")
