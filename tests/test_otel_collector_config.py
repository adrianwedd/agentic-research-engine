import yaml


def load_config():
    with open("otel-collector-config.yaml", "r") as f:
        return yaml.safe_load(f)


def test_processors_configured():
    config = load_config()
    processors = config["processors"]
    assert "memory_limiter" in processors
    assert "batch" in processors
    assert "queued_retry" in processors
    assert "attributes" in processors
    actions = processors["attributes"]["actions"]
    env_action = next((a for a in actions if a["key"] == "environment"), None)
    version_action = next((a for a in actions if a["key"] == "service.version"), None)
    assert env_action == {
        "key": "environment",
        "value": "${ENVIRONMENT}",
        "action": "upsert",
    }
    assert version_action == {
        "key": "service.version",
        "value": "${SERVICE_VERSION}",
        "action": "upsert",
    }


def test_pipeline_uses_processors():
    config = load_config()
    pipeline = config["service"]["pipelines"]["traces"]
    processors = pipeline["processors"]
    for name in ["memory_limiter", "batch", "queued_retry", "attributes"]:
        assert name in processors
