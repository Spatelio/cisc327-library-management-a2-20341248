
import pytest
from datetime import datetime, timedelta
from services.library_service import return_book_by_patron
from database import insert_borrow_record, update_book_availability, get_patron_borrowed_books

# helper function to borrow a book for a patron for testing
def borrow_book_for_test(patron_id, book_id, days_ago_borrowed=0):
    borrow_date = datetime.now() - timedelta(days=days_ago_borrowed)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    update_book_availability(book_id, -1)
    return borrow_date, due_date

def test_return_book_success():
    # should succeed
    patron_id = "987654"
    book_id = 1 # great gatsby

    borrow_book_for_test(patron_id, book_id)
    
    success, message = return_book_by_patron(patron_id, book_id)
    assert success is True
    assert "return processed" in message.lower()
    
    # check book is removed from patron's borrowed books, copies updated
    borrowed = get_patron_borrowed_books(patron_id)
    assert all(b['book_id'] != book_id for b in borrowed)

def test_return_book_invalid_patron():
    # should fail, as patron 000000 does not exist and/or did not borrow book 1
    success, message = return_book_by_patron("000000", 1)
    assert success is False
    assert "invalid" in message.lower() or "not borrowed" in message.lower()

def test_return_book_not_borrowed():
    # should fail, as patron did not borrow book 9999 as it does not exist
    success, message = return_book_by_patron("654987", 9999)
    assert success is False
    assert "not borrowed" in message.lower() or "not found" in message.lower()

def test_return_book_calculates_late_fee():
    # should succeed, if correctly calculates late fee (should be $3.00)
    patron_id = "123456"
    book_id = 2 # to kill a mockingbird
    borrow_book_for_test(patron_id, book_id, days_ago_borrowed=20)  # overdue by 6 days
    success, message = return_book_by_patron(patron_id, book_id)
    assert success is True
    assert "late fee" in message.lower()  # message should mention fee owed
