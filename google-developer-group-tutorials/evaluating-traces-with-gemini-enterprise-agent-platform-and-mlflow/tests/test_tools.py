from shared.tools import calculator, get_weather


def test_weather_is_fixed():
    assert get_weather("Cape Town") == {"city": "Cape Town", "condition": "sunny", "temp_c": 22}


def test_weather_unknown_city():
    assert "error" in get_weather("Atlantis")


def test_calculator():
    assert calculator("(12 + 30) * 2")["result"] == 84


def test_calculator_rejects_code():
    assert "error" in calculator("__import__('os')")
