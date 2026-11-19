import hashlib
import os
import shutil
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Please install dependencies first: pip install -r requirements.txt")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "smart_grocery.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Color Palette
GREEN = "#176B4D"
DARK_GREEN = "#104A36"
LIGHT_GREEN = "#EAF5EF"
BG = "#F1F8F4"
TEXT = "#172B22"
MUTED = "#6B7C73"
WHITE = "#FFFFFF"
RED = "#C0392B"
ORANGE = "#B9770E"
TEAL = "#0E7C7B"
BORDER = "#DFEAF3"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ==========================================
# Custom Data Structure: Singly Linked List
# ==========================================
class ProductNode:
    def __init__(self, product: dict):
        self.product = product
        self.next = None


class ProductLinkedList:
    def __init__(self):
        self.head = None

    def append(self, product: dict):
        new_node = ProductNode(product)
        if not self.head:
            self.head = new_node
            return
        curr = self.head
        while curr.next:
            curr = curr.next
        curr.next = new_node

    def to_list(self) -> list:
        items = []
        curr = self.head
        while curr:
            items.append(curr.product)
            curr = curr.next
        return items

    def search(self, query: str) -> list:
        q = query.strip().lower()
        if not q:
            return self.to_list()
        matches = []
        curr = self.head
        while curr:
            p = curr.product
            if q in str(p["name"]).lower() or q in str(p["category"]).lower() or q in str(p["supplier"]).lower():
                matches.append(p)
            curr = curr.next
        return matches


# ==========================================
# Database Layer (SQLite3)
# ==========================================
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'employee', 'customer')),
                    email TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    photo_path TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    cost_price REAL NOT NULL DEFAULT 0.0,
                    price REAL NOT NULL DEFAULT 0.0,
                    min_stock INTEGER NOT NULL DEFAULT 5,
                    supplier TEXT NOT NULL DEFAULT ''
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    customer_name TEXT NOT NULL,
                    cashier TEXT NOT NULL DEFAULT 'Online',
                    total REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES users(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    line_total REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)

            now = datetime.now().isoformat(timespec="seconds")

            # Seed default admin
            cur.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO users (full_name, username, password_hash, role, email, phone, address, created_at)
                    VALUES (?, ?, ?, 'admin', ?, ?, ?, ?)
                """, ("Store Administrator", "admin", hash_password("admin123"), "admin@smartgrocery.local", "03213928528", "Nawabshah", now))

            # Seed sample products if empty
            cur.execute("SELECT COUNT(*) AS cnt FROM products")
            if cur.fetchone()["cnt"] == 0:
                sample_products = [
                    ("Basmati Rice 5kg", "Grains", 34, 1450.0, 1690.0, 8, "Al-Madina Traders"),
                    ("Fresh Milk 1L", "Dairy", 42, 210.0, 245.0, 10, "Fresh Dairy"),
                    ("Sugar 1kg", "Grains", 60, 145.0, 170.0, 12, "City Wholesale"),
                    ("Cooking Oil 1L", "Cooking Essentials", 23, 520.0, 585.0, 8, "National Foods"),
                    ("Tea 190g", "Beverages", 18, 410.0, 465.0, 6, "Tea Distributors"),
                    ("Potato 1kg", "Fruits & Vegetables", 50, 90.0, 120.0, 10, "Fresh Market"),
                    ("Dishwashing Liquid", "Household", 4, 180.0, 230.0, 8, "HomeCare Supply"),
                    ("Orange Juice 1L", "Beverages", 16, 260.0, 310.0, 5, "Juice House"),
                ]
                cur.executemany("""
                    INSERT INTO products (name, category, stock, cost_price, price, min_stock, supplier)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, sample_products)

            conn.commit()

    def authenticate(self, username: str, password: str):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ?",
                (username.strip(), hash_password(password))
            ).fetchone()
            return dict(row) if row else None

    def register_user(self, full_name: str, username: str, password: str, role: str = "customer", email: str = "", phone: str = "", address: str = ""):
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO users (full_name, username, password_hash, role, email, phone, address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (full_name.strip(), username.strip(), hash_password(password), role, email.strip(), phone.strip(), address.strip(), now))
            conn.commit()

    def get_all_users(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()]

    def get_user_by_id(self, user_id: int):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def update_user_profile(self, user_id: int, full_name: str, email: str, phone: str, address: str, photo_path: str):
        with self.connect() as conn:
            conn.execute("""
                UPDATE users
                SET full_name = ?, email = ?, phone = ?, address = ?, photo_path = ?
                WHERE id = ?
            """, (full_name.strip(), email.strip(), phone.strip(), address.strip(), photo_path, user_id))
            conn.commit()

    def get_products_linked_list(self) -> ProductLinkedList:
        ll = ProductLinkedList()
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
            for r in rows:
                ll.append(dict(r))
        return ll

    def add_product(self, name: str, category: str, stock: int, cost_price: float, price: float, min_stock: int, supplier: str):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO products (name, category, stock, cost_price, price, min_stock, supplier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), category.strip(), stock, cost_price, price, min_stock, supplier.strip()))
            conn.commit()

    def update_product(self, product_id: int, name: str, category: str, stock: int, cost_price: float, price: float, min_stock: int, supplier: str):
        with self.connect() as conn:
            conn.execute("""
                UPDATE products
                SET name = ?, category = ?, stock = ?, cost_price = ?, price = ?, min_stock = ?, supplier = ?
                WHERE id = ?
            """, (name.strip(), category.strip(), stock, cost_price, price, min_stock, supplier.strip(), product_id))
            conn.commit()

    def delete_product(self, product_id: int):
        with self.connect() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    def create_order(self, customer: dict, cart_items: list):
        if not cart_items:
            raise ValueError("Cart is empty.")
        total = sum(item["quantity"] * item["price"] for item in cart_items)
        now = datetime.now().isoformat(timespec="seconds")

        with self.connect() as conn:
            cur = conn.cursor()
            # Verify stock first
            for item in cart_items:
                prod = cur.execute("SELECT stock, name FROM products WHERE id = ?", (item["id"],)).fetchone()
                if not prod or prod["stock"] < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {item['name']}.")

            cur.execute("""
                INSERT INTO orders (customer_id, customer_name, cashier, total, status, created_at)
                VALUES (?, ?, 'Online', ?, 'Pending', ?)
            """, (customer["id"], customer["full_name"], total, now))
            order_id = cur.lastrowid

            for item in cart_items:
                line_total = item["quantity"] * item["price"]
                cur.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item["id"], item["name"], item["quantity"], item["price"], line_total))

                cur.execute("""
                    UPDATE products SET stock = stock - ? WHERE id = ?
                """, (item["quantity"], item["id"]))

            conn.commit()
            return order_id

    def get_orders(self, customer_id: int = None):
        with self.connect() as conn:
            if customer_id is not None:
                rows = conn.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def mark_order_completed(self, order_id: int):
        with self.connect() as conn:
            conn.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
            conn.commit()

    def get_dashboard_stats(self):
        products = self.get_products_linked_list().to_list()
        users = self.get_all_users()
        orders = self.get_orders()

        total_products = len(products)
        customers_count = sum(1 for u in users if u["role"] == "customer")
        employees_count = sum(1 for u in users if u["role"] == "employee")
        total_revenue = sum(float(o["total"]) for o in orders)
        estimated_cost = sum(int(p["stock"]) * float(p["cost_price"]) for p in products)
        low_stock_items = [p for p in products if int(p["stock"]) <= int(p["min_stock"])]

        return {
            "total_products": total_products,
            "customers_count": customers_count,
            "employees_count": employees_count,
            "total_revenue": total_revenue,
            "estimated_cost": estimated_cost,
            "orders_count": len(orders),
            "low_stock_items": low_stock_items,
            "recent_orders": orders[:5],
            "products": products,
        }


# ==========================================
# Main Application Window
# ==========================================
class SmartGroceryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SMART GROCERY PRO")
        self.geometry("1280x760")
        self.minsize(1024, 650)
        self.configure(fg_color=BG)

        self.db = DatabaseManager(DB_PATH)
        self.current_user = None
        self.cart = []  # list of dicts: {id, name, price, quantity}

        self.container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.container.pack(fill="both", expand=True)

        self.show_login_screen()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # --------------------------------------
    # 1. Login & Registration Screen
    # --------------------------------------
    def show_login_screen(self):
        self.clear_container()
        self.current_user = None
        self.cart = []

        left_panel = ctk.CTkFrame(self.container, fg_color=DARK_GREEN, corner_radius=0, width=420)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        ctk.CTkLabel(
            left_panel,
            text="SMART\nGROCERY PRO",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=WHITE,
            justify="left"
        ).pack(anchor="w", padx=45, pady=(110, 18))

        ctk.CTkLabel(
            left_panel,
            text="A smarter way to manage\nyour everyday grocery business.",
            font=ctk.CTkFont(size=16),
            text_color="#D8EDE2",
            justify="left"
        ).pack(anchor="w", padx=45, pady=(0, 35))

        ctk.CTkLabel(
            left_panel,
            text="INVENTORY  •  SALES  •  CUSTOMERS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9CD6B8"
        ).pack(anchor="w", padx=45)

        right_panel = ctk.CTkFrame(self.container, fg_color=BG, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        card = ctk.CTkFrame(right_panel, fg_color=WHITE, corner_radius=16, width=430, height=440, border_width=1, border_color=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="Welcome back", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).pack(anchor="w", padx=35, pady=(35, 4))
        ctk.CTkLabel(card, text="Sign in to continue to your workspace", font=ctk.CTkFont(size=13), text_color=MUTED).pack(anchor="w", padx=35, pady=(0, 24))

        username_entry = ctk.CTkEntry(card, placeholder_text="Username", height=42, corner_radius=8)
        username_entry.pack(fill="x", padx=35, pady=(0, 14))

        password_entry = ctk.CTkEntry(card, placeholder_text="Password", show="*", height=42, corner_radius=8)
        password_entry.pack(fill="x", padx=35, pady=(0, 20))

        def handle_login(event=None):
            user = self.db.authenticate(username_entry.get(), password_entry.get())
            if not user:
                messagebox.showerror("Login Failed", "Invalid username or password.")
                return
            self.current_user = user
            if user["role"] in ("admin", "employee"):
                self.show_workspace("admin")
            else:
                self.show_workspace("customer")

        password_entry.bind("<Return>", handle_login)

        ctk.CTkButton(
            card,
            text="Sign In",
            height=42,
            corner_radius=8,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=handle_login
        ).pack(fill="x", padx=35, pady=(0, 12))

        ctk.CTkButton(
            card,
            text="Create customer account",
            height=40,
            corner_radius=8,
            fg_color=LIGHT_GREEN,
            hover_color="#D7ECE1",
            text_color=DARK_GREEN,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_register_modal
        ).pack(fill="x", padx=35)

        ctk.CTkLabel(
            card,
            text="Demo admin: admin  |  Password: admin123",
            font=ctk.CTkFont(size=11),
            text_color=MUTED
        ).pack(pady=(22, 0))

    def open_register_modal(self):
        win = ctk.CTkToplevel(self)
        win.title("Create Customer Account")
        win.geometry("420x430")
        win.grab_set()

        ctk.CTkLabel(win, text="Create Customer Account", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).pack(pady=(20, 12))

        name_e = ctk.CTkEntry(win, placeholder_text="Full Name", height=38)
        name_e.pack(fill="x", padx=30, pady=6)
        user_e = ctk.CTkEntry(win, placeholder_text="Username", height=38)
        user_e.pack(fill="x", padx=30, pady=6)
        pass_e = ctk.CTkEntry(win, placeholder_text="Password", show="*", height=38)
        pass_e.pack(fill="x", padx=30, pady=6)
        email_e = ctk.CTkEntry(win, placeholder_text="Email (optional)", height=38)
        email_e.pack(fill="x", padx=30, pady=6)
        phone_e = ctk.CTkEntry(win, placeholder_text="Phone (optional)", height=38)
        phone_e.pack(fill="x", padx=30, pady=6)

        def submit():
            if not name_e.get().strip() or not user_e.get().strip() or not pass_e.get().strip():
                messagebox.showwarning("Missing Fields", "Full name, username, and password are required.")
                return
            try:
                self.db.register_user(
                    name_e.get(), user_e.get(), pass_e.get(),
                    role="customer", email=email_e.get(), phone=phone_e.get()
                )
                messagebox.showinfo("Success", "Customer account created! You can sign in now.")
                win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")

        ctk.CTkButton(win, text="Register Account", fg_color=GREEN, hover_color=DARK_GREEN, height=40, command=submit).pack(fill="x", padx=30, pady=16)

    # --------------------------------------
    # Shared Workspace Shell (Sidebar + Content)
    # --------------------------------------
    def show_workspace(self, mode: str):
        self.clear_container()

        sidebar = ctk.CTkFrame(self.container, fg_color=DARK_GREEN, corner_radius=0, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="SMART\nGROCERY PRO",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=WHITE,
            justify="left"
        ).pack(anchor="w", padx=22, pady=(26, 4))

        role_subtitle = "ADMIN WORKSPACE" if mode == "admin" else "CUSTOMER PORTAL"
        ctk.CTkLabel(
            sidebar,
            text=role_subtitle,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#9CD6B8"
        ).pack(anchor="w", padx=22, pady=(0, 22))

        content_area = ctk.CTkFrame(self.container, fg_color=BG, corner_radius=0)
        content_area.pack(side="right", fill="both", expand=True)

        nav_buttons = {}

        def switch_tab(tab_key: str, render_fn):
            for key, btn in nav_buttons.items():
                btn.configure(fg_color=GREEN if key == tab_key else "transparent")
            for w in content_area.winfo_children():
                w.destroy()
            render_fn(content_area)

        if mode == "admin":
            tabs = [
                ("dashboard", "Dashboard", self.render_admin_dashboard),
                ("products", "Products", self.render_admin_products),
                ("users", "Customers & Staff", self.render_admin_users),
                ("orders", "Orders", self.render_admin_orders),
                ("reports", "Reports", self.render_admin_reports),
                ("profile", "My Profile", self.render_profile_view),
            ]
            default_tab = ("dashboard", self.render_admin_dashboard)
        else:
            tabs = [
                ("home", "Home", lambda parent: self.render_customer_shop(parent, title="Discover Groceries", subtitle="Fresh essentials, everyday value — shop by product")),
                ("shop", "Shop Products", lambda parent: self.render_customer_shop(parent, title="Shop Products", subtitle="Browse all available grocery items")),
                ("cart", "My Cart", self.render_customer_cart),
                ("orders", "My Orders", self.render_customer_orders),
                ("profile", "My Profile", self.render_profile_view),
            ]
            default_tab = ("home", lambda parent: self.render_customer_shop(parent, title="Discover Groceries", subtitle="Fresh essentials, everyday value — shop by product"))

        for key, label, fn in tabs:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                hover_color=GREEN,
                text_color=WHITE,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda k=key, f=fn: switch_tab(k, f)
            )
            btn.pack(fill="x", padx=14, pady=3)
            nav_buttons[key] = btn

        # Bottom user info & Logout button
        bottom_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=16, pady=18)

        ctk.CTkLabel(
            bottom_box,
            text=self.current_user["full_name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            bottom_box,
            text=self.current_user["role"].capitalize(),
            font=ctk.CTkFont(size=11),
            text_color="#B7DEC9",
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            bottom_box,
            text="Logout",
            height=36,
            corner_radius=8,
            fg_color="#E85A5A",
            hover_color="#C94444",
            text_color=WHITE,
            font=ctk.CTkFont(size=13, weight="bold"),