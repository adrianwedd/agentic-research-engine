from services.ltm_service.skill_library import SkillLibrary


def test_add_freeze_and_compose():
    lib = SkillLibrary()
    sid = lib.add_skill({"actions": ["a"]}, "h1", {"domain": "test"})
    lib.freeze_skill(sid)
    assert lib.is_frozen(sid)

    # new skill composed from frozen one
    cid = lib.compose_skill([sid], "combined")
    assert cid != sid
    results = lib.query_by_metadata({"prompt": "combined"})
    assert results and results[0]["id"] == cid
