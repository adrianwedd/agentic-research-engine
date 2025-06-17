# Concurrency Testing Approach

To ensure collaborative agents can safely operate on a shared scratchpad, the test suite includes a stress test that spawns many concurrent writers. The `DynamicGroupChat` helper exposes an optional lock and the test validates that all updates are preserved.

Run the test with `pytest -k test_concurrent_scratchpad_updates` to simulate 200 simultaneous workers writing to the scratchpad. The final value must match the number of workers, confirming that no updates were lost.
