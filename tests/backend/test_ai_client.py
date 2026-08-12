from api.schemas.extraction import MealExtractionData, WorkoutExtractionData
from api.services.ai_client import _strict_schema


def _assert_strict(schema: dict) -> None:
    if "properties" in schema:
        assert set(schema["required"]) == set(schema["properties"].keys())
        assert schema["additionalProperties"] is False
        assert "default" not in schema
        for value in schema["properties"].values():
            _assert_strict(value)
    if "items" in schema:
        _assert_strict(schema["items"])
    if "anyOf" in schema:
        for sub in schema["anyOf"]:
            _assert_strict(sub)


def test_strict_schema_requires_every_property_for_workout_extraction() -> None:
    _assert_strict(_strict_schema(WorkoutExtractionData.model_json_schema()))


def test_strict_schema_requires_every_property_for_meal_extraction() -> None:
    _assert_strict(_strict_schema(MealExtractionData.model_json_schema()))
