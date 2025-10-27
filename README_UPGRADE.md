# Concurrency safety helper files for 'Путь кожевника'

These files are intended to be added to your repository to help make
database mutations safer under concurrency and to provide a reproduction
test for concurrency issues.

Files added:
- utils/locks.py             -- per-player asyncio locks
- utils/db_utils.py          -- sqlite helpers: WAL PRAGMA, run_atomic wrapper, example buy
- scripts/test_concurrency.py -- a simple test script that simulates many players

**How to use (recommended minimal steps):**

1. Unzip these files into the repository root so that `utils/` and `scripts/` folders appear.
2. Add imports and use `get_player_lock(player_id)` around critical handlers, e.g. in routers/tutorial.py:

```py
from utils.locks import get_player_lock
lock = get_player_lock(player_id)
async with lock:
    # call into atomic DB helper in utils.db_utils (or your models.buy_item_atomic)
    result = await loop.run_in_executor(None, example_buy_item_atomic, DB_PATH, player_id, item_name)
```

3. Integrate `example_buy_item_atomic` logic into your `database/models.py` as `buy_item_atomic` (recommended).
   The `db_utils.run_atomic` wrapper shows the intended transaction pattern (BEGIN IMMEDIATE -> checks -> mutations -> COMMIT).

4. Enable WAL and busy timeout (db_utils.get_connection already attempts this). For production, ensure your DB connections apply:
   `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; PRAGMA synchronous=NORMAL;`

5. Run the concurrency test locally:
   ```bash
   python3 scripts/test_concurrency.py path/to/game.db
   ```

**Notes**
- These helpers are intentionally non-invasive: they do not change your existing handlers or messages.
- For best results, copy the example transaction logic into your models layer and call it from handlers under a per-player lock.
- For very large concurrency (100-200+), consider moving DB from SQLite to a server DB (Postgres) or sharding write-heavy workloads.
