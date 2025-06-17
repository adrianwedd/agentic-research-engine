import importlib


def test_import_engine():
    assert importlib.import_module("engine")


def test_import_agents():
    assert importlib.import_module("agents")
