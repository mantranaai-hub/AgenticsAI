from models import Category, DuplicateBookError, BookNotFoundError, LoanExceededError
from library import LibraryManager, get_default_loan_days
from datetime import date

def main():
    print("Running verification script...")
    
    # Test get_default_loan_days
    assert get_default_loan_days(Category.FICTION) == 14
    assert get_default_loan_days(Category.REFERENCE) == 7
    assert get_default_loan_days(Category.CHILDREN) == 21
    print("[OK] get_default_loan_days passed")

    manager = LibraryManager()

    # Success path: add book
    book = manager.add_book("B1", "The Hobbit", Category.FICTION, 2)
    assert book.book_id == "B1"
    assert book.total_copies == 2
    print("[OK] add_book success path passed")

    # Rejection path: duplicate book
    try:
        manager.add_book("B1", "Duplicate Hobbit", Category.FICTION, 1)
        raise AssertionError("Expected DuplicateBookError")
    except DuplicateBookError as e:
        print(f"[OK] add_book rejection path passed: {e}")

    # Success path: set total copies
    manager.set_total_copies("B1", 3)
    assert manager.get_remaining_copies("B1") == 3
    print("[OK] set_total_copies success path passed")

    # Success path: record loan
    loan1 = manager.record_loan("B1", "Alice", date(2023, 1, 1))
    assert loan1.borrower == "Alice"
    assert loan1.due_date == date(2023, 1, 15)
    assert manager.get_remaining_copies("B1") == 2
    print("[OK] record_loan success path passed")

    # Loan remaining copies until exhaustion (total copies is 3, already 1 loaned, loan 2 more)
    manager.record_loan("B1", "Bob")
    manager.record_loan("B1", "Charlie")
    assert manager.get_remaining_copies("B1") == 0
    print("[OK] copies exhaustion passed")

    # Rejection path: loan exceeded
    try:
        manager.record_loan("B1", "Dave")
        raise AssertionError("Expected LoanExceededError")
    except LoanExceededError as e:
        print(f"[OK] record_loan rejection path passed: {e}")

    # Success path: get books by category
    manager.add_book("B2", "Python Programming", Category.REFERENCE, 1)
    fiction_books = manager.get_books_by_category(Category.FICTION)
    assert len(fiction_books) == 1
    assert fiction_books[0].book_id == "B1"
    print("[OK] get_books_by_category passed")

    # Success path: get loan history
    history = manager.get_loan_history("B1")
    assert len(history) == 3
    assert history[0].borrower == "Alice"
    print("[OK] get_loan_history passed")

    # Rejection path: book not found
    try:
        manager.get_book("NONEXISTENT")
        raise AssertionError("Expected BookNotFoundError")
    except BookNotFoundError as e:
        print(f"[OK] book not found rejection path passed: {e}")

    print("All verification checks passed successfully!")

if __name__ == "__main__":
    main()
