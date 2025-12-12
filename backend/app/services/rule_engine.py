"""Rule engine for transaction categorization."""

import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.category import Category
from app.models.rule import Rule
from app.models.transaction import Transaction

logger = get_logger(__name__)


class RuleEngine:
    """Engine for applying categorization rules to transactions."""

    def __init__(self, db: Session):
        """
        Initialize rule engine.

        Args:
            db: Database session
        """
        self.db = db

    def apply_rules(
        self, transaction: Transaction, apply_changes: bool = True
    ) -> dict[str, Any] | None:
        """
        Apply rules to a transaction.

        Args:
            transaction: Transaction to categorize
            apply_changes: If True, apply actions to transaction. If False, just return actions.

        Returns:
            Dictionary of changes to apply, or None if no rules matched
        """
        logger.info(f"Applying rules to transaction: {transaction.transaction_id}")

        rules = self.db.query(Rule).filter(Rule.active).order_by(Rule.priority.desc()).all()

        for rule in rules:
            if self._matches_conditions(transaction, rule):
                logger.info(f"Rule matched: {rule.name}")
                actions = self._parse_actions(rule.actions)

                # Update rule statistics
                rule.match_count += 1
                rule.last_matched_at = datetime.now(UTC)

                if apply_changes:
                    self._apply_actions(transaction, actions)

                self.db.commit()

                return actions

        return None

    def _matches_conditions(self, transaction: Transaction, rule: Rule) -> bool:
        """
        Check if transaction matches rule conditions.

        Args:
            transaction: Transaction to check
            rule: Rule with conditions

        Returns:
            True if all conditions match

        Supports:
        - Simple condition: {"field": "description", "operator": "contains", "value": "amazon"}
        - AND logic: {"all": [condition1, condition2, ...]}
        - OR logic: {"any": [condition1, condition2, ...]}
        - Operators: equals, not_equals, contains, not_contains, regex, starts_with, ends_with,
                     greater_than, less_than, greater_than_or_equal, less_than_or_equal
        - Fields: description, payee, merchant_name, amount, pending, plaid_primary_category,
                  plaid_detailed_category, plaid_confidence_level, account.name
        """
        conditions = json.loads(rule.conditions)
        return self._evaluate_condition(transaction, conditions)

    def _evaluate_condition(self, transaction: Transaction, condition: dict) -> bool:
        """
        Recursively evaluate a condition.

        Args:
            transaction: Transaction to check
            condition: Condition dictionary

        Returns:
            True if condition matches
        """
        # Handle AND logic
        if "all" in condition:
            return all(self._evaluate_condition(transaction, c) for c in condition["all"])

        # Handle OR logic
        if "any" in condition:
            return any(self._evaluate_condition(transaction, c) for c in condition["any"])

        # Handle simple condition
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not field or not operator:
            return False

        # Get field value from transaction
        field_value = self._get_field_value(transaction, field)
        if field_value is None and operator not in ["equals", "not_equals"]:
            return False

        # Apply operator
        return self._apply_operator(field_value, operator, value)

    def _get_field_value(self, transaction: Transaction, field: str) -> Any:
        """
        Get field value from transaction.

        Args:
            transaction: Transaction object
            field: Field name (supports dot notation like "account.name")

        Returns:
            Field value or None
        """
        # Handle nested fields (e.g., "account.name")
        if "." in field:
            parts = field.split(".", 1)
            obj = getattr(transaction, parts[0], None)
            if obj is None:
                return None
            return getattr(obj, parts[1], None)

        # Direct field access
        return getattr(transaction, field, None)

    def _apply_operator(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """
        Apply comparison operator.

        Args:
            field_value: Actual value from transaction
            operator: Comparison operator
            expected_value: Expected value to compare against

        Returns:
            True if comparison passes
        """
        # Handle None values
        if field_value is None:
            return operator == "equals" and expected_value is None

        # String operators (case-insensitive)
        if operator in [
            "equals",
            "not_equals",
            "contains",
            "not_contains",
            "starts_with",
            "ends_with",
            "regex",
        ]:
            field_str = str(field_value).lower()
            expected_str = str(expected_value).lower() if expected_value is not None else ""

            if operator == "equals":
                return field_str == expected_str
            elif operator == "not_equals":
                return field_str != expected_str
            elif operator == "contains":
                return expected_str in field_str
            elif operator == "not_contains":
                return expected_str not in field_str
            elif operator == "starts_with":
                return field_str.startswith(expected_str)
            elif operator == "ends_with":
                return field_str.endswith(expected_str)
            elif operator == "regex":
                try:
                    return bool(re.search(expected_str, field_str, re.IGNORECASE))
                except re.error:
                    logger.warning(f"Invalid regex pattern: {expected_str}")
                    return False

        # Numeric operators
        elif operator in [
            "greater_than",
            "less_than",
            "greater_than_or_equal",
            "less_than_or_equal",
        ]:
            try:
                field_num = float(field_value)
                expected_num = float(expected_value)

                if operator == "greater_than":
                    return field_num > expected_num
                elif operator == "less_than":
                    return field_num < expected_num
                elif operator == "greater_than_or_equal":
                    return field_num >= expected_num
                elif operator == "less_than_or_equal":
                    return field_num <= expected_num
            except (ValueError, TypeError):
                return False

        return False

    def _parse_actions(self, actions_json: str) -> dict[str, Any]:
        """
        Parse rule actions from JSON.

        Args:
            actions_json: JSON string of actions

        Returns:
            Dictionary of actions to apply

        Supported actions:
        - set_category: Category ID or category name
        - set_payee: Set payee value
        - add_tags: Add tags (JSON array)
        - set_reviewed: Mark as reviewed (boolean)
        """
        return json.loads(actions_json)

    def apply_rules_bulk(self, transactions: list[Transaction]) -> dict[str, int]:
        """
        Apply rules to multiple transactions.

        Args:
            transactions: List of transactions

        Returns:
            Statistics on rules applied
        """
        logger.info(f"Applying rules to {len(transactions)} transactions")

        categorized = 0
        for transaction in transactions:
            actions = self.apply_rules(transaction)
            if actions:
                self._apply_actions(transaction, actions)
                categorized += 1

        self.db.commit()

        return {
            "total": len(transactions),
            "categorized": categorized,
            "uncategorized": len(transactions) - categorized,
        }

    def _apply_actions(self, transaction: Transaction, actions: dict[str, Any]) -> None:
        """
        Apply actions to a transaction.

        Args:
            transaction: Transaction to modify
            actions: Dictionary of actions to apply
        """
        # Set category
        if "set_category" in actions:
            category_value = actions["set_category"]
            if isinstance(category_value, int):
                # Category ID provided
                transaction.category_id = category_value
            elif isinstance(category_value, str):
                # Category name provided - look it up
                category = self.db.query(Category).filter(Category.name == category_value).first()
                if category:
                    transaction.category_id = category.id
                else:
                    logger.warning(f"Category not found: {category_value}")

            # Mark as auto-categorized
            transaction.auto_categorized = True
            transaction.categorization_method = "rule"

        # Set payee
        if "set_payee" in actions:
            transaction.payee = actions["set_payee"]

        # Add tags
        if "add_tags" in actions:
            tags = actions["add_tags"]
            if isinstance(tags, list):
                # Merge with existing tags
                existing_tags = json.loads(transaction.tags) if transaction.tags else []
                merged_tags = list(set(existing_tags + tags))
                transaction.tags = json.dumps(merged_tags)
            else:
                logger.warning(f"Invalid tags format: {tags}")

        # Set reviewed
        if "set_reviewed" in actions:
            transaction.reviewed = bool(actions["set_reviewed"])

    def test_rule(self, rule: Rule, transaction: Transaction) -> bool:
        """
        Test if a rule would match a transaction without applying it.

        Args:
            rule: Rule to test
            transaction: Transaction to test against

        Returns:
            True if rule matches
        """
        return self._matches_conditions(transaction, rule)
