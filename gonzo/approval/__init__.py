"""Approval service: opens an approval session, never grants one (D-14).

Agents may ask this service to render an "Adopt as doctrine" card. They never hold
the token, never set an adopted flag, and never call promote — they cannot forge
what they do not hold.
"""
