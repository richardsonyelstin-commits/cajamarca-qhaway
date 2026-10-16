"""Aceptación 011: deferred."""


def test_deferred_rules_never_enter_core(engine, evaluate, payload, corpus):
    import copy

    for code in [
        "short-tender-window",
        "direct-award-threshold",
        "contract-splitting-orders",
        "direct-administration-equipment-rent",
    ]:
        value = copy.deepcopy(payload)
        value["scopes"][0]["rules"] = [code]
        assert evaluate(value)["problems"][0]["code"] == "UNSUPPORTED_VERSION"
