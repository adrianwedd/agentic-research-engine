# Task P3-TEST-01
## Reasoning
Replace deprecated `datetime.utcnow()` calls to ensure Python 3.12 compatibility.
## Plan
- Search repository for `utcnow` usage.
- Update calls to `datetime.now(datetime.UTC)`.
- Add regression test verifying timezone-aware timestamps.
## Expected Outputs
- Updated modules such as `services/tool_registry/__init__.py`.
- Passing tests.
