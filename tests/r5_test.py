import pytest
from datetime import datetime, timedelta
from services.library_service import calculate_late_fee_for_book
from database import insert_borrow_record, update_book_availability

# helper function to borrow a book for a patron for testing
def borrow_book_for_test(patron_id, book_id, days_ago_borrowed=0):
    borrow_date = datetime.now() - timedelta(days=days_ago_borrowed)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    update_book_availability(book_id, -1)
    return borrow_date, due_date

def test_no_late_fee():
    # should return no late fee as returned on time
    patron_id = "123456"
    book_id = 1

    # assuming late fee service will get borrow and due date directly from db when implemented
    borrow_book_for_test(patron_id, book_id, days_ago_borrowed=5) 

    result = calculate_late_fee_for_book(patron_id, book_id)
    assert result['fee_amount'] == 0.00
    assert result['days_overdue'] == 0
    assert 'status' not in result or 'not implemented' not in result['status']

def test_late_fee_under_7_days():
    # 5 days overdue, therefore should be $2.50 (5 * $0.50)
    patron_id = "123456"
    book_id = 2

    borrow_book_for_test(patron_id, book_id, days_ago_borrowed=19)

    result = calculate_late_fee_for_book(patron_id, book_id)
    assert result['days_overdue'] == 5
    assert result['fee_amount'] == 5 * 0.50  # $0.50 per day for first 7 days

def test_late_fee_over_7_days():
    # 10 days overdue, therefore should be $6.50 ((7 * $0.50) + (3 * $1.00))
    patron_id = "123321"
    book_id = 1

    borrow_book_for_test(patron_id, book_id, days_ago_borrowed=24)

    result = calculate_late_fee_for_book(patron_id, book_id)
    
    expected_fee = 3.5 + 3
    assert result['days_overdue'] == 10
    assert result['fee_amount'] == expected_fee

def test_late_fee_max_fee():
    # book extremely overdue, but should cap at $15
    patron_id = "123123"
    book_id = 2

    borrow_book_for_test(patron_id, book_id, days_ago_borrowed=55)

    result = calculate_late_fee_for_book(patron_id, book_id)
    assert result['fee_amount'] <= 15.0

def test_late_fee_not_borrowed():
    # book not borrowed, should fail
    patron_id = "000000"
    book_id = 6789

    result = calculate_late_fee_for_book(patron_id, book_id)
    assert 'fee_amount' in result
    assert result['fee_amount'] == 0.0  # no fee
    assert 'status' in result or 'not borrowed' in result.get('status', '').lower()