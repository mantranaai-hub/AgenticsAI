import unittest
from datetime import date, timedelta
from models import Category, Book, LoanRecord, DuplicateBookError, BookNotFoundError, LoanExceededError
from library import LibraryManager, get_default_loan_days
from app import build_app, library_manager

class TestModelsAndLibrary(unittest.TestCase):
    
    def setUp(self):
        self.manager = LibraryManager()

    def test_get_default_loan_days(self):
        self.assertEqual(get_default_loan_days(Category.FICTION), 14)
        self.assertEqual(get_default_loan_days(Category.REFERENCE), 7)
        self.assertEqual(get_default_loan_days(Category.CHILDREN), 21)
        self.assertEqual(get_default_loan_days("Unknown"), 14)

    def test_add_book_success(self):
        book = self.manager.add_book("B1", "Test Book", Category.FICTION, 3)
        self.assertEqual(book.book_id, "B1")
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.category, Category.FICTION)
        self.assertEqual(book.total_copies, 3)
        self.assertEqual(len(self.manager.get_all_books()), 1)

    def test_add_book_duplicate(self):
        self.manager.add_book("B1", "Book 1", Category.FICTION, 2)
        with self.assertRaises(DuplicateBookError):
            self.manager.add_book("B1", "Book 1 Duplicate", Category.FICTION, 1)

    def test_add_book_negative_copies(self):
        with self.assertRaises(ValueError):
            self.manager.add_book("B2", "Negative Copies", Category.CHILDREN, -1)

    def test_set_total_copies_success(self):
        self.manager.add_book("B1", "Book 1", Category.FICTION, 2)
        updated = self.manager.set_total_copies("B1", 5)
        self.assertEqual(updated.total_copies, 5)

    def test_set_total_copies_negative(self):
        self.manager.add_book("B1", "Book 1", Category.FICTION, 2)
        with self.assertRaises(ValueError):
            self.manager.set_total_copies("B1", -2)

    def test_set_total_copies_below_active_loans(self):
        self.manager.add_book("B1", "Book 1", Category.FICTION, 2)
        self.manager.record_loan("B1", "Alice")
        self.manager.record_loan("B1", "Bob")
        with self.assertRaises(ValueError):
            self.manager.set_total_copies("B1", 1)

    def test_set_total_copies_book_not_found(self):
        with self.assertRaises(BookNotFoundError):
            self.manager.set_total_copies("NONEXISTENT", 5)

    def test_record_loan_success(self):
        self.manager.add_book("B1", "Book 1", Category.FICTION, 2)
        loan_date = date(2023, 1, 1)
        loan = self.manager.record_loan("B1", "Alice", loan_date=loan_date)
        self.assertEqual(loan.book_id, "B1")
        self.assertEqual(loan.borrower, "Alice")
        self.assertEqual(loan.loan_date, loan_date)
        self.assertEqual(loan.due_date, loan_date + timedelta(days=14))
        self.assertEqual(self.manager.get_remaining_copies("B1"), 1)

    def test_record_loan_default_date(self):
        self.manager.add_book("B1", "Book 1", Category.REFERENCE, 1)
        loan = self.manager.record_loan("B1", "Charlie")
        self.assertEqual(loan.due_date, date.today() + timedelta(days=7))

    def test_record_loan_exceeded(self):
        self.manager.add_book("B1", "Book 1", Category.CHILDREN, 1)
        self.manager.record_loan("B1", "Alice")
        with self.assertRaises(LoanExceededError):
            self.manager.record_loan("B1", "Bob")

    def test_record_loan_book_not_found(self):
        with self.assertRaises(BookNotFoundError):
            self.manager.record_loan("MISSING", "Alice")

    def test_get_books_by_category(self):
        self.manager.add_book("B1", "F1", Category.FICTION, 1)
        self.manager.add_book("B2", "R1", Category.REFERENCE, 1)
        self.manager.add_book("B3", "F2", Category.FICTION, 1)
        
        fiction_books = self.manager.get_books_by_category(Category.FICTION)
        self.assertEqual(len(fiction_books), 2)
        self.assertEqual({b.book_id for b in fiction_books}, {"B1", "B3"})

    def test_get_loan_history(self):
        self.manager.add_book("B1", "F1", Category.FICTION, 2)
        self.manager.record_loan("B1", "Alice")
        self.manager.record_loan("B1", "Bob")
        history = self.manager.get_loan_history("B1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].borrower, "Alice")
        self.assertEqual(history[1].borrower, "Bob")

    def test_get_loan_history_not_found(self):
        with self.assertRaises(BookNotFoundError):
            self.manager.get_loan_history("BAD_ID")

    def test_get_book_not_found(self):
        with self.assertRaises(BookNotFoundError):
            self.manager.get_book("BAD_ID")


class TestAppHandlerContracts(unittest.TestCase):
    
    def setUp(self):
        self.demo = build_app()

    def test_build_app_returns_blocks(self):
        self.assertIsNotNone(self.demo)

    def test_helpers_and_handlers_directly(self):
        from app import library_manager, get_catalog_data, get_filtered_catalog_data, get_loan_history_data
        
        catalog = get_catalog_data(library_manager)
        self.assertIsInstance(catalog, list)

        filtered = get_filtered_catalog_data(library_manager, "Fiction")
        self.assertIsInstance(filtered, list)

        history = get_loan_history_data(library_manager, "")
        self.assertEqual(history, [])

    def test_fn_contracts(self):
        import gradio as gr
        for fn_key, fn_obj in self.demo.fns.items():
            inputs = getattr(fn_obj, "inputs", [])
            outputs = getattr(fn_obj, "outputs", [])
            for inp in inputs:
                if inp in outputs:
                    self.fail(f"Handler violates Rule 1: component is its own output.")

if __name__ == "__main__":
    unittest.main()