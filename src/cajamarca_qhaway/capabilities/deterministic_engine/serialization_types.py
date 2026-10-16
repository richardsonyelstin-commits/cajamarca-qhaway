"""Vocabulario JSON sin punto flotante para contratos y canonización."""

type JSONValue = None | bool | int | str | list[JSONValue] | dict[str, JSONValue]
