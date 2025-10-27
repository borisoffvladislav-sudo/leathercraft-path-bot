import asyncio
from collections import defaultdict

"""Per-player asyncio Locks.

Usage:
    from utils.locks import get_player_lock
    lock = get_player_lock(player_id)
    async with lock:
        # critical section for this player
"""

_player_locks: dict[int, asyncio.Lock] = defaultdict(lambda: asyncio.Lock())

def get_player_lock(player_id: int) -> asyncio.Lock:
    return _player_locks[player_id]
