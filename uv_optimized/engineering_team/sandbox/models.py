from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Dict

class Category(str, Enum):
    FICTION = "Fiction"
    REFERENCE = "Reference"
    CHILDREN = "Children"

class DuplicateBookError(Exception):
    """Raised when attempting to create a book with an ID that already exists."""
    pass

class BookNotFoundError(Exception):
    """Raised when a book ID does not exist in the library."""
    pass

class LoanExceededError(Exception):
    """Raised when a loan request exceeds remaining available copies."""
    pass

@dataclass
class LoanRecord:
    loan_id: str
    book_id: str
    borrower: str
    loan_date: date
    due_date: date

@dataclass
class Book:
    book_id: str
    title: str
    category: Category
    total_copies: int = 1
    loans: List[LoanRecord] = field(default_factory=list)
