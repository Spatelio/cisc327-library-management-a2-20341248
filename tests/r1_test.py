import pytest
from library_service import add_book_to_catalog

# RESET LIBRARY.DB AND RUN APP SETUP BETWEEN EACH TEST SCRIPT FILE (R1-R7)

def test_add_book_valid():
    # should succeed, valid input
    success, message = add_book_to_catalog("A New Book", "Sascha", "1234567830123", 5)

    assert success is True
    assert "successfully" in message.lower()

def test_add_book_missing_title():
    # should fail, missing title
    success, message = add_book_to_catalog("", "Sascha", "1234567890123", 5)

    assert success is False
    assert "title" in message.lower()

def test_add_book_invalid_isbn_length():
    # should fail, ISBN too short
    success, message = add_book_to_catalog("Book", "Sascha", "12345", 5)

    assert success is False
    assert "13 digits" in message.lower()

def test_add_book_negative_copies():
    # should fail, negative copies
    success, message = add_book_to_catalog("Book", "Sascha", "1234567890123", -1)

    assert success is False
    assert "positive" in message.lower()

def test_add_book_duplicate_isbn():
    # should fail (second add), duplicate ISBN
    add_book_to_catalog("Book A", "Sascha", "9999999999999", 5)
    success, message = add_book_to_catalog("Book B", "Sascha", "9999999999999", 3)

    assert success is False
    assert "isbn" in message.lower()


