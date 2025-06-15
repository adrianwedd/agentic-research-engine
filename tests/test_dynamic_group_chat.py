from engine.collaboration.group_chat import DynamicGroupChat


def test_message_passing():
    chat = DynamicGroupChat({})
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.post_message("A", "hello")
    msgs_b = chat.get_messages("B")
    assert msgs_b and msgs_b[-1]["content"] == "hello"


def test_shared_workspace():
    workspace = {}
    chat = DynamicGroupChat(workspace)
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.update_workspace("A", "note", "value")
    assert workspace["note"] == "value"
