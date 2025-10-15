import pytest
from datetime import datetime, timedelta
from library_service import get_patron_status_report
from database import insert_borrow_record, update_book_availability

# helper function to borrow a book for a patron for testing
def borrow_book_for_test(patron_id, book_id, days_ago_borrowed=0):
    borrow_date = datetime.now() - timedelta(days=days_ago_borrowed)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    update_book_availability(book_id, -1)
    return borrow_date, due_date

patron = "123456"
borrow_book_for_test(patron, 1, days_ago_borrowed=5)
borrow_book_for_test(patron, 2, days_ago_borrowed=3)

def test_status_report_existing_patron():
    #should return all 4 categories of the status report
    report = get_patron_status_report(patron)

    for key in ["current_loans", "total_late_fees_owed", "books_borrowed_count", "borrow_history"]:
        assert key in report

def test_status_report_no_borrowed_books():
    #patron should have no borrowed books, therefor 0 currently borrowed and 0 late fees
    report = get_patron_status_report("000001")

    assert report["books_borrowed_count"] == 0
    assert report["total_late_fees_owed"] == 0.0
    assert report["current_loans"] == []
    assert report["borrow_history"] == []

def test_status_report_has_due_dates():
    #ensures each borrowed book has a due date and is a datetime object
    report = get_patron_status_report(patron)

    for book in report["current_loans"]:
        assert "due_date" in book
        datetime.fromisoformat(book["due_date"])

def test_status_report_total_late_fees():
    #should get a non negative value for late fees
    report = get_patron_status_report(patron)

    assert report["total_late_fees_owed"] >= 0

def test_status_report_borrow_history():
    #should correctly show past borrowed (and returned) books and info in correct format
    report = get_patron_status_report(patron)
    for rec in report["borrow_history"]:
        for k in ["book_id", "title", "author", "borrow_date", "due_date", "return_date", "was_late", "fee_at_return"]:
            assert k in rec

        datetime.fromisoformat(rec["borrow_date"])
        datetime.fromisoformat(rec["due_date"])
        if rec["return_date"]:
            datetime.fromisoformat(rec["return_date"])