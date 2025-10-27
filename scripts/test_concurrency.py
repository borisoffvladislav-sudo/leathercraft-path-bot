# Simple concurrency test script.
# It simulates many concurrent 'players' performing atomic buys using db_utils.example_buy_item_atomic.
# Usage: python3 test_concurrency.py /path/to/game.db
import asyncio
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.db_utils import example_buy_item_atomic

async def worker(db_path, player_id, item_name, loop):
    # run blocking example_buy_item_atomic in threadpool
    return await loop.run_in_executor(None, example_buy_item_atomic, db_path, player_id, item_name)

async def main(db_path):
    loop = asyncio.get_running_loop()
    tasks = []
    # simulate 100 concurrent players (or fewer if DB is small)
    for i in range(1, 101):
        # choose a random item_name; replace with real names from your shop_items
        item = random.choice(['Канцелярский нож', 'Высечные пробойники', 'Мультитул 3 в 1'])
        tasks.append(worker(db_path, i, item, loop))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = sum(1 for r in results if r is True)
    print(f"Success purchases: {success} / {len(results)}")
    for idx, r in enumerate(results, start=1):
        if isinstance(r, Exception):
            print(idx, 'ERROR', type(r), r)
        else:
            print(idx, 'OK' if r else 'FAIL')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python test_concurrency.py /path/to/game.db')
        sys.exit(1)
    db = sys.argv[1]
    asyncio.run(main(db))
