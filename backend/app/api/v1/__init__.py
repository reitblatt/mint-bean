"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    accounts,
    admin,
    analytics,
    auth,
    beancount,
    categories,
    dashboards,
    deletion,
    onboarding,
    plaid,
    plaid_category_mappings,
    rules,
    settings,
    setup,
    transactions,
)

api_router = APIRouter()

api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])

api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])

api_router.include_router(categories.router, prefix="/categories", tags=["categories"])

api_router.include_router(rules.router, prefix="/rules", tags=["rules"])

api_router.include_router(plaid.router, prefix="/plaid", tags=["plaid"])

api_router.include_router(
    plaid_category_mappings.router,
    prefix="/plaid-category-mappings",
    tags=["plaid-category-mappings"],
)

api_router.include_router(beancount.router, prefix="/beancount", tags=["beancount"])

api_router.include_router(deletion.router, prefix="/deletion", tags=["deletion"])

api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
