from __future__ import annotations


def check(value: object) -> None:
    if not value:
        raise AssertionError
