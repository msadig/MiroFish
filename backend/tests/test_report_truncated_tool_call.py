import pytest
from flask import Flask

from app.services.report_agent import ReportAgent
from app.utils.locale import get_locale

# Verbatim Gemini reply that was saved as a whole report section: cut off at "</".
TRUNCATED = (
    '<tool_call>\n{"name": "quick_search", "parameters": {"query": "welcome email", "limit": 12}}\n</'
)


@pytest.mark.parametrize(
    ("response", "count"),
    [
        (TRUNCATED, 1),
        ('<tool_call>\n{"name": "quick_search", "parameters": {"query": "q"}}', 1),
        ('<tool_call>{"name": "quick_search", "parameters": {"q": {"a": 1}}}</tool_call>', 1),
        ("Plain section prose with no tool call.", 0),
    ],
)
def test_parse_tool_calls_tolerates_missing_close_tag(response, count):
    agent = ReportAgent.__new__(ReportAgent)
    assert len(agent._parse_tool_calls(response)) == count


def test_strip_tool_call_fragments():
    assert ReportAgent._strip_tool_call_fragments(TRUNCATED) == ""
    assert ReportAgent._strip_tool_call_fragments("Body text.\n" + TRUNCATED) == "Body text."


@pytest.mark.parametrize(
    ("header", "expected"),
    [("en-US,en;q=0.9", "en"), (None, "en"), ("zh", "zh"), ("zh-CN", "zh"), ("fr", "en")],
)
def test_get_locale_normalises_accept_language(header, expected):
    headers = {"Accept-Language": header} if header else {}
    with Flask(__name__).test_request_context(headers=headers):
        assert get_locale() == expected


def test_language_reminder_appends_to_last_turn_without_mutating_history():
    from app.utils.locale import set_locale

    set_locale("en")
    history = [{"role": "system", "content": "sys"}, {"role": "user", "content": "观察结果"}]
    out = ReportAgent._with_language_reminder(history)
    assert out[-1]["content"].endswith("Please respond in English.")
    assert history[-1]["content"] == "观察结果"
