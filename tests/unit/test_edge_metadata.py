from engine.orchestration_engine import create_orchestration_engine


def test_add_edge_with_metadata():
    eng = create_orchestration_engine()
    eng.add_node("A", lambda s, sp: s)
    eng.add_node("B", lambda s, sp: s)

    eng.add_edge("A", "B", edge_type="ok", metadata={"custom": 1})

    assert eng.edges[0].edge_type == "ok"
    assert eng.edges[0].metadata["custom"] == 1
    eng.build()
    edges = eng.get_edges("A", "ok")
    assert len(edges) == 1
    assert edges[0].metadata["custom"] == 1


def test_labeled_edge_export_dot():
    eng = create_orchestration_engine()
    eng.add_node("A", lambda s, sp: s)
    eng.add_node("B", lambda s, sp: s)
    eng.add_edge("A", "B", edge_type="label")
    eng.build()
    dot = eng.export_dot()
    assert '"A" -> "B" [label="label"];' in dot
