"""
Shared helper for lightweight managers that reuse the app's single
DatabaseManager connection but write their own raw SQL.

Why this exists
----------------
Three managers were found, independently, to hardcode a SQL placeholder
style for one backend only instead of adapting to whichever one is
actually configured via DATABASE_TYPE:

- src/auth/security_manager.py      -> hardcoded '%s' (breaks on SQLite)
- src/auth/api_key_manager.py       -> hardcoded '?'  (breaks on Postgres)
- src/payments/subscription_manager.py -> hardcoded '?'  (breaks on Postgres)

This is the same class of bug already fixed twice this month in
CredentialsManager and ManualPaymentManager (each got its own copy of a
_get_connection()/_q() pair). Rather than patch a fourth (and future
fifth, sixth...) file with another copy-pasted fix, BaseManager centralizes
the one piece of logic that actually needs to be correct: turning a query
written with '?' placeholders into whatever the active backend expects.

Usage
-----
    from src.database.base_manager import BaseManager

    class SomeManager(BaseManager):
        def do_thing(self, x):
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute(self._q("SELECT * FROM t WHERE id = ?"), (x,))
            ...

BaseManager does not open its own connections — it reuses
self.db (a DatabaseManager instance, shared or injected), which already
knows how to connect to SQLite or Postgres correctly. It only adapts the
placeholder style, using DatabaseManager's own `placeholder` attribute as
the single source of truth for which backend is active.
"""


class BaseManager:
    """Mixin providing a shared DatabaseManager connection + placeholder adapter."""

    def __init__(self, db_manager=None):
        if db_manager is not None:
            self.db = db_manager
        else:
            from src.database.database_manager import get_db_manager
            self.db = get_db_manager()

    def _q(self, query: str) -> str:
        """Adapt a query written with '?' placeholders to the active backend."""
        placeholder = getattr(self.db, 'placeholder', '?')
        if placeholder == '?':
            return query
        return query.replace('?', placeholder)

    def get_connection(self):
        """Shorthand for self.db.get_connection()."""
        return self.db.get_connection()
