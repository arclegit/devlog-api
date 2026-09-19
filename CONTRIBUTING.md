# Contributing

Thanks for improving DevLog API. Please create a focused branch, add or update tests for behavioural changes, and run `pytest -q` before opening a pull request.

Keep migrations additive and reviewable. Never commit `.env` files, credentials, or database dumps. For schema changes, generate an Alembic migration and verify both upgrade and downgrade locally.
