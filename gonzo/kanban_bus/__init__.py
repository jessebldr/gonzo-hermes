"""Kanban as the coordination bus between profile processes (D-02, D-03).

team_ask, the worker inbox, and the dispatcher that wakes the owning process. The
four profiles share this bus and nothing else — no shared context, no shared memory.
"""
