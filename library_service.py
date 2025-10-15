"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books,
    get_patron_borrowed_books,
    get_db_connection
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    # fix: borrow limit stops at 5, not 6
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Accepts patron_id and book_id, verifies active loan, applies late fee,
    updates availability and closes borrow record.
    """
    #validate patron ID format
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    #verify there is an active loan for patron/book
    active_loans = get_patron_borrowed_books(patron_id)
    active_record = next((r for r in active_loans if r["book_id"] == book_id), None)
    if not active_record:
        return False, "No active borrow record found for this patron and book."

    #compute late fee
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    fee = float(fee_info.get('fee_amount', 0.0))
    days_overdue = int(fee_info.get('days_overdue', 0))

    #close borrowing and increment availability
    now = datetime.now()
    if not update_borrow_record_return_date(patron_id, book_id, now):
        return False, "Database error occurred while closing the borrow record."
    if not update_book_availability(book_id, +1):
        return False, "Database error occurred while updating book availability."

    if fee > 0:
        return True, (f'Return processed for "{book["title"]}". '
                      f'Late by {days_overdue} day(s). Fee: ${fee:.2f}.')
    else:
        return True, (f'Return processed for "{book["title"]}". '
                      f'No late fee.')

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    """
    #get active borrow info
    active_borrowed = get_patron_borrowed_books(patron_id)
    record = next((r for r in active_borrowed if r["book_id"] == book_id), None)
    if not record:
        return {'fee_amount': 0.00, 'days_overdue': 0,
            'status': 'No active borrow record found for this patron and book'}

    due_dt = record['due_date']
    ref_dt = datetime.now()
    status = 'Active loan'

    days_overdue = max(0, (ref_dt - due_dt).days)

    #compute fee
    first_seven = min(days_overdue, 7) * 0.50
    after_seven = max(days_overdue - 7, 0) * 1.00
    fee = min(first_seven + after_seven, 15.00)

    return {'fee_amount': round(fee, 2), 'days_overdue': int(days_overdue), 'status': status}

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    """
    if not search_term:
        return []

    stype = (search_type or "title").strip().lower()
    term = search_term.strip()

    #exact ISBN search
    if stype == "isbn":
        cleaned = term.replace(" ", "")
        if len(cleaned) == 13 and cleaned.isdigit():
            book = get_book_by_isbn(cleaned)
            return [book] if book else []
        return []

    #partial, case-insensitive title/author search
    books = get_all_books()  # already ordered by title in DB layer
    needle = term.lower()

    if stype == "author":
        return [b for b in books if needle in str(b.get("author", "")).lower()]

    #default to title search
    return [b for b in books if needle in str(b.get("title", "")).lower()]

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    """

    #validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            "patron_id": patron_id,
            "current_loans": [],
            "books_borrowed_count": 0,
            "total_late_fees_owed": 0.00,
            "borrow_history": [],
            "status": "Invalid patron ID (must be 6 digits)",
        }

    current_loans_raw = get_patron_borrowed_books(patron_id)

    current_loans = []
    total_owed = 0.0
    for loan in current_loans_raw:
        fee_info = calculate_late_fee_for_book(patron_id, loan["book_id"])
        fee_amt = float(fee_info.get("fee_amount", 0.0))
        days_over = int(fee_info.get("days_overdue", 0))
        if days_over > 0 and fee_amt > 0:
            total_owed += fee_amt

        current_loans.append({
            "book_id": loan["book_id"],
            "title": loan["title"],
            "author": loan["author"],
            "borrow_date": loan["borrow_date"].isoformat(),
            "due_date": loan["due_date"].isoformat(),
            "is_overdue": loan["is_overdue"],
        })

    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT br.book_id, br.borrow_date, br.due_date, br.return_date,
                   b.title, b.author
            FROM borrow_records br
            JOIN books b ON br.book_id = b.id
            WHERE br.patron_id = ?
            ORDER BY br.borrow_date DESC
            """,
            (patron_id,),
        ).fetchall()
    finally:
        conn.close()

    def _fee_at_return(due_dt: datetime, ret_dt: datetime) -> float:
        days_over = max(0, (ret_dt - due_dt).days)
        first_seven = min(days_over, 7) * 0.50
        after_seven = max(days_over - 7, 0) * 1.00
        return round(min(first_seven + after_seven, 15.00), 2)

    history = []
    for r in rows:
        borrow_dt = datetime.fromisoformat(r["borrow_date"])
        due_dt = datetime.fromisoformat(r["due_date"])
        ret_iso = None
        was_late = False
        fee_ret = 0.0

        if r["return_date"] is not None:
            ret_dt = datetime.fromisoformat(r["return_date"])
            ret_iso = ret_dt.isoformat()
            fee_ret = _fee_at_return(due_dt, ret_dt)
            was_late = (ret_dt - due_dt).days > 0

        history.append({
            "book_id": r["book_id"],
            "title": r["title"],
            "author": r["author"],
            "borrow_date": borrow_dt.isoformat(),
            "due_date": due_dt.isoformat(),
            "return_date": ret_iso,
            "was_late": was_late,
            "fee_at_return": fee_ret,
        })

    return {
        "patron_id": patron_id,
        "current_loans": current_loans,
        "books_borrowed_count": len(current_loans),
        "total_late_fees_owed": round(total_owed, 2),
        "borrow_history": history,
    }

