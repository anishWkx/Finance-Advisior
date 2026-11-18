
import re
from decimal import Decimal
from uuid import uuid4


MONEY_PATTERN = re.compile(r"\$?\d[\d,]*\.\d{2}")


def parse_amount(value):
    cleaned = value.replace("$", "").replace(",", "").strip()
    return Decimal(cleaned).quantize(Decimal("0.01"))


def extract_opening_balance(sections):
    for section in sections:
        text = section.get("content", "")

        match = re.search(
            r"Beginning balance.*?\$([\d,]+\.\d{2})",
            text,
            re.IGNORECASE
        )

        if match:
            return parse_amount(match.group(1))

    raise ValueError("Could not identify the statement opening balance")


def extract_us_statement_transactions(sections):
    """
    Extract transactions from a US bank statement's daily
    running-balance table.

    Transaction amounts are verified using consecutive balances.
    """
    transactions = []
    previous_balance = extract_opening_balance(sections)

    in_transaction_table = False

    for section in sections:
        text = section.get("content", "")
        page = section.get("page")

        for line in text.splitlines():
            line = line.strip()

            if "Account Transactions by date" in line:
                in_transaction_table = True
                continue

            if "Account Transactions by type" in line:
                in_transaction_table = False
                continue

            if not in_transaction_table:
                continue

            date_match = re.match(
                r"^(\d{2}/\d{2})[.]?\s+(.+)$",
                line
            )

            if not date_match:
                continue

            transaction_date, remaining = date_match.groups()

            amounts = MONEY_PATTERN.findall(remaining)

            if not amounts:
                continue

            # The final amount is the resulting running balance.
            current_balance = parse_amount(amounts[-1])

            # When two amounts exist, the second-last is the
            # transaction amount. Otherwise, infer it from balances.
            balance_change = current_balance - previous_balance

            if len(amounts) >= 2:
                reported_amount = parse_amount(amounts[-2])

                if abs(abs(balance_change) - reported_amount) > Decimal("0.01"):
                    raise ValueError(
                        f"Transaction amount does not reconcile: {line}"
                    )

            transaction_amount = abs(balance_change)

            if transaction_amount == Decimal("0.00"):
                continue

            is_credit = balance_change > 0

            description = re.sub(
                MONEY_PATTERN,
                "",
                remaining
            ).strip()

            transactions.append({
                "id": uuid4().hex,
                "transaction_date": transaction_date,
                "description": description,
                "debit": None if is_credit else str(transaction_amount),
                "credit": str(transaction_amount) if is_credit else None,
                "balance": str(current_balance),
                "source_page": page,
                "source_sheet": None,
                "raw_text": line,
            })

            previous_balance = current_balance

    return transactions
