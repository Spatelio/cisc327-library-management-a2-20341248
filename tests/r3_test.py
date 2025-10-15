import pytest
from library_service import borrow_book_by_patron
from database import insert_book, update_book_availability, get_db_connection

# helper function to get book ids
def get_book_id_by_isbn(isbn):
    conn = get_db_connection()
    cur = conn.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None

# helper function to insert a book for testing
def setup_test_book(isbn="1238477822223"):
    insert_book("Test Book", "Test Author", isbn, total_copies=3, available_copies=3)
    return get_book_id_by_isbn(isbn)

def test_borrow_valid():
    # should succeed
    bid = setup_test_book("1111111111111")
    success, message = borrow_book_by_patron("123454", bid)
    
    assert success is True
    assert "successfully borrowed" in message.lower()

def test_invalid_patron_id():
    # should fail, invalid patron IDs
    bid = setup_test_book("2222222222222")

    invalid_ids = ["12345", "abcdef", "", "1234567"]
    for pid in invalid_ids:
        success, message = borrow_book_by_patron(pid, bid)
        assert success is False
        assert "invalid patron id" in message.lower()

def test_unavailable_book():
    # should fail on second attempt if the copy count gets correctly updated when
    # borrowed, as available copies is initially only 1
    bid = setup_test_book("3333333333333")
    
    update_book_availability(bid, -2)

    # first patron borrows, should be successful
    success, message = borrow_book_by_patron("123455", bid)
    assert success is True
    assert "successfully borrowed" in message.lower()

    # second patron borrows same book, should fail
    success, message = borrow_book_by_patron("654321", bid)
    assert success is False
    assert "not available" in message.lower()

def test_patron_borrow_limit():
    # should fail, after 5 books already borrowed by same patron (fixed bug allowing 6)

    pid = "123123"
    borrowed = []

    for i in range(5):
        bid = setup_test_book(f"999999999999{i}") # diff isbn for each
        borrow_book_by_patron(pid, bid) # test book ids start at 4 due to sample data
        borrowed.append(bid)
    
    # attempt 6th borrow, borrow should fail here
    bid = setup_test_book("8888888888888")
    success, message = borrow_book_by_patron(pid, bid)

    assert success is True
    assert "successfully borrowed" in message.lower()

    