from datetime import date, timedelta
from typing import List, Dict, Optional
from models import Category, Book, LoanRecord, DuplicateBookError, BookNotFoundError, LoanExceededError

def get_default_loan_days(category: Category) -> int:
    """Returns fixed loan periods for Fiction, Reference, and Children."""
    if category == Category.FICTION:
        return 14
    elif category == Category.REFERENCE:
        return 7
    elif category == Category.CHILDREN:
        return 21
    else:
        return 14

class LibraryManager:
    def __init__(self) -> None:
        self.books: Dict[str, Book] = {}
        self._loan_counter: int = 0

    def add_book(self, book_id: str, title: str, category: Category, total_copies: int) -> Book:
        if book_id in self.books:
            raise DuplicateBookError(f"Book with ID '{book_id}' already exists.")
        if total_copies < 0:
            raise ValueError("Total copies cannot be negative.")
        book = Book(book_id=book_id, title=title, category=category, total_copies=total_copies)
        self.books[book_id] = book
        return book

    def set_total_copies(self, book_id: str, total_copies: int) -> Book:
        book = self.get_book(book_id)
        if total_copies < 0:
            raise ValueError("Total copies cannot be negative.")
        current_loans_count = len(book.loans)
        if total_copies < current_loans_count:
            raise ValueError(f"Cannot set total copies to {total_copies}; there are already {current_loans_count} active loans.")
        book.total_copies = total_copies
        return book

    def record_loan(self, book_id: str, borrower: str, loan_date: Optional[date] = None) -> LoanRecord:
        book = self.get_book(book_id)
        remaining = self.get_remaining_copies(book_id)
        if remaining <= 0:
            raise LoanExceededError(f"Cannot loan book '{book_id}': no remaining available copies.")
        
        if loan_date is None:
            loan_date = date.today()
            
        days = get_default_loan_days(book.category)
        due_date = loan_date + timedelta(days=days)
        
        self._loan_counter += 1
        loan_id = f"L{self._loan_counter:03d}"
        
        loan_record = LoanRecord(
            loan_id=loan_id,
            book_id=book_id,
            borrower=borrower,
            loan_date=loan_date,
            due_date=due_date
        )
        book.loans.append(loan_record)
        return loan_record

    def get_remaining_copies(self, book_id: str) -> int:
        book = self.get_book(book_id)
        return book.total_copies - len(book.loans)

    def get_books_by_category(self, category: Category) -> List[Book]:
        return [book for book in self.books.values() if book.category == category]

    def get_loan_history(self, book_id: str) -> List[LoanRecord]:
        book = self.get_book(book_id)
        return list(book.loans)

    def get_book(self, book_id: str) -> Book:
        if book_id not in self.books:
            raise BookNotFoundError(f"Book with ID '{book_id}' not found.")
        return self.books[book_id]

    def get_all_books(self) -> List[Book]:
        return list(self.books.values())
