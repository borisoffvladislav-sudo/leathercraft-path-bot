import sqlite3
import time
import typing
import contextlib

# Utility functions to open sqlite connections with safer defaults for concurrency.
# These wrappers are intentionally conservative and synchronous (sqlite3).
# You can adapt them to aiosqlite if the project uses async DB calls.

def get_connection(db_path: str, timeout: float = 5.0) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=timeout, isolation_level=None, check_same_thread=False)
    # Improve concurrency characteristics
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA foreign_keys=ON;')
        conn.execute('PRAGMA busy_timeout=5000;')
    except Exception:
        # Some sqlite builds may not allow PRAGMA changes; ignore if they fail.
        pass
    return conn

class DatabaseLockedError(RuntimeError):
    pass

def with_retry(fn, max_attempts: int = 3, backoff: float = 0.12):
    """Decorator-like helper to retry DB operations on sqlite 'database is locked'."""
    def wrapper(*args, **kwargs):
        attempt = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except sqlite3.OperationalError as e:
                msg = str(e).lower()
                if 'database is locked' in msg or 'database is busy' in msg:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise DatabaseLockedError('DB locked after %d attempts' % attempt) from e
                    time.sleep(backoff * attempt)
                    continue
                raise
    return wrapper

@with_retry
def run_atomic(db_path: str, callback) -> typing.Any:
    """Open connection, begin immediate transaction, call callback(cursor) and commit/rollback.
    callback must perform all necessary checks and mutations using provided cursor.
    Returns value returned by callback.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    try:
        cur.execute('BEGIN IMMEDIATE;')
        result = callback(cur)
        conn.commit()
        return result
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        cur.close()
        conn.close()

# Example template for an atomic buy operation.
# You can copy/adapt this into your models.py as buy_item_atomic.
def example_buy_item_atomic(db_path: str, player_id: int, item_name: str) -> bool:
    """Example logic (not tied to schemas) showing pattern:
    - SELECT balance
    - SELECT item price and availability
    - Check duplicates
    - UPDATE balance
    - INSERT into inventory
    All inside one transaction.
    """
    def _tx(cur):
        cur.execute('SELECT coins FROM players WHERE id=?;', (player_id,))
        row = cur.fetchone()
        if not row:
            return False
        balance = row[0]
        cur.execute('SELECT price, category, available_in_tutorial FROM shop_items WHERE name=?;', (item_name,))
        shop = cur.fetchone()
        if not shop:
            return False
        price = shop[0]
        # check duplicate
        cur.execute('SELECT 1 FROM tutorial_inventory WHERE player_id=? AND item_name=?;', (player_id, item_name))
        if cur.fetchone():
            return False
        if balance < price:
            return False
        cur.execute('UPDATE players SET coins = coins - ? WHERE id=?;', (price, player_id))
        cur.execute('INSERT INTO tutorial_inventory (player_id, item_name, item_type, quantity) VALUES (?,?,?,1);',
                    (player_id, item_name, shop[1]))
        return True

    return run_atomic(db_path, _tx)
