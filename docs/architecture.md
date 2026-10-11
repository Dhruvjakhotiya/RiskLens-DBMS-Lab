# Architecture

Browser requests reach Flask routes in `app.py`. Routes validate input and call service modules. Services use `database.db` for foreign-key-enabled SQLite transactions. The ML modules train serialized sklearn pipelines, generate probabilities and model-association explanations, and save evaluation JSON/plots. Templates render persisted data; artifacts are local and reproducible.
