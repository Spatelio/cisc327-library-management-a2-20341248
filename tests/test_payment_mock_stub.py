from unittest.mock import Mock, ANY
import pytest
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway

# helper functions for stubbing
def stub_late_fee(mocker, amount: float, days_overdue: int = 0):
    # stub calculate_late_fee_for_book to avoid touching the real DB
    return mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            "fee_amount": amount,
            "days_overdue": days_overdue,
            "status": "stubbed",
        },
    )


def stub_book_lookup(mocker, book_id: int = 1, title: str = "Stubbed Book"):
    # stub get_book_by_id so tests dont depend on real catalog contents
    return mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={
            "id": book_id,
            "title": title,
            "author": "Stubbed Author",
            "isbn": "1234567890123",
            "total_copies": 1,
            "available_copies": 0,
        },
    )


# tests for pay_late_fees
def test_pay_late_fees_successful_payment(mocker):
    """
    happy path:
    - patron has a positive late fee
    - book exists
    - payment gateway accepts the payment

    expecting:
    - function returns success=True
    - gateway.process_payment called once with patron_id and amount
    """
    patron_id = "123456"
    book_id = 1

    stub_late_fee(mocker, amount=5.00, days_overdue=3)
    stub_book_lookup(mocker, book_id, "The Stubbed Book")

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_123456_1", "Payment processed")

    success, message, txn_id = pay_late_fees(patron_id, book_id, gateway)

    assert success is True
    assert "payment" in message.lower() or "success" in message.lower()
    assert txn_id == "txn_123456_1"

    gateway.process_payment.assert_called_once_with(
        patron_id=patron_id,
        amount=5.00,
        description=ANY
    )


def test_pay_late_fees_zero_fee_does_not_call_gateway(mocker):
    """
    if stubbed late fee is 0, nothing to pay

    expecting:
    - function indicates no payment was made
    - payment gateway is never called
    """
    patron_id = "123456"
    book_id = 1

    stub_late_fee(mocker, amount=0.00, days_overdue=0)
    stub_book_lookup(mocker, book_id)

    gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees(patron_id, book_id, gateway)

    assert success is False  # no payment processed
    assert "no late fee" in message.lower() or "no late fees" in message.lower()
    assert txn_id is None

    gateway.process_payment.assert_not_called()


def test_pay_late_fees_invalid_patron_id_short_circuits(mocker):
    """
    invalid patron IDs should be rejected before any DB or payment work

    expecting:
    - failure result
    - calculate_late_fee_for_book and payment gateway NOT called
    """
    invalid_patron_id = "123"  # not 6 digits
    book_id = 1

    fee_stub = stub_late_fee(mocker, amount=10.0)
    gateway = Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees(invalid_patron_id, book_id, gateway)

    assert success is False
    assert "invalid patron" in message.lower()
    assert txn_id is None

    fee_stub.assert_not_called()
    gateway.process_payment.assert_not_called()


def test_pay_late_fees_payment_declined(mocker):
    """
    if the payment gateway declines transaction,
    the function should report failure but still call gateway once.
    """
    patron_id = "654321"
    book_id = 2

    stub_late_fee(mocker, amount=7.50, days_overdue=5)
    stub_book_lookup(mocker, book_id)

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (
        False,
        "",
        "declined by issuer",
    )  # simulate decline

    success, message, txn_id = pay_late_fees(patron_id, book_id, gateway)

    assert success is False
    assert "declined" in message.lower() or "failed" in message.lower()
    assert txn_id is None

    gateway.process_payment.assert_called_once_with(
        patron_id=patron_id,
        amount=7.50,
        description=ANY
    )


def test_pay_late_fees_gateway_raises_exception(mocker):
    """
    if the payment gateway raises an exception like network error,
    the function should handle it gracefully and return a faillure result
    """
    patron_id = "777777"
    book_id = 3

    stub_late_fee(mocker, amount=4.00, days_overdue=2)
    stub_book_lookup(mocker, book_id)

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.side_effect = Exception("Network error")

    success, message, txn_id = pay_late_fees(patron_id, book_id, gateway)

    assert success is False
    assert "error" in message.lower() or "network" in message.lower()
    assert txn_id is None

    gateway.process_payment.assert_called_once_with(
        patron_id=patron_id,
        amount=4.00,
        description=ANY
    )


# tests for refund_late_fee_payment
def test_refund_successful(mocker):
    """
    happy path:
    - valid transaction ID and amount
    - gateway confirms refund

    expecting:
    - success=True
    - refund_payment called once with transaction_id and amount
    """
    txn_id = "txn_9999"
    amount = 5.00

    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (
        True,
        "Refund of $5.00 processed successfully.",
    )

    success, message = refund_late_fee_payment(txn_id, amount, gateway)

    assert success is True
    assert "refund" in message.lower()
    gateway.refund_payment.assert_called_once_with(txn_id, amount)


@pytest.mark.parametrize("bad_amount", [0.0, -1.0, -10.5])
def test_refund_rejects_non_positive_amounts(bad_amount):
    """
    refund amounts must be positive

    for zero or negative amounts, gateway shouldnt be contacted
    """
    txn_id = "txn_0001"
    gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment(txn_id, bad_amount, gateway)

    assert success is False
    assert "amount" in message.lower() or "greater than 0" in message.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_rejects_missing_txn_id():
    """
    empty or whitespace transaction IDs should be rejected immediately
    """
    gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("   ", 5.00, gateway)

    assert success is False
    assert "transaction" in message.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_gateway_failure():
    """
    if gateway is called but returns false/none, refund should
    be reported as failed
    """
    txn_id = "txn_2222"
    amount = 3.50

    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (
        False,
        "declined by bank",
    )

    success, message = refund_late_fee_payment(txn_id, amount, gateway)

    assert success is False
    assert "failed" in message.lower() or "declined" in message.lower()
    gateway.refund_payment.assert_called_once_with(txn_id, amount)


# direct payment gateway tests
def test_process_payment_invalid_amount():
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123456", 0)
    assert not success
    assert "invalid" in msg.lower()

def test_process_payment_amount_too_large():
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123456", 2000)
    assert not success
    assert "exceeds limit" in msg.lower()

def test_process_payment_invalid_patron_format():
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123", 10.0)
    assert not success
    assert "invalid patron" in msg.lower()

def test_process_payment_successful_transaction():
    gateway = PaymentGateway()
    success, txn, msg = gateway.process_payment("123456", 10.0, "Late fee")
    assert success is True
    assert txn.startswith("txn_")
    assert "processed" in msg.lower()

def test_refund_payment_invalid_txn_and_amount():
    gateway = PaymentGateway()
    success, msg = gateway.refund_payment("bad_id", -5)
    assert not success
    assert "invalid" in msg.lower() or "refund" in msg.lower()

def test_refund_payment_success():
    gateway = PaymentGateway()
    success, msg = gateway.refund_payment("txn_123456_1111", 10.0)
    assert success is True
    assert "refund" in msg.lower()

def test_verify_payment_status_invalid_txn():
    gateway = PaymentGateway()
    result = gateway.verify_payment_status("bad_txn")
    assert result["status"] == "not_found"

def test_verify_payment_status_valid_txn():
    gateway = PaymentGateway()
    result = gateway.verify_payment_status("txn_123456_9999")
    assert result["status"] == "completed"
    assert "timestamp" in result