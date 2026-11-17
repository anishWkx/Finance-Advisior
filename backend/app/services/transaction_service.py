
from decimal import Decimal

from app.auth.database import get_user_transactions


ZERO = Decimal("0.00")


def decimal_value(value):
    """Safely convert stored monetary values to Decimal."""
    if value is None or value == "":
        return ZERO

    return Decimal(str(value))


def get_transaction_summary(user_id, document_id=None):
    """
    Calculate financial totals using only transactions
    belonging to the authenticated user.

    When document_id is provided, also calculate the
    opening and closing balances for that document.
    """
    transactions = get_user_transactions(
        user_id=user_id,
        document_id=document_id,
    )

    if not transactions:
        return {
            "transaction_count": 0,
            "total_deposits": "0.00",
            "total_withdrawals": "0.00",
            "net_cash_flow": "0.00",
            "opening_balance": None,
            "closing_balance": None,
        }

    total_deposits = sum(
        (
            decimal_value(transaction["credit"])
            for transaction in transactions
        ),
        ZERO,
    )

    total_withdrawals = sum(
        (
            decimal_value(transaction["debit"])
            for transaction in transactions
        ),
        ZERO,
    )

    net_cash_flow = total_deposits - total_withdrawals

    opening_balance = None
    closing_balance = None

    if document_id:
        first_transaction = transactions[0]
        last_transaction = transactions[-1]

        first_balance = decimal_value(first_transaction["balance"])
        first_debit = decimal_value(first_transaction["debit"])
        first_credit = decimal_value(first_transaction["credit"])

        opening_balance = (
            first_balance + first_debit - first_credit
        )

        closing_balance = decimal_value(last_transaction["balance"])

    return {
        "transaction_count": len(transactions),
        "total_deposits": f"{total_deposits:.2f}",
        "total_withdrawals": f"{total_withdrawals:.2f}",
        "net_cash_flow": f"{net_cash_flow:.2f}",
        "opening_balance": (
            f"{opening_balance:.2f}"
            if opening_balance is not None else None
        ),
        "closing_balance": (
            f"{closing_balance:.2f}"
            if closing_balance is not None else None
        ),
    }
