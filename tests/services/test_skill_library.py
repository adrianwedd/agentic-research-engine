from services.ltm_service.skill_library import SkillLibrary


def test_add_and_query():
    lib = SkillLibrary()
    sid = lib.add_skill({"steps": [1]}, "hello", {"domain": "test"})
    assert sid

    results = lib.query_by_vector("hello")
    assert results and results[0]["id"] == sid

    results = lib.query_by_metadata({"domain": "test"})
    assert results and results[0]["id"] == sid
