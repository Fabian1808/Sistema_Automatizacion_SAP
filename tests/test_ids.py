from app.utils.ids import analyze_ids


def test_single_valid():
    result = analyze_ids(["1042866626"])
    assert result["valid"] == ["1042866626"]
    assert result["duplicates"] == []
    assert result["invalid"] == []


def test_spaces_and_empty_lines_removed():
    result = analyze_ids([" 1042866626 ", "", "   ", "1042866631"])
    assert result["valid"] == ["1042866626", "1042866631"]


def test_duplicates_detected():
    result = analyze_ids(["1042866626", "1042866626"])
    assert result["valid"] == ["1042866626"]
    assert result["duplicates"] == ["1042866626"]


def test_invalid_values():
    result = analyze_ids(["1042866626", "ABC123", "12.5", "-1"])
    assert result["valid"] == ["1042866626"]
    assert len(result["invalid"]) == 3


def test_order_preserved():
    result = analyze_ids(["1042866672", "1042866626", "1042866631"])
    assert result["valid"] == ["1042866672", "1042866626", "1042866631"]