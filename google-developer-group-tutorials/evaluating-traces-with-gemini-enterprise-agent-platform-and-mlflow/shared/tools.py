"""Two deterministic tools. Fixed fake data keeps the demo repeatable and offline."""

import ast
import operator

FAKE_WEATHER = {
    "cape town": {"condition": "sunny", "temp_c": 22},
    "johannesburg": {"condition": "thunderstorms", "temp_c": 18},
    "london": {"condition": "drizzle", "temp_c": 11},
    "tokyo": {"condition": "clear", "temp_c": 25},
}


def get_weather(city: str) -> dict:
    """Get today's weather for a city.

    Args:
        city: The city name, for example "Cape Town".
    """
    weather = FAKE_WEATHER.get(city.strip().lower())
    if weather is None:
        return {"city": city, "error": "No weather data for this city."}
    return {"city": city, **weather}


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Only numbers and + - * / ** are allowed.")


def calculator(expression: str) -> dict:
    """Evaluate an arithmetic expression such as "(12 + 30) * 2".

    Args:
        expression: The arithmetic expression to evaluate.
    """
    try:
        return {"expression": expression, "result": _evaluate(ast.parse(expression, mode="eval").body)}
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return {"expression": expression, "error": str(error)}


TOOLS = [get_weather, calculator]
