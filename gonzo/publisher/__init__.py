"""Publisher: the only service permitted to write a vault note's `status` field.

Triggered solely by a signed Lark callback carrying a valid adoption event (D-14).
Promotes in place — no move, no rename — then validates and commits (D-05).
"""
