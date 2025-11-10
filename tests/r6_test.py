import pytest
from services.library_service import search_books_in_catalog

def test_search_by_exact_title():
    # should succeed
    results = search_books_in_catalog("The Great Gatsby", "title")
    assert any(b['title'] == "The Great Gatsby" for b in results)

def test_search_by_partial_title_case_insensitive():
    # should succeed, partial match
    results = search_books_in_catalog("kill a", "title")
    assert any("kill a" in b['title'].lower() for b in results)

def test_search_by_author_partial_case_insensitive():
    # should succeed, orwell author of 1984
    results = search_books_in_catalog("orwell", "author")
    assert any("orwell" in b['author'].lower() for b in results)

def test_search_by_isbn_exact_match():
    # should succeed, 9780451524935 is exact ISBN for 1984
    results = search_books_in_catalog("9780451524935", "isbn")
    assert any(b['isbn'] == "9780451524935" for b in results)

def test_search_no_results():
    # should return nothing in results as book does not exist
    results = search_books_in_catalog("Nonexistent Book", "title")
    assert results == []