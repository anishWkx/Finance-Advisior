
import re
from decimal import Decimal
from uuid import uuid4


MONEY_PATTERN = re.compile(r"[₹$]?\s*\d[\d,]*\.\d{2}")

DATE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{2,4})$"
)


def parse_amount(value):
    cleaned = str(value)
    cleaned = cleaned.replace("$", "").replace("₹", "")
    cleaned = cleaned.replace("I", "")
    cleaned = cleaned.replace(",", "").strip()
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

            current_balance = parse_amount(amounts[-1])
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
            description = MONEY_PATTERN.sub("", remaining).strip()

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


def extract_generic_statement_transactions(sections):
    # 1. Find the opening balance.
    opening_balance = None

    for section in sections:
        text = section.get("content", "")

        if "Account summary" in text:
            summary = text.split("Account summary", 1)[1]
            amounts = MONEY_PATTERN.findall(summary)

            if amounts:
                opening_balance = parse_amount(amounts[0])
                break

    # Fallback for other statement formats.
    if opening_balance is None:
        for section in sections:
            text = section.get("content", "")

            match = re.search(
                r"(?:Opening|Beginning)\s+balance"
                r".{0,150}?([\d,]+\.\d{2})",
                text,
                re.IGNORECASE | re.DOTALL
            )

            if match:
                opening_balance = parse_amount(match.group(1))
                break

    if opening_balance is None:
        print("Could not identify opening balance")
        return []

    print("Opening balance detected:", opening_balance)

    previous_balance = opening_balance
    transactions = []

    # 2. Read transactions from each page.
    for section in sections:
        lines = [
            line.strip()
            for line in section.get("content", "").splitlines()
            if line.strip()
        ]

        page = section.get("page")
        index = 0

        while index < len(lines):
            if not DATE_PATTERN.fullmatch(lines[index]):
                index += 1
                continue

            # Expected vertical layout:
            # Date
            # Mode
            # Description
            # Credit
            # Debit
            # Balance

            if index + 5 >= len(lines):
                index += 1
                continue

            transaction_date = lines[index]
            description = lines[index + 2]
            credit_line = lines[index + 3]
            debit_line = lines[index + 4]
            balance_line = lines[index + 5]

            def read_amount(value):
                value = value.strip()

                if value in ("—", "–", "-", ""):
                    return Decimal("0.00")

                amounts = MONEY_PATTERN.findall(value)

                if amounts:
                    return parse_amount(amounts[0])

                return None

            credit = read_amount(credit_line)
            debit = read_amount(debit_line)
            current_balance = read_amount(balance_line)

            if credit is None or debit is None or current_balance is None:
                index += 1
                continue

            if credit == Decimal("0.00") and debit == Decimal("0.00"):
                index += 1
                continue

            # Reconcile transaction with running balance.
            expected_balance = previous_balance + credit - debit

            if abs(expected_balance - current_balance) > Decimal("0.01"):
                print(
                    "Balance mismatch:",
                    transaction_date,
                    description
                )
                index += 6
                continue

            transactions.append({
                "id": uuid4().hex,
                "transaction_date": transaction_date,
                "description": description,
                "debit": str(debit) if debit > 0 else None,
                "credit": str(credit) if credit > 0 else None,
                "balance": str(current_balance),
                "source_page": page,
                "source_sheet": None,
                "raw_text": " | ".join(lines[index:index + 6]),
            })

            previous_balance = current_balance
            index += 6

    return transactions
