"""Deletion policy definitions for data lifecycle management."""

from enum import Enum


class DeletionPolicy(str, Enum):
    """
    Defines how an entity should be deleted.

    MANUAL: Only deleted manually by user action (e.g., via UI)
    CASCADE: Deleted automatically when parent/referenced object is deleted
    TTL: Deleted after a time-to-live period expires
    """

    MANUAL = "manual"
    CASCADE = "cascade"
    TTL = "ttl"


class DeletionMetadata:
    """
    Metadata about deletion behavior for each model.

    Attributes:
        policy: The deletion policy for this entity type
        cascade_from: List of parent models that trigger cascade deletion
        cascade_to: List of child models that will be cascade deleted
        ttl_days: Number of days before TTL deletion (if policy is TTL)
    """

    def __init__(
        self,
        policy: DeletionPolicy,
        cascade_from: list[str] | None = None,
        cascade_to: list[str] | None = None,
        ttl_days: int | None = None,
    ):
        self.policy = policy
        self.cascade_from = cascade_from or []
        self.cascade_to = cascade_to or []
        self.ttl_days = ttl_days


# Deletion metadata registry for each model
DELETION_REGISTRY = {
    "User": DeletionMetadata(
        policy=DeletionPolicy.MANUAL,
        cascade_to=[
            "PlaidItem",
            "Account",
            "Transaction",
            "Category",
            "Rule",
            "PlaidCategoryMapping",
        ],
    ),
    "PlaidItem": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=[],  # PlaidItems don't directly cascade to accounts (accounts cascade from user)
    ),
    "Account": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=["Transaction"],
    ),
    "Transaction": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User", "Account"],
        cascade_to=[],
    ),
    "Category": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=[],  # Categories don't cascade delete transactions (transactions just lose their category)
    ),
    "Rule": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=[],
    ),
    "PlaidCategoryMapping": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=[],
    ),
}
