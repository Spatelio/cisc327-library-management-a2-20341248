Sascha Patel, 20341248

### VIEW FILE ON FULL SCREEN FOR UNDISTORTED TABLE VIEW ###

|     Function name     | Implementation Status |                            Missing?                            |
------------------------------------------------------------------------------------------------------------------
|  add book to catalog  |       COPMLETE        |                                                                |
|    catalog display    |       COPMLETE        |                                                                |
|  borrowing interface  |        PARTIAL        | incorrect conditional statement (allows for 6 max books not 5) |
|      book return      |        MISSING        |                       whole functionality                      |
|  late fee calculation |        MISSING        |                       whole functionality                      |
|  book search function |        MISSING        |                       whole functionality                      |
|  patron status report |        MISSING        |                       whole functionality                      |


UNIT TESTS

R1:
- tests for success with valid input
- tests for failure of inputs with missing title, incorrect ISBN length, negative copy counts, and adding duplicate ISBNs

R2:
- tests that books show up in catalog and that all books display all info
- tests if borrow action works for available books, and doesnt for non available books
- makes sure available is less than total copies

R3
- tests a valid case where a test book is created and borrowed by patron
- tests borrowing a book with various invalid patron ids to verify checking
- tests updating functionality of available copies within the test of borrowing an unavailable book
- tests patron borrowing limit by borrowing more than 5 books (flaw here)

R4
- tests a successful return by a patron passing patron id and book id as parameters
- tests bad cases with invalid patron as well as a valid patron but an unborrowed book
- tests for is late fee is calculated and displayed upon an overdue return

R5
- tests late fee calculation for each possible case
    - on time (under 14 days after borrowed)
    - overdue under 7 days late
    - overdue over 7 days later (but under $15 cap)
    - overdue by a long time (max fee)
- also tests function for a book not borrowed (but since the late fee calculation, when service functions are fully
  implemented, will most likely only be called within the return book function, this may not be needed as the verification of patron records will already be done the return fucntion before late fee calculation occurs)

R6
- tests for a search with exact title
- tests for a partial, all lowercase title search
- tests for a search by author name
- tests for a search by exact ISBN
- tests for a search with no results

R7
- tests that the patron status report returns all correct categories
- tests for a patron with no borrow history or currently borrowed books
- tests for existence of due dates within the report for borrowed books
- tests validity of total late fee report
- tests for existence of each book's info in borrow history