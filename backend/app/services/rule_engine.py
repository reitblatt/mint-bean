"""Rule engine for transaction categorization."""

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
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

    def apply_rules(self, transaction: Transaction) -> Optional[dict[str, Any]]:
        """
        Apply rules to a transaction.

        Args:
            transaction: Transaction to categorize

        Returns:
            Dictionary of changes to apply, or None if no rules matched

        TODO: Implement rule application logic
        - Query active rules ordered by priority
        - For each rule, check if conditions match
        - If match, apply actions and return changes
        - Track rule match statistics
        """
        logger.info(f"Applying rules to transaction: {transaction.transaction_id}")

        rules = self.db.query(Rule).filter(Rule.active == True).order_by(Rule.priority.desc()).all()

        for rule in rules:
            if self._matches_conditions(transaction, rule):
                logger.info(f"Rule matched: {rule.name}")
                actions = self._parse_actions(rule.actions)

                # Update rule statistics
                rule.match_count += 1
                from datetime import datetime
                rule.last_matched_at = datetime.utcnow()
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

        TODO: Implement condition matching
        - Parse rule.conditions JSON
        - Support operators: equals, contains, regex, greater_than, less_than
        - Support fields: description, payee, amount, account
        - Support AND/OR logic for multiple conditions
        """
        import json
        conditions = json.loads(rule.conditions)

        # Simple example implementation
        if conditions.get("field") == "description":
            operator = conditions.get("operator")
            value = conditions.get("value", "").lower()
            desc = transaction.description.lower()

            if operator == "contains":
                return value in desc
            elif operator == "equals":
                return value == desc
            elif operator == "regex":
                import re
                return bool(re.search(value, desc))

        return False

    def _parse_actions(self, actions_json: str) -> dict[str, Any]:
        """
        Parse rule actions from JSON.

        Args:
            actions_json: JSON string of actions

        Returns:
            Dictionary of actions to apply

        TODO: Expand action support
        - Support set_category, set_payee, set_tags, set_account
        - Validate actions before returning
        """
        import json
        return json.loads(actions_json)

    def apply_rules_bulk(self, transactions: list[Transaction]) -> dict[str, int]:
        """
        Apply rules to multiple transactions.

        Args:
            transactions: List of transactions

        Returns:
            Statistics on rules applied

        TODO: Implement bulk rule application
        - Iterate through transactions
        - Apply rules to each
        - Track how many were categorized
        - Return statistics
        """
        logger.info(f"Applying rules to {len(transactions)} transactions")

        categorized = 0
        for transaction in transactions:
            actions = self.apply_rules(transaction)
            if actions:
                # Apply the actions
                if "set_category" in actions:
                    # TODO: Look up category and set category_id
                    pass
                if "set_payee" in actions:
                    transaction.payee = actions["set_payee"]

                categorized += 1

        self.db.commit()

        return {
            "total": len(transactions),
            "categorized": categorized,
            "uncategorized": len(transactions) - categorized,
        }

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
