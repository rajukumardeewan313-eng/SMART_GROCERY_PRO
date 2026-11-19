# SMART GROCERY PRO

A Python desktop grocery management application with role-based access and an explicitly implemented singly linked list for product traversal.

## Features
- Separate Admin, Employee and Customer accounts/permissions
- Admin dashboard, product CRUD, staff/customer list, orders and reports
- Employee dashboard, point of sale, product/stock view and order history
- Customer registration, optional profile photo, product shop, cart, checkout and order history
- Admin, employee and customer profile editing with photo upload
- SQLite persistence
- Product data loaded into a custom singly linked list (`ProductLinkedList`) for traversal

## Requirements
- Python 3.10+
- CustomTkinter

Install:
```bash
python -m pip install -r requirements.txt
```

Run:
```bash
python main.py
```

## Demo admin login
- Username: `admin`
- Password: `admin123`

Change the demo password and create employee accounts before real use.

## Notes
- Customer registration is available from the login screen.
- Admin creates employee accounts from **Customers & Staff**.
- Profile and product photo files selected by the user are copied into the local `uploads/` folder.
- Product images are currently stored as file paths; the current GUI focuses on product data and operations rather than rendering image thumbnails.
- This is an academic/local desktop prototype, not a production-ready retail payment system. Payment gateway integration, invoice printing, role-specific password reset, tax configuration, audit logging, and automated backups can be added in a later iteration.
- The database file `smart_grocery.db` is created automatically on first run.
