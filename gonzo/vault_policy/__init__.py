"""Vault seam: retrieval, read contract, and draft-write policy (D-04, D-04a, D-04b).

The only path agents have into gonzo-vault. Reads return a use_class, never a raw
authority number; writes may only create or touch files whose status is `draft`.
"""
