
from fastapi import APIRouter, Depends, HTTPException

from app.auth.security import get_current_user
from app.auth.database import get_user_transactions
from app.services.transaction_service import get_transaction_summary
from app.services.categorization_service import categorize_transactions


router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
)


@router.get("/summary")
def transaction_summary(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    transactions = get_user_transactions(
        current_user["id"],
        document_id,
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="No transactions found for this document",
        )

    summary = get_transaction_summary(
        current_user["id"],
        document_id,
    )

    categorized = categorize_transactions(transactions)

    return {
        "summary": summary,
        "spending_by_category": categorized["spending_by_category"],
        "total_expenses": categorized["total_expenses"],
    }


@router.get("/")
def list_transactions(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    transactions = get_user_transactions(
        current_user["id"],
        document_id,
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="No transactions found for this document",
        )

    categorized = categorize_transactions(transactions)

    return {
        "transactions": categorized["transactions"],
        "count": len(categorized["transactions"]),
    }
