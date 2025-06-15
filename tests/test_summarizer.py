from tools.summarizer import summarize_text


def test_summarize_long_text_truncates():
    text = "word " * 6000
    summary = summarize_text(text)
    assert len(summary.split()) <= 200


def test_summarize_empty_input_returns_empty():
    assert summarize_text("") == ""
    assert summarize_text(None) == ""
