
from decimal import Decimal

import pytest

from app.services.financial_calculator import (
    to_decimal,
    calculate_net_cash_flow,
    calculate_withdrawal_percentage,
    calculate_balance_change,
    calculate_financial_summary,
)


def test_net_cash_flow():
    result = calculate_net_cash_flow("1876.02", "1320.02")
    assert result == Decimal("556.00")


def test_withdrawal_percentage():
    result = calculate_withdrawal_percentage(
        "1876.02", "1320.02"
    )
    assert result == Decimal("70.36")


def test_balance_change():
    result = calculate_balance_change("69.96", "586.71")

    assert result["change"] == Decimal("516.75")
    assert result["percentage_change"] == Decimal("738.64")


def test_zero_deposits():
    result = calculate_withdrawal_percentage("0", "100")
    assert result is None


def test_negative_balance_change():
    result = calculate_balance_change("500", "400")

    assert result["change"] == Decimal("-100.00")
    assert result["percentage_change"] == Decimal("-20.00")


def test_currency_formatting():
    assert to_decimal("$1,876.02") == Decimal("1876.02")
    assert to_decimal("(250.00)") == Decimal("-250.00")


def test_financial_summary():
    result = calculate_financial_summary("1876.02", "1320.02")

    assert result["net_cash_flow"] == Decimal("556.00")
    assert result["withdrawal_percentage"] == Decimal("70.36")
