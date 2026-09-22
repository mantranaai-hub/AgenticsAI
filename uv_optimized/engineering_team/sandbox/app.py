import gradio as gr
from datetime import date
from typing import List, Dict, Any, Tuple
from models import Category, DuplicateBookError, BookNotFoundError, LoanExceededError, Book, LoanRecord
from library import LibraryManager, get_default_loan_days

library_manager = LibraryManager()

def get_catalog_data(manager: LibraryManager) -> List[List[Any]]:
    books = manager.get_all_books()
    data = []
    for b in books:
        remaining = manager.get_remaining_copies(b.book_id)
        data.append([
            b.book_id,
            b.title,
            b.category.value,
            b.total_copies,
            remaining,
            len(b.loans)
        ])
    return data

def get_filtered_catalog_data(manager: LibraryManager, category_str: str) -> List[List[Any]]:
    try:
        cat = Category(category_str)
        books = manager.get_books_by_category(cat)
    except Exception:
        books = []
    data = []
    for b in books:
        remaining = manager.get_remaining_copies(b.book_id)
        data.append([
            b.book_id,
            b.title,
            b.category.value,
            b.total_copies,
            remaining,
            len(b.loans)
        ])
    return data

def get_loan_history_data(manager: LibraryManager, book_id: str) -> List[List[Any]]:
    if not book_id:
        return []
    try:
        history = manager.get_loan_history(book_id)
        data = []
        for l in history:
            data.append([
                l.loan_id,
                l.book_id,
                l.borrower,
                str(l.loan_date),
                str(l.due_date)
            ])
        return data
    except Exception:
        return []

def build_app() -> gr.Blocks:
    global library_manager
    library_manager = LibraryManager()

    with gr.Blocks(title="Library Management System") as demo:
        selected_book_id_state = gr.State(value="")

        gr.Markdown(
            "# Library Management System\n"
            "Manage books, track copies, record loans, and inspect category catalogs and loan history."
        )

        with gr.Tabs():
            with gr.TabItem("Catalog & Loans"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Add New Book")
                        id_input = gr.Textbox(label="Book ID", placeholder="e.g. B001")
                        title_input = gr.Textbox(label="Book Title", placeholder="e.g. The Great Gatsby")
                        category_input = gr.Dropdown(
                            choices=[c.value for c in Category],
                            value=Category.FICTION.value,
                            label="Category"
                        )
                        copies_input = gr.Number(value=1, label="Total Copies", precision=0)
                        add_btn = gr.Button("Add Book", variant="primary")

                        gr.Markdown("---")
                        gr.Markdown("### Select & Manage Book")
                        
                        initial_book_choices = [b.book_id for b in library_manager.get_all_books()]
                        book_dropdown = gr.Dropdown(
                            choices=initial_book_choices,
                            value=None,
                            label="Select Book ID",
                            interactive=True,
                            allow_custom_value=True
                        )

                        update_copies_input = gr.Number(value=1, label="New Total Copies", precision=0)
                        update_copies_btn = gr.Button("Update Copies")

                        gr.Markdown("### Record Loan")
                        borrower_input = gr.Textbox(label="Borrower Name", placeholder="e.g. Jane Doe")
                        loan_btn = gr.Button("Record Loan", variant="secondary")

                    with gr.Column(scale=2):
                        status_output = gr.Textbox(label="System Status / Messages", value="System ready.", interactive=False)
                        
                        gr.Markdown("### Selected Book Details")
                        details_output = gr.Markdown("No book selected.")

                        gr.Markdown("### Library Catalog")
                        catalog_headers = ["Book ID", "Title", "Category", "Total Copies", "Available", "Active Loans"]
                        catalog_dataframe = gr.Dataframe(
                            headers=catalog_headers,
                            value=get_catalog_data(library_manager),
                            interactive=False
                        )

                        gr.Markdown("### Loan History for Selected Book")
                        history_headers = ["Loan ID", "Book ID", "Borrower", "Loan Date", "Due Date"]
                        history_dataframe = gr.Dataframe(
                            headers=history_headers,
                            value=[],
                            interactive=False
                        )

            with gr.TabItem("Category Filter"):
                with gr.Row():
                    filter_category_input = gr.Dropdown(
                        choices=[c.value for c in Category],
                        value=Category.FICTION.value,
                        label="Filter by Category"
                    )
                    filter_category_btn = gr.Button("Filter Books", variant="primary")
                
                filtered_catalog_dataframe = gr.Dataframe(
                    headers=["Book ID", "Title", "Category", "Total Copies", "Available", "Active Loans"],
                    value=get_filtered_catalog_data(library_manager, Category.FICTION.value),
                    interactive=False
                )

        def handle_add_book(book_id: str, title: str, category_str: str, total_copies: float):
            try:
                if not book_id or not title:
                    status = "Error: Book ID and Title cannot be empty."
                    all_ids = [b.book_id for b in library_manager.get_all_books()]
                    val = book_dropdown.value if 'book_dropdown' in globals() else (all_ids[0] if all_ids else None)
                    return gr.update(choices=all_ids, value=val if val in all_ids else (all_ids[0] if all_ids else None)), status, get_catalog_data(library_manager)
                
                cat = Category(category_str)
                copies = int(total_copies)
                library_manager.add_book(book_id.strip(), title.strip(), cat, copies)
                status = f"Success: Book '{title}' ({book_id}) added successfully."
                all_ids = [b.book_id for b in library_manager.get_all_books()]
                return gr.update(choices=all_ids, value=book_id.strip()), status, get_catalog_data(library_manager)
            except DuplicateBookError as e:
                status = f"Error: {e}"
                all_ids = [b.book_id for b in library_manager.get_all_books()]
                return gr.update(choices=all_ids, value=all_ids[0] if all_ids else None), status, get_catalog_data(library_manager)
            except Exception as e:
                status = f"Error: {e}"
                all_ids = [b.book_id for b in library_manager.get_all_books()]
                return gr.update(choices=all_ids, value=all_ids[0] if all_ids else None), status, get_catalog_data(library_manager)

        add_btn.click(
            fn=handle_add_book,
            inputs=[id_input, title_input, category_input, copies_input],
            outputs=[book_dropdown, status_output, catalog_dataframe]
        )

        def handle_select_book(book_id: str):
            if not book_id:
                return "", "No book selected.", []
            try:
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                default_days = get_default_loan_days(book.category)
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Title:** {book.title}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}\n\n"
                    f"**Standard Loan Period:** {default_days} days"
                )
                history = get_loan_history_data(library_manager, book_id)
                return book_id, details, history
            except BookNotFoundError:
                return "", f"Book '{book_id}' not found.", []
            except Exception as e:
                return "", f"Error: {e}", []

        book_dropdown.change(
            fn=handle_select_book,
            inputs=[book_dropdown],
            outputs=[selected_book_id_state, details_output, history_dataframe]
        )

        def handle_record_loan(book_id: str, borrower: str):
            if not book_id:
                return "Error: No book selected for loan.", "No book selected.", [], get_catalog_data(library_manager)
            if not borrower or not borrower.strip():
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Title:** {book.title}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}"
                )
                return "Error: Borrower name cannot be empty.", details, get_loan_history_data(library_manager, book_id), get_catalog_data(library_manager)
            
            try:
                loan = library_manager.record_loan(book_id, borrower.strip())
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                status = f"Success: Loan {loan.loan_id} recorded for {borrower} on book '{book.title}' (Due: {loan.due_date})."
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Title:** {book.title}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}"
                )
                history = get_loan_history_data(library_manager, book_id)
                catalog = get_catalog_data(library_manager)
                return status, details, history, catalog
            except LoanExceededError as e:
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Title:** {book.title}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}"
                )
                status = f"Error: {e}"
                return status, details, get_loan_history_data(library_manager, book_id), get_catalog_data(library_manager)
            except Exception as e:
                book = library_manager.get_book(book_id) if book_id in library_manager.books else None
                details = f"Error encountered." if not book else f"**ID:** {book.book_id}"
                status = f"Error: {e}"
                return status, details, get_loan_history_data(library_manager, book_id), get_catalog_data(library_manager)

        loan_btn.click(
            fn=handle_record_loan,
            inputs=[selected_book_id_state, borrower_input],
            outputs=[status_output, details_output, history_dataframe, catalog_dataframe]
        )

        def handle_update_copies(book_id: str, new_copies: float):
            if not book_id:
                return "Error: No book selected.", "No book selected.", get_catalog_data(library_manager)
            try:
                copies = int(new_copies)
                library_manager.set_total_copies(book_id, copies)
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                status = f"Success: Total copies for '{book.title}' updated to {copies}."
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Title:** {book.title}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}"
                )
                catalog = get_catalog_data(library_manager)
                return status, details, catalog
            except ValueError as e:
                book = library_manager.get_book(book_id)
                remaining = library_manager.get_remaining_copies(book_id)
                status = f"Error: {e}"
                details = (
                    f"**ID:** {book.book_id}\n\n"
                    f"**Category:** {book.category.value}\n\n"
                    f"**Total Copies:** {book.total_copies}\n\n"
                    f"**Remaining Available:** {remaining}\n\n"
                    f"**Active Loans Count:** {len(book.loans)}"
                )
                return status, details, get_catalog_data(library_manager)
            except Exception as e:
                status = f"Error: {e}"
                return status, "Error.", get_catalog_data(library_manager)

        update_copies_btn.click(
            fn=handle_update_copies,
            inputs=[selected_book_id_state, update_copies_input],
            outputs=[status_output, details_output, catalog_dataframe]
        )

        def handle_filter_category(category_str: str):
            return get_filtered_catalog_data(library_manager, category_str)

        filter_category_btn.click(
            fn=handle_filter_category,
            inputs=[filter_category_input],
            outputs=[filtered_catalog_dataframe]
        )

    return demo

if __name__ == "__main__":
    app = build_app()
    app.launch()
