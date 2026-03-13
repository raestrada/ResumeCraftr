from resumecraftr.cli.utils.json import clean_json_response


def test_clean_json_response_simple_object():
    response = '{"a": 1, "b": 2}'
    assert clean_json_response(response) == {"a": 1, "b": 2}


def test_clean_json_response_with_code_fence_and_language():
    response = """```json
{"x": 42}
```"""
    assert clean_json_response(response) == {"x": 42}


def test_clean_json_response_extracts_first_valid_block():
    response = "noise before {\"ok\": true} and some trailing text"
    assert clean_json_response(response) == {"ok": True}


def test_clean_json_response_returns_none_when_no_json():
    assert clean_json_response("this is not json") is None

