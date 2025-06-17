import json
import types

from services.learning.skill_spec import (
    generate_skill_specs,
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
