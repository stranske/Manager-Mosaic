# Raw store validation evidence

All129 tests pass with91.50% coverage, above the existing80% gate. Focused mypy, Black and Ruff pass. Both schema copies are unchanged. Valid-fixture and original reference tests remain intact; malformed typed-API tests now construct their damaged dataclasses directly because raw admission rejects that structural damage first.

Removing only the structural-violation collection from validate_payload makes both unchanged combined-defect and missing-inferred regressions fail. Byte-identical restoration returns all30 model tests green. Raw RED, restored GREEN and full coverage logs are adjacent. No malformed value is coerced; independent semantic checks run only when their prerequisite inputs have usable types. Store.from_dict rejects malformed structure with one aggregate ValueError and retains structurally valid semantic inspection through validate(Store).
