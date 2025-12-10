"""Rule API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse

router = APIRouter()


@router.get("/", response_model=List[RuleResponse])
def list_rules(
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[Rule]:
    """
    List all rules.

    Args:
        active_only: Only return active rules
        db: Database session

    Returns:
        List of rules ordered by priority
    """
    query = db.query(Rule)
    if active_only:
        query = query.filter(Rule.active == True)
    return query.order_by(Rule.priority.desc()).all()


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
) -> Rule:
    """
    Get a specific rule by ID.

    Args:
        rule_id: Rule ID
        db: Database session

    Returns:
        Rule details
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/", response_model=RuleResponse, status_code=201)
def create_rule(
    rule: RuleCreate,
    db: Session = Depends(get_db),
) -> Rule:
    """
    Create a new rule.

    Args:
        rule: Rule data
        db: Database session

    Returns:
        Created rule
    """
    import json

    rule_data = rule.model_dump()
    # Convert dicts to JSON strings
    rule_data["conditions"] = json.dumps(rule_data["conditions"])
    rule_data["actions"] = json.dumps(rule_data["actions"])

    db_rule = Rule(**rule_data)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule: RuleUpdate,
    db: Session = Depends(get_db),
) -> Rule:
    """
    Update a rule.

    Args:
        rule_id: Rule ID
        rule: Updated rule data
        db: Database session

    Returns:
        Updated rule
    """
    import json

    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
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
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a rule.

    Args:
        rule_id: Rule ID
        db: Database session
    """
    db_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(db_rule)
    db.commit()
