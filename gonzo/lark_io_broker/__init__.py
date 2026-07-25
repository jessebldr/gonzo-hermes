"""Outbound capability broker for Lark (D-20).

Workers hold no Lark app secret. They call a narrow API — post_message, post_card,
patch_card, write_base_row — with a signed capability bound to a task_id, and the
payload reaches Lark without passing through the orchestrator's model context.
"""
