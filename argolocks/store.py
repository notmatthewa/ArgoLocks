from argolocks.models import Lock

_locks: dict[str, Lock] = {}


def create_lock(lock: Lock) -> None:
    _locks[lock.lock_id] = lock


def get_lock(lock_id: str) -> Lock | None:
    return _locks.get(lock_id)
