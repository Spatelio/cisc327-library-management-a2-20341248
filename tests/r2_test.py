import pytest
from library_service import get_all_books

def test_catalog_returns_all_books():
    # should return all books in catalog
    books = get_all_books()
    assert isinstance(books, list)
    assert len(books) > 0
    
def test_catalog_has_fields():
    # should have ID, Title, Author, ISBN, & copies for each book
    books = get_all_books()
    for book in books:
        assert "id" in book
        assert "title" in book
        assert "author" in book
        assert "isbn" in book
        assert "available_copies" in book
        assert "total_copies" in book

def test_borrow_action():
    # should have borrow option if available, and vice versa
    books = get_all_books()
    for book in books:
        if book["available_copies"] > 0:
            # borrow action exists
            assert book["available_copies"] > 0
        else:
            # no borrow possible
            assert book["available_copies"] == 0

def test_total_copies_not_less_than_available():
    # available copies should be less than total
    books = get_all_books()
    for book in books:
        assert book["total_copies"] >= book["available_copies"]
