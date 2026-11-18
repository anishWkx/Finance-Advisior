
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENT = Decimal("0.01")
PERCENT_PRECISION = Decimal("0.01")


def to_decimal(value):
    """Safely convert a monetary value to Decimal."""
    if value is None or value == "":
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    cleaned = str(value).strip()
    cleaned = cleaned.replace("$", "").replace(",", "").replace("₹", "")

    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]

    try:
        return Decimal(cleaned)
    except InvalidOperation as error:
        raise ValueError(f"Invalid monetary value: {value}") from error


def money(value):
    """Round monetary values to two decimal places."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def percentage(numerator, denominator):
    """Calculate a percentage safely."""
    if denominator == 0:
        return None

    return (
        (numerator / denominator) * Decimal("100")
    ).quantize(PERCENT_PRECISION, rounding=ROUND_HALF_UP)


def calculate_net_cash_flow(deposits, withdrawals):
    deposits = to_decimal(deposits)
    withdrawals = to_decimal(withdrawals)

    return money(deposits - withdrawals)


def calculate_withdrawal_percentage(deposits, withdrawals):
    deposits = to_decimal(deposits)
    withdrawals = to_decimal(withdrawals)

    return percentage(withdrawals, deposits)


def calculate_balance_change(beginning_balance, ending_balance):
    beginning = to_decimal(beginning_balance)
    ending = to_decimal(ending_balance)

    change = money(ending - beginning)

    change_percentage = percentage(change, beginning)

    return {
        "beginning_balance": money(beginning),
        "ending_balance": money(ending),
        "change": change,
        "percentage_change": change_percentage,
    }


def calculate_financial_summary(deposits, withdrawals):
    deposits = to_decimal(deposits)
    withdrawals = to_decimal(withdrawals)

    return {
        "total_deposits": money(deposits),
        "total_withdrawals": money(withdrawals),
        "net_cash_flow": calculate_net_cash_flow(
            deposits, withdrawals
        ),
        "withdrawal_percentage": calculate_withdrawal_percentage(
            deposits, withdrawals
        ),
    }
