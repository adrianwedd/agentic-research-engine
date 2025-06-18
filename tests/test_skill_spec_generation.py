import json
import sys
import types

# flake8: noqa: E402

sys.modules.setdefault("openai", types.SimpleNamespace(OpenAI=types.SimpleNamespace()))
sys.modules.setdefault("requests", types.SimpleNamespace(post=lambda *a, **k: None))

# minimal stubs for optional deps imported by ltm_service
splitter_mod = types.ModuleType("langchain.text_splitter")
splitter_mod.RecursiveCharacterTextSplitter = lambda **_: types.SimpleNamespace(
    split_text=lambda text: [text]
)
langchain_mod = types.ModuleType("langchain")
sys.modules.setdefault("langchain", langchain_mod)
sys.modules.setdefault("langchain.text_splitter", splitter_mod)

fastapi_mod = types.ModuleType("fastapi")
fastapi_mod.FastAPI = object
fastapi_mod.Body = object
fastapi_mod.Header = object
fastapi_mod.HTTPException = Exception
fastapi_mod.Query = object
responses_mod = types.ModuleType("fastapi.responses")
responses_mod.RedirectResponse = object
sys.modules.setdefault("fastapi.responses", responses_mod)
sys.modules.setdefault("fastapi", fastapi_mod)

otel_mod = types.ModuleType("opentelemetry")
trace_mod = types.ModuleType("opentelemetry.trace")
trace_mod.get_tracer = lambda *_, **__: types.SimpleNamespace(
    start_as_current_span=lambda *a, **k: types.SimpleNamespace(
        __enter__=lambda *a2, **k2: None, __exit__=lambda *a2, **k2: None
    )
)
otel_mod.trace = trace_mod
otel_mod.metrics = types.SimpleNamespace()
sys.modules.setdefault("opentelemetry", otel_mod)
sys.modules.setdefault("opentelemetry.trace", trace_mod)
sys.modules.setdefault(
    "opentelemetry.exporter", types.ModuleType("opentelemetry.exporter")
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp", types.ModuleType("opentelemetry.exporter.otlp")
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto",
    types.ModuleType("opentelemetry.exporter.otlp.proto"),
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.grpc",
    types.ModuleType("opentelemetry.exporter.otlp.proto.grpc"),
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.grpc.metric_exporter",
    types.ModuleType("opentelemetry.exporter.otlp.proto.grpc.metric_exporter"),
)
sys.modules[
    "opentelemetry.exporter.otlp.proto.grpc.metric_exporter"
].OTLPMetricExporter = object

pydantic_mod = types.ModuleType("pydantic")
pydantic_mod.BaseModel = type(
    "BaseModel", (), {"model_rebuild": classmethod(lambda cls: None)}
)
pydantic_mod.Field = lambda *args, **kwargs: None
sys.modules.setdefault("pydantic", pydantic_mod)
sys.modules.setdefault(
    "services.monitoring.system_monitor",
    types.SimpleNamespace(SystemMonitor=object),
)

from services.learning.skill_spec import (
    generate_skill_specs,
    generate_skill_specs_from_agent,
    parse_skill_specs,
    store_skill_specs,
)
from services.ltm_service.skill_library import SkillLibrary


def test_parse_skill_specs():
    text = json.dumps(
        {
            "sub_tasks": [
                {
                    "name": "move block",
                    "termination_condition": "position == target",
                    "reward_function": "return float(position==target)",
                }
            ]
        }
    )
    specs = parse_skill_specs(text)
    assert len(specs) == 1
    assert specs[0].name == "move block"


def test_generate_and_store_specs():
    # fake llm returning deterministic specs
    def fake_llm(msgs):
        return json.dumps(
            {
                "sub_tasks": [
                    {
                        "name": "pick up",
                        "termination_condition": "holding == True",
                        "reward_function": "return 1.0 if holding else 0.0",
                    }
                ]
            }
        )

    llm = types.SimpleNamespace(invoke=fake_llm)
    template = "TASK: {task}"
    specs = generate_skill_specs("stack blocks", llm=llm, template=template)
    assert specs and specs[0].termination_condition

    lib = SkillLibrary()
    ids = store_skill_specs(specs, lib)
    assert ids
    stored = lib.get_skill(ids[0])
    assert stored["skill_metadata"]["skill_spec"]["name"] == "pick up"


def test_generate_skill_specs_from_agent():
    calls = []

    def fake_llm(msgs):
        calls.append(msgs[0]["content"])
        return json.dumps(
            {
                "sub_tasks": [
                    {
                        "name": "demo",
                        "termination_condition": "done",
                        "reward_function": "return 1.0",
                    }
                ]
            }
        )

    llm = types.SimpleNamespace(invoke=fake_llm)
    specs = generate_skill_specs_from_agent("demo task", llm=llm)
    assert calls and "demo task" in calls[0]

    lib = SkillLibrary()
    sid = store_skill_specs(specs, lib)[0]
    stored = lib.get_skill(sid)
    meta = stored["skill_metadata"]["skill_spec"]
    assert meta["termination_condition"] == "done"
    assert meta["reward_function"] == "return 1.0"
