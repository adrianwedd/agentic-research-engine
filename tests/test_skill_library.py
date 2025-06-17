from services.ltm_service.skill_library import Skill, SkillLibrary


def test_store_and_query_skill():
    lib = SkillLibrary()
    sid = lib.add(Skill(policy="p", embedding=[1.0, 0.0], metadata={"name": "a"}))
    assert sid
    retrieved = lib.get(sid)
    assert retrieved and retrieved.metadata["name"] == "a"
    results = lib.query([1.0, 0.0], limit=1)
    assert results and results[0].metadata["name"] == "a"
