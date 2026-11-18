
from decimal import Decimal


CATEGORY_RULES = {
    "Food & Dining": [
        "RESTAURANT", "CAFE", "FOOD", "GRILL", "BAR",
    ],
    "Shopping": [
        "WAL-MART", "WALMART", "DILLONS", "HOME DEPOT",
        "PURCHASE", "STORE",
    ],
    "ATM & Cash": [
        "ATM", "CASH WITHDRAWAL",
    ],
    "Bills & Utilities": [
        "UTILITY", "ELECTRIC", "WATER BILL", "INTERNET",
        "PHONE BILL",
    ],
    "Bank Fees": [
        "SERVICE CHARGE", "BANK FEE", "MAINTENANCE FEE",
    ],
    "Checks": [
        "CHECK",
    ],
}


def categorize_transaction(description):
    normalized = (description or "").upper()

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return category

    return "Other"


def categorize_transactions(transactions):
    categorized = []
    spending_by_category = {}
    total_expenses = Decimal("0.00")

    for transaction in transactions:
        debit = Decimal(str(transaction["debit"] or "0.00"))

        category = categorize_transaction(
            transaction["description"]
        )

        categorized.append({
            **dict(transaction),
            "category": category,
        })

        if debit > 0:
            total_expenses += debit
            spending_by_category[category] = (
                spending_by_category.get(category, Decimal("0.00"))
                + debit
            )

    return {
        "transactions": categorized,
        "spending_by_category": {
            category: f"{amount:.2f}"
            for category, amount in spending_by_category.items()
        },
        "total_expenses": f"{total_expenses:.2f}",
    }
