# Library Management System - Engineering Design

## 1. Modules & File Structure

All files reside in a single flat directory (`/sandbox`). The project runs as a `uv` project where `gradio` is the only third-party package. Standard library modules only are used for backend and tests.

* **`models.py`** (assigned to `backend_engineer`): Contains dataclasses, enums, and exceptions for books, categories, loans, and validation rules.
* **`library.py`** (assigned to `backend_engineer`): Contains the core `LibraryManager` class managing books, total copies, loans, loan history, category lookups, default loan days, and duplication/over-loan prevention.
* **`app.py`** (assigned to `frontend_engineer`): Gradio web interface implementation containing all UI components, state management, and event handlers.
* **`test_library.py`** (assigned to `test_engineer`): Standard library unit tests covering models, library manager constraints, duplicate book prevention, loan capacity checks, and category reports.

---

## 2. Module Specifications: `models.py`

```python
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
```

---

## 3. Module Specifications: `library.py`

```python
from datetime import date
from typing import List, Dict, Optional
from models import Category, Book, LoanRecord, DuplicateBookError, BookNotFoundError, LoanExceededError

def get_default_loan_days(category: Category) -> int:
    ...

class LibraryManager:
    def __init__(self) -> None:
        ...

    def add_book(self, book_id: str, title: str, category: Category, total_copies: int) -> Book:
        ...

    def set_total_copies(self, book_id: str, total_copies: int) -> Book:
        ...

    def record_loan(self, book_id: str, borrower: str, loan_date: Optional[date] = None) -> LoanRecord:
        ...

    def get_remaining_copies(self, book_id: str) -> int:
        ...

    def get_books_by_category(self, category: Category) -> List[Book]:
        ...

    def get_loan_history(self, book_id: str) -> List[LoanRecord]:
        ...

    def get_book(self, book_id: str) -> Book:
        ...

    def get_all_books(self) -> List[Book]:
        ...
```

---

## 4. Module Specifications: `app.py` & Authoritative Selection State

* **Authoritative Selection State:** `selected_book_id_state = gr.State(value="")` holds the currently selected book ID. All handlers that require the active book read from this state rather than querying the UI Dropdown directly.

---

## 5. Event Wiring Table

### Structural Rules Enforced:
* **Rule 1 (No Self-Re-entrant Outputs):** A handler bound to a component's own listener must never write back to that same component. If handler $H$ is triggered by component $X$, then $X$ must not appear in $H$'s outputs.
* **Rule 2 (Dropdown/Radio/CheckboxGroup Updates):** Any Dropdown, Radio, or CheckboxGroup appearing in a handler's outputs must receive `gr.update(choices=..., value=...)` carrying both choices and value. A bare list or string sets only the value, which Gradio rejects when it is not already among the existing choices.

| Trigger Component | Trigger Method | Handler Name | Input Components | Output Components | Return Contract (Exact Position Mapping) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `add_btn` | `.click()` | `handle_add_book` | `[id_input, title_input, category_input, copies_input]` | `[book_dropdown, status_output, catalog_dataframe]` | Returns 3 values: <br>1. `gr.update(choices=..., value=...)` for `book_dropdown`<br>2. Status message string for `status_output`<br>3. Updated data list/dataframe for `catalog_dataframe` |
| `book_dropdown` | `.change()` | `handle_select_book` | `[book_dropdown]` | `[selected_book_id_state, details_output, history_dataframe]` | Returns 3 values:<br>1. Selected book ID string for `selected_book_id_state`<br>2. Book detail string for `details_output`<br>3. Loan history list/dataframe for `history_dataframe` |
| `loan_btn` | `.click()` | `handle_record_loan` | `[selected_book_id_state, borrower_input]` | `[status_output, details_output, history_dataframe, catalog_dataframe]` | Returns 4 values:<br>1. Status message string for `status_output`<br>2. Refreshed details string for `details_output`<br>3. Refreshed loan history for `history_dataframe`<br>4. Refreshed catalog for `catalog_dataframe` |
| `update_copies_btn` | `.click()` | `handle_update_copies` | `[selected_book_id_state, new_copies_input]` | `[status_output, details_output, catalog_dataframe]` | Returns 3 values:<br>1. Status message string for `status_output`<br>2. Refreshed details string for `details_output`<br>3. Refreshed catalog for `catalog_dataframe` |
| `filter_category_btn` | `.click()` | `handle_filter_category` | `[filter_category_input]` | `[filtered_catalog_dataframe]` | Returns 1 value:<br>1. Filtered books dataframe for `filtered_catalog_dataframe` |

---

## 6. Deliverables & Acceptance Criteria

### `backend_engineer`
* **Deliverables:** `models.py`, `library.py`
* **Acceptance Criteria:**
  1. `get_default_loan_days` returns correct fixed days for Fiction, Reference, and Children.
  2. `LibraryManager.add_book` raises `DuplicateBookError` on duplicate book IDs.
  3. `LibraryManager.record_loan` raises `LoanExceededError` when active loans equal or exceed `total_copies`, and calculates remaining copies correctly.
  4. Code uses Python standard library only and contains no third-party dependencies.

### `frontend_engineer`
* **Deliverables:** `app.py`
* **Acceptance Criteria:**
  1. Implements Gradio 6 blocks interface satisfying all functional requirements (add book, set copies, record loan, calculate remaining copies, filter category, view loan history).
  2. Conforms strictly to Rule 1 (no self-referencing output component in trigger listener) and Rule 2 (`gr.update(choices=..., value=...)` for all Dropdown outputs).
  3. Uses `gr.State` as the single source of truth for the selected book ID.

### `test_engineer`
* **Deliverables:** `test_library.py`
* **Acceptance Criteria:**
  1. Unit tests written using `unittest` or `pytest` (standard library compatible).
  2. Tests cover successful book creation, duplicate ID rejection, copy updates, loan recording within limits, loan rejection when exceeding capacity, category filtering, and loan history reporting.
  3. All tests pass cleanly in the `uv` sandbox environment.