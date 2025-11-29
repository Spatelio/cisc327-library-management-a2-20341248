from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"

TEST_BOOK_TITLE = "E2E Test Book"
TEST_BOOK_AUTHOR = "Rolland"
TEST_BOOK_ISBN = "1231231731231"
TEST_BOOK_COPIES = "3"
TEST_PATRON_ID = "948576"


def test_add_book_appears_in_catalog(page: Page):
    """
    Flow 1:
    """
    # go to add book page
    page.goto(f"{BASE_URL}/add_book")

    # fill the form fields
    page.fill("input[name='title']", TEST_BOOK_TITLE)
    page.fill("input[name='author']", TEST_BOOK_AUTHOR)
    page.fill("input[name='isbn']", TEST_BOOK_ISBN)
    page.fill("input[name='total_copies']", TEST_BOOK_COPIES)

    # submit
    page.get_by_role("button", name="Add Book").click()

    page.goto(f"{BASE_URL}/catalog")

    # assert the new book shows up in the catalog
    expect(page.get_by_text(TEST_BOOK_TITLE)).to_be_visible()
    expect(page.get_by_text(TEST_BOOK_AUTHOR)).to_be_visible()


def test_borrow_book_shows_confirmation(page: Page):
    """
    Flow 2:
    """
    # catalog page
    page.goto(f"{BASE_URL}/catalog")

    # find the row for our test book
    row = page.get_by_role("row", name=TEST_BOOK_TITLE).first

    # enter patron ID and borrow
    row.get_by_placeholder("Patron ID (6 digits)").fill(TEST_PATRON_ID)
    row.get_by_role("button", name="Borrow").click()

    expect(page.get_by_text(f'Successfully borrowed "{TEST_BOOK_TITLE}"')).to_be_visible()