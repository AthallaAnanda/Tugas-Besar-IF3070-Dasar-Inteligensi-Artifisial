import math


def validate_fields(supplied, specification):
    if not isinstance(supplied, dict):
        raise ValueError("Parameter harus berupa object")
    unknown = set(supplied) - set(specification)
    if unknown:
        raise ValueError("Parameter tidak dikenal: " + ", ".join(sorted(unknown)))

    values = {}
    for name, rules in specification.items():
        value = supplied.get(name, rules["default"])
        valid_type = type(value) is int if rules["type"] == "integer" else type(value) in (int, float)
        try:
            finite = valid_type and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f"{name} harus berupa angka yang valid dan terbatas")
        for boundary, exclusive, lower in (
            ("min", False, True), ("max", False, False),
            ("exclusive_min", True, True), ("exclusive_max", True, False),
        ):
            if boundary not in rules:
                continue
            bound = rules[boundary]
            if lower:
                invalid = value <= bound if exclusive else value < bound
            else:
                invalid = value >= bound if exclusive else value > bound
            if invalid:
                raise ValueError(f"{name} tidak memenuhi batas {boundary}: {bound}")
        values[name] = value
    return values
