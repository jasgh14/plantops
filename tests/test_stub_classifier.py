from __future__ import annotations

from src.inference.stub_classifier import StubClassifier


def test_stub_classifier_healthy_keyword() -> None:
    classifier = StubClassifier()
    result = classifier.predict({"filename": "tomato_healthy_leaf.jpg"})

    assert result["predicted_class"] == "healthy"
    assert result["confidence"] >= 0.9
    assert result["source_type"] == "stub_rule"


def test_stub_classifier_disease_keyword() -> None:
    classifier = StubClassifier()
    result = classifier.predict({"filename": "pepper_blight_001.jpg"})

    assert result["predicted_class"] == "blight"
    assert result["source_type"] == "stub_rule"


def test_stub_classifier_hash_fallback_is_stable() -> None:
    classifier = StubClassifier()

    first = classifier.predict({"filename": "mystery_leaf_123.jpg"})
    second = classifier.predict({"filename": "mystery_leaf_123.jpg"})

    assert first == second
    assert first["source_type"] == "stub_hash"
    assert 0.0 <= first["confidence"] <= 1.0
