"""Rule API endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.rule import Rule
from app.models.user import User
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()


@router.get("", response_model=list[RuleResponse])
def list_rules(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Rule]:
    """
    List all rules.

    Args:
        active_only: Only return active rules
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of rules ordered by priority
    """
    query = db.query(Rule).filter(Rule.user_id == current_user.id)
    if active_only:
        query = query.filter(Rule.active)
    return query.order_by(Rule.priority.desc()).all()


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rule:
    """
    Get a specific rule by ID.

    Args:
        rule_id: Rule ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Rule details
    """
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


.post("", response_model=RuleResponse, status_code=201)
def create_rule(
    rule: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rule:
    """
    Create a new rule.

    Args:
        rule: Rule data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created rule
    """
    import json

    rule_data = rule.model_dump()
    # Convert dicts to JSON strings
    rule_data["conditions"] = json.dumps(rule_data["conditions"])
    rule_data["actions"] = json.dumps(rule_data["actions"])

    db_rule = Rule(
        user_id=current_user.id,
        **rule_data,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule: RuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rule:
    """
    Update a rule.

    Args:
        rule_id: Rule ID
        rule: Updated rule data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated rule
    """
    import json

    db_rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == current_user.id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = rule.model_dump(exclude_unset=True)
    # Convert dicts to JSON strings
    if "conditions" in update_data:
        update_data["conditions"] = json.dumps(update_data["conditions"])
    if "actions" in update_data:
        update_data["actions"] = json.dumps(update_data["actions"])

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a rule.

    Args:
        rule_id: Rule ID
        current_user: Current authenticated user
        db: Database session
    """
    db_rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == current_user.id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(db_rule)
    db.commit()
