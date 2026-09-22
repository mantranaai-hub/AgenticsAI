import warnings
import sys

# 1. Turn warnings into errors at the top of the file
warnings.filterwarnings("error")

import gradio as gr
from app import build_app, library_manager, get_catalog_data, get_filtered_catalog_data, get_loan_history_data
from models import Category, DuplicateBookError, BookNotFoundError, LoanExceededError

def main():
    print("Building app blocks...")
    demo = build_app()

    print("Validation script running...")
    
    # Test library manager & handlers directly
    manager = library_manager

    # 1. Add book
    book = manager.add_book("L1", "Python Guide", Category.FICTION, 2)
    assert book.book_id == "L1"
    
    # 2. Select book / get book details
    selected_id = book.book_id
    assert selected_id == "L1"
    
    # 3. Update copies
    manager.set_total_copies("L1", 3)
    assert manager.get_remaining_copies("L1") == 3
    
    # 4. Record loan
    loan = manager.record_loan("L1", "Student A")
    assert loan.borrower == "Student A"
    assert manager.get_remaining_copies("L1") == 2
    
    # 5. Filter category
    fiction_books = manager.get_books_by_category(Category.FICTION)
    assert len(fiction_books) >= 1

    # 6. Loan history
    history = manager.get_loan_history("L1")
    assert len(history) == 1

    print("[OK] Smoke sequence completed successfully!")
    print("_validate.py passed all checks with exit code 0.")

if __name__ == "__main__":
    main()
