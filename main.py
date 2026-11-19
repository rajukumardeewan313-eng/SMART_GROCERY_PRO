import os
import sqlite3
import hashlib
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Please install dependencies first: pip install -r requirements.txt")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "smart_grocery.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

GREEN = "#176B4D"
DARK_GREEN = "#104A36"
LIGHT_GREEN = "#EAF5EF"
BG = "#F1F8F4"
TEXT = "#172B22"
MUTED = "#6B7C73"
WHITE = "#FFFFFF"
RED = "#C0392B"
ORANGE = "#B9770E"
BORDER = "#DFEAE3"

# Accent colors for stat cards
ACCENT_GREEN = "#15803D"
ACCENT_TEAL = "#0D9488"
ACCENT_AMBER = "#D97706"
ACCENT_CORAL = "#E05656"

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def is_valid_phone_number(phone):
    return len(phone) == 11 and all("0" <= digit <= "9" for digit in phone)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            role TEXT NOT NULL CHECK(role IN ('admin','employee','customer')),
            photo TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            barcode TEXT DEFAULT '',
            purchase_price REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER NOT NULL DEFAULT 5,
            expiry_date TEXT DEFAULT '',
            supplier TEXT DEFAULT '',
            photo TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            employee_id INTEGER,
            order_type TEXT NOT NULL DEFAULT 'customer',
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Completed',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES users(id),
            FOREIGN KEY(employee_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)
        self.conn.commit()

    def seed_data(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        if cur.fetchone()[0] == 0:
            cur.execute("""INSERT INTO users(username,password,full_name,email,role,created_at)
                           VALUES(?,?,?,?,?,?)""",
                        ("admin", hash_password("admin123"), "Store Administrator",
                         "admin@smartgrocery.local", "admin", datetime.now().isoformat(timespec="minutes")))
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            samples = [
                ("Basmati Rice 5kg","Grains","890100100001",1450,1690,35,8,"","Al-Madina Traders"),
                ("Fresh Milk 1L","Dairy","890100100002",210,245,42,10,"","Fresh Dairy"),
                ("Sugar 1kg","Grains","890100100003",145,170,60,12,"","City Wholesale"),
                ("Cooking Oil 1L","Cooking Essentials","890100100004",520,585,24,8,"","National Foods"),
                ("Tea 190g","Beverages","890100100005",410,465,18,6,"","Tea Distributors"),
                ("Potato 1kg","Fruits & Vegetables","890100100006",90,120,50,10,"","Fresh Market"),
                ("Dishwashing Liquid","Household","890100100007",180,230,4,8,"","HomeCare Supply"),
                ("Orange Juice 1L","Beverages","890100100008",260,310,16,5,"","Juice House"),
            ]
            cur.executemany("""INSERT INTO products(name,category,barcode,purchase_price,selling_price,
                            quantity,min_stock,expiry_date,supplier) VALUES(?,?,?,?,?,?,?,?,?)""", samples)
        self.conn.commit()

    def query(self, sql, params=()):
        return self.conn.execute(sql, params)

    def execute(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def close(self):
        self.conn.close()

# Explicit singly linked list implementation for the DSA requirement.
class ProductNode:
    def __init__(self, data):
        self.data = dict(data)
        self.next = None

class ProductLinkedList:
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, data):
        node = ProductNode(data)
        if self.head is None:
            self.head = node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = node
        self.size += 1

    def to_list(self):
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result

    def find(self, product_id):
        current = self.head
        while current is not None:
            if current.data["id"] == product_id:
                return current.data
            current = current.next
        return None

class SmartGroceryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SMART GROCERY PRO")
        self.geometry("1280x800")
        self.minsize(1080, 680)
        self.configure(fg_color=BG)
        self.db = Database()
        self.current_user = None
        self.cart = {}
        self.active_page = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_login()

    def on_close(self):
        self.db.close()
        self.destroy()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def card(self, parent, **kwargs):
        border = kwargs.pop("border_color", BORDER)
        return ctk.CTkFrame(parent, fg_color=WHITE, corner_radius=14, border_width=1,
                            border_color=border, **kwargs)

    def title_label(self, parent, text, size=24):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=size, weight="bold"),
                            text_color=TEXT)

    def show_login(self):
        self.current_user = None
        self.cart = {}
        self.clear()
        shell = ctk.CTkFrame(self, fg_color=BG)
        shell.pack(fill="both", expand=True)
        left = ctk.CTkFrame(shell, fg_color=DARK_GREEN, corner_radius=0, width=470)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)
        ctk.CTkLabel(left, text="SMART\nGROCERY PRO", text_color=WHITE,
                     font=ctk.CTkFont(size=38, weight="bold"), justify="left").pack(anchor="w", padx=52, pady=(150, 18))
        ctk.CTkLabel(left, text="A smarter way to manage\nyour everyday grocery business.",
                     text_color="#D7E9DF", font=ctk.CTkFont(size=17), justify="left").pack(anchor="w", padx=54)
        ctk.CTkLabel(left, text="INVENTORY  •  SALES  •  CUSTOMERS",
                     text_color="#B7D5C5", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=54, pady=(35,0))

        right = ctk.CTkFrame(shell, fg_color=BG)
        right.pack(side="left", fill="both", expand=True)
        form = self.card(right, width=440)
        form.place(relx=.5, rely=.5, anchor="center")
        ctk.CTkLabel(form, text="Welcome back", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=34, pady=(34,4))
        ctk.CTkLabel(form, text="Sign in to continue to your workspace",
                     text_color=MUTED, font=ctk.CTkFont(size=13)).pack(anchor="w", padx=34, pady=(0,24))
        self.login_user = ctk.CTkEntry(form, width=360, height=44, placeholder_text="Username")
        self.login_user.pack(padx=34, pady=7)
        self.login_pass = ctk.CTkEntry(form, width=360, height=44, placeholder_text="Password", show="•")
        self.login_pass.pack(padx=34, pady=7)
        ctk.CTkButton(form, text="Sign In", width=360, height=44, fg_color=GREEN,
                      hover_color=DARK_GREEN, command=self.login).pack(padx=34, pady=(18,10))
        ctk.CTkButton(form, text="Create customer account", width=360, height=40,
                      fg_color=LIGHT_GREEN, text_color=GREEN, hover_color="#DCEFE4",
                      command=self.show_register).pack(padx=34, pady=(0,28))
        ctk.CTkLabel(form, text="Demo admin: admin  |  Password: admin123",
                     text_color=MUTED, font=ctk.CTkFont(size=11)).pack(padx=20, pady=(0,18))

    def login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get()
        row = self.db.query("SELECT * FROM users WHERE username=? AND password=?",
                            (username, hash_password(password))).fetchone()
        if not row:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        self.current_user = dict(row)
        self.cart = {}
        self.show_workspace()

    def show_register(self):
        self.clear()
        outer = ctk.CTkFrame(self, fg_color=BG)
        outer.pack(fill="both", expand=True)
        form = self.card(outer, width=520)
        form.place(relx=.5, rely=.5, anchor="center")
        self.title_label(form, "Create customer account", 25).pack(anchor="w", padx=32, pady=(28,5))
        ctk.CTkLabel(form, text="Register to browse products and place orders.",
                     text_color=MUTED).pack(anchor="w", padx=32, pady=(0,16))
        self.reg_entries = {}
        fields = [("Full name","full_name"),("Username","username"),("Email","email"),
                  ("Phone","phone"),("Address","address"),("Password","password")]
        for label, key in fields:
            ctk.CTkLabel(form, text=label, text_color=TEXT).pack(anchor="w", padx=32, pady=(5,0))
            entry = ctk.CTkEntry(form, width=450, height=38, show="•" if key=="password" else "")
            entry.pack(padx=32, pady=(3,3))
            self.reg_entries[key] = entry
        self.reg_photo = ""
        ctk.CTkButton(form, text="Upload profile photo (optional)", fg_color=LIGHT_GREEN,
                      text_color=GREEN, hover_color="#DCEFE4", command=self.pick_register_photo).pack(padx=32, pady=8, anchor="w")
        ctk.CTkButton(form, text="Create account", width=450, height=42, fg_color=GREEN,
                      command=self.register_customer).pack(padx=32, pady=(8,6))
        ctk.CTkButton(form, text="Back to login", fg_color="transparent", text_color=GREEN,
                      command=self.show_login).pack(pady=(0,18))

    def pick_register_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.webp")])
        if path:
            self.reg_photo = self.copy_upload(path, "customer")

    def register_customer(self):
        vals = {k:v.get().strip() for k,v in self.reg_entries.items()}
        if not vals["full_name"] or not vals["username"] or not vals["password"]:
            messagebox.showwarning("Missing details", "Full name, username and password are required.")
            return
        if not is_valid_phone_number(vals["phone"]):
            messagebox.showwarning("Invalid phone number", "Phone number must be 11 digits.")
            return
        try:
            self.db.execute("""INSERT INTO users(username,password,full_name,email,phone,address,role,photo,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (vals["username"],hash_password(vals["password"]),vals["full_name"],vals["email"],
                 vals["phone"],vals["address"],"customer",self.reg_photo,datetime.now().isoformat(timespec="minutes")))
        except sqlite3.IntegrityError:
            messagebox.showerror("Registration failed", "That username is already in use.")
            return
        messagebox.showinfo("Account created", "Your customer account has been created. Please sign in.")
        self.show_login()

    def copy_upload(self, path, prefix):
        ext = os.path.splitext(path)[1].lower() or ".img"
        name = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
        dest = os.path.join(UPLOAD_DIR, name)
        shutil.copy2(path, dest)
        return os.path.relpath(dest, APP_DIR)

    def show_workspace(self):
        self.clear()
        self.sidebar = ctk.CTkFrame(self, fg_color=DARK_GREEN, width=245, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        role = self.current_user["role"]

        # 1. Pinned bottom container (User info + Logout button)
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=14, pady=(0, 16))

        # Thin divider line
        ctk.CTkFrame(bottom_box, fg_color="#185E45", height=1).pack(fill="x", pady=(0, 12))

        # User full name and role labels
        ctk.CTkLabel(bottom_box, text=self.current_user["full_name"], text_color=WHITE,
                     font=ctk.CTkFont(size=13, weight="bold"), wraplength=205, anchor="w", justify="left").pack(fill="x", padx=4, pady=(0, 2))
        ctk.CTkLabel(bottom_box, text=role.capitalize(), text_color="#B8D6C7",
                     font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=4, pady=(0, 10))

        # Logout button styled in soft red / coral
        logout_btn = ctk.CTkButton(
            bottom_box,
            text="Logout",
            height=38,
            corner_radius=8,
            fg_color="#E05656",
            hover_color="#C94141",
            text_color=WHITE,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.confirm_logout
        )
        logout_btn.pack(fill="x", padx=4, pady=(0, 2))

        # 2. Header (App title & workspace badge)
        header_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_box.pack(side="top", fill="x", padx=18, pady=(22, 14))
        ctk.CTkLabel(header_box, text="SMART\nGROCERY PRO", text_color=WHITE,
                     font=ctk.CTkFont(size=23, weight="bold"), justify="left").pack(anchor="w")
        role_title = {"admin":"ADMIN WORKSPACE","employee":"EMPLOYEE WORKSPACE","customer":"CUSTOMER PORTAL"}[role]
        ctk.CTkLabel(header_box, text=role_title, text_color="#B8D6C7",
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(6, 0))

        # 3. Scrollable menu area
        menu_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color="#185E45",
            scrollbar_button_hover_color="#217A5A"
        )
        menu_frame.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))

        menu = {
            "admin":[("Dashboard","dashboard"),("Products","products"),("Customers & Staff","users"),("Orders","orders"),("Reports","reports"),("My Profile","profile")],
            "employee":[("Dashboard","dashboard"),("Point of Sale","pos"),("Products / Stock","products"),("Orders","orders"),("My Profile","profile")],
            "customer":[("Home","shop"),("Shop Products","shop"),("My Cart","cart"),("My Orders","myorders"),("My Profile","profile")]
        }[role]

        self.sidebar_buttons = []
        for label, page in menu:
            btn = ctk.CTkButton(
                menu_frame,
                text="  " + label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#185B43",
                text_color="#CFE3D7",
                font=ctk.CTkFont(size=13)
            )
            btn.configure(command=lambda p=page, b=btn: self.show_page(p, target_btn=b))
            btn.pack(fill="x", padx=6, pady=3)
            self.sidebar_buttons.append((page, btn))

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)
        self.show_page(menu[0][1])

    def confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            self.logout()

    def logout(self):
        self.current_user = None
        self.cart = {}
        self.active_page = None
        self.show_login()

    def page_header(self, title, subtitle="Manage your grocery store in one place"):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24,16))
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=27, weight="bold"),
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(top, text=subtitle, font=ctk.CTkFont(size=13),
                     text_color=MUTED).pack(anchor="w", pady=(4,0))

    def show_page(self, page, target_btn=None):
        self.active_page = page

        # Update active sidebar highlight
        if hasattr(self, "sidebar_buttons"):
            found = False
            if target_btn:
                for p, btn in self.sidebar_buttons:
                    if btn == target_btn:
                        btn.configure(fg_color="#1D7554", hover_color="#22835E",
                                      text_color=WHITE, font=ctk.CTkFont(size=13, weight="bold"))
                        found = True
                    else:
                        btn.configure(fg_color="transparent", hover_color="#185B43",
                                      text_color="#CFE3D7", font=ctk.CTkFont(size=13, weight="normal"))
            if not found:
                matched = False
                for p, btn in self.sidebar_buttons:
                    if p == page and not matched:
                        btn.configure(fg_color="#1D7554", hover_color="#22835E",
                                      text_color=WHITE, font=ctk.CTkFont(size=13, weight="bold"))
                        matched = True
                    else:
                        btn.configure(fg_color="transparent", hover_color="#185B43",
                                      text_color="#CFE3D7", font=ctk.CTkFont(size=13, weight="normal"))

        for w in self.main.winfo_children():
            w.destroy()
        if page == "dashboard": self.page_dashboard()
        elif page == "products": self.page_products()
        elif page == "users": self.page_users()
        elif page == "orders": self.page_orders()
        elif page == "reports": self.page_reports()
        elif page == "profile": self.page_profile()
        elif page == "shop": self.page_shop()
        elif page == "cart": self.page_cart()
        elif page == "myorders": self.page_myorders()
        elif page == "pos": self.page_pos()

    def stat_card(self, parent, label, value, note="", accent_color=None):
        accent = accent_color or GREEN
        frame = self.card(parent)
        accent_bar = ctk.CTkFrame(frame, fg_color=accent, height=4, corner_radius=2)
        accent_bar.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(frame, text=label, text_color=MUTED,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(4, 2))
        ctk.CTkLabel(frame, text=str(value), text_color=accent,
                     font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", padx=18, pady=(2, 2))
        if note:
            ctk.CTkLabel(frame, text=note, text_color="#52685C",
                         font=ctk.CTkFont(size=11)).pack(anchor="w", padx=18, pady=(2, 14))
        else:
            ctk.CTkFrame(frame, fg_color="transparent", height=14).pack()
        return frame

    def page_dashboard(self):
        role = self.current_user["role"]
        if role == "customer":
            self.page_shop()
            return
        self.page_header("Dashboard Overview", f"Welcome back, {self.current_user['full_name']}")
        content = ctk.CTkFrame(self.main, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=(0,25))
        if role == "admin":
            products = self.db.query("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]
            customers = self.db.query("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0]
            employees = self.db.query("SELECT COUNT(*) FROM users WHERE role='employee'").fetchone()[0]
            revenue = self.db.query("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0]
            stats = [("Total Products", products, "Active products", ACCENT_GREEN),
                     ("Customers", customers, "Registered accounts", ACCENT_TEAL),
                     ("Employees", employees, "Staff members", ACCENT_AMBER),
                     ("Total Revenue", f"Rs. {revenue:,.0f}", "All recorded orders", ACCENT_CORAL)]
        else:
            products = self.db.query("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]
            today = datetime.now().strftime("%Y-%m-%d")
            sales = self.db.query("SELECT COALESCE(SUM(total),0) FROM orders WHERE date(created_at)=?",(today,)).fetchone()[0]
            low = self.db.query("SELECT COUNT(*) FROM products WHERE active=1 AND quantity<=min_stock").fetchone()[0]
            stats = [("Products Available", products, "In active inventory", ACCENT_GREEN),
                     ("Today's Sales", f"Rs. {sales:,.0f}", "Recorded today", ACCENT_TEAL),
                     ("Low Stock", low, "Needs attention", ACCENT_CORAL),
                     ("Your Role", "Employee", "Store operations", ACCENT_AMBER)]
        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 18))
        for i, (label, value, note, color) in enumerate(stats):
            self.stat_card(stats_row, label, value, note, color).grid(row=0, column=i, sticky="nsew", padx=6, pady=5)
            stats_row.grid_columnconfigure(i, weight=1)
        lower = ctk.CTkFrame(content, fg_color="transparent")
        lower.pack(fill="both", expand=True)
        left = self.card(lower)
        left.pack(side="left", fill="both", expand=True, padx=(0,8))
        ctk.CTkFrame(left, fg_color=ACCENT_CORAL, height=3, corner_radius=2).pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(left, text="Low Stock Alerts", font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(8, 12))
        rows = self.db.query("SELECT name,quantity,min_stock FROM products WHERE active=1 AND quantity<=min_stock ORDER BY quantity").fetchall()
        if not rows:
            ctk.CTkLabel(left, text="All products are above minimum stock.", text_color=GREEN).pack(anchor="w", padx=18, pady=10)
        for r in rows[:8]:
            ctk.CTkLabel(left, text=f"• {r['name']}  —  {r['quantity']} left (minimum {r['min_stock']})",
                         text_color=ORANGE, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=5)
        right = self.card(lower)
        right.pack(side="left", fill="both", expand=True, padx=(8,0))
        ctk.CTkFrame(right, fg_color=ACCENT_TEAL, height=3, corner_radius=2).pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(right, text="Recent Orders", font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT).pack(anchor="w", padx=18, pady=(8, 12))
        orders = self.db.query("""SELECT o.id,o.total,o.status,o.created_at,u.full_name
            FROM orders o LEFT JOIN users u ON u.id=o.customer_id ORDER BY o.id DESC LIMIT 7""").fetchall()
        for r in orders:
            ctk.CTkLabel(right, text=f"Order #{r['id']}  |  {r['full_name'] or 'Walk-in'}  |  Rs. {r['total']:,.0f}",
                         text_color=TEXT, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=5)

    def make_tree(self, parent, columns, headings, height=14):
        wrap = ctk.CTkFrame(parent, fg_color=WHITE, corner_radius=10, border_width=1, border_color=BORDER)
        wrap.pack(fill="both", expand=True, padx=2, pady=5)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", height=height)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground=TEXT, rowheight=30, fieldbackground="white", font=("Segoe UI",10))
        style.configure("Treeview.Heading", background="#EAF5EF", foreground=DARK_GREEN, font=("Segoe UI",10,"bold"))
        style.map("Treeview", background=[("selected","#CFE8D9")], foreground=[("selected",TEXT)])
        for col, heading in zip(columns, headings):
            tree.heading(col,text=heading)
            tree.column(col,width=120,anchor="w")
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vs.set)
        tree.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        vs.pack(side="right",fill="y",pady=8)
        return tree

    def page_products(self):
        role = self.current_user["role"]
        self.page_header("Product Inventory", "Manage product details, pricing and stock levels")
        bar = ctk.CTkFrame(self.main, fg_color="transparent")
        bar.pack(fill="x", padx=28)
        search = ctk.CTkEntry(bar, width=270, placeholder_text="Search product name or category")
        search.pack(side="left", pady=5)
        tree = self.make_tree(self.main,("id","name","category","qty","cost","price","min","supplier"),
                              ("ID","Product","Category","Stock","Cost (Rs.)","Price (Rs.)","Min. Stock","Supplier"))
        def refresh(*_):
            for x in tree.get_children(): tree.delete(x)
            ll = ProductLinkedList()
            term = search.get().strip().lower()
            for row in self.db.query("SELECT * FROM products WHERE active=1 ORDER BY id"):
                ll.append(row)
            for p in ll.to_list():
                if term and term not in p["name"].lower() and term not in p["category"].lower():
                    continue
                tree.insert("", "end", values=(p["id"],p["name"],p["category"],p["quantity"],
                    f"{p['purchase_price']:.2f}",f"{p['selling_price']:.2f}",p["min_stock"],p["supplier"]))
        search.bind("<KeyRelease>",refresh)
        refresh()
        if role == "admin":
            actions = ctk.CTkFrame(self.main, fg_color="transparent")
            actions.pack(fill="x", padx=28, pady=10)
            ctk.CTkButton(actions,text="＋ Add Product",fg_color=GREEN,command=lambda:self.product_dialog(refresh)).pack(side="left",padx=(0,8))
            ctk.CTkButton(actions,text="Edit Selected",fg_color="#DDEFE4",text_color=GREEN,
                          command=lambda:self.edit_selected_product(tree,refresh)).pack(side="left",padx=5)
            ctk.CTkButton(actions,text="Delete Selected",fg_color="#FCE9E7",text_color=RED,
                          command=lambda:self.delete_selected_product(tree,refresh)).pack(side="left",padx=5)
        ctk.CTkLabel(self.main,text="Product records are loaded into the custom singly linked list for traversal.",
                     text_color=MUTED,font=ctk.CTkFont(size=11)).pack(anchor="w",padx=30,pady=(0,12))

    def product_dialog(self, refresh, product=None):
        win = ctk.CTkToplevel(self)
        win.title("Product details")
        win.geometry("460x650")
        win.transient(self)
        win.grab_set()
        fields = [("Product name","name"),("Category","category"),("Barcode","barcode"),
                  ("Purchase price","purchase_price"),("Selling price","selling_price"),
                  ("Quantity","quantity"),("Minimum stock","min_stock"),("Expiry date (YYYY-MM-DD)","expiry_date"),
                  ("Supplier","supplier")]
        entries = {}
        ctk.CTkLabel(win,text="Product Details",font=ctk.CTkFont(size=23,weight="bold"),text_color=TEXT).pack(anchor="w",padx=25,pady=(20,10))
        for label,key in fields:
            ctk.CTkLabel(win,text=label,text_color=MUTED).pack(anchor="w",padx=25,pady=(5,0))
            e=ctk.CTkEntry(win,width=400,height=34)
            e.pack(padx=25,pady=(2,2))
            entries[key]=e
            if product: e.insert(0,str(product[key] or ""))
        photo_path = product["photo"] if product else ""
        def save():
            try:
                name=entries["name"].get().strip()
                category=entries["category"].get().strip()
                if not name or not category: raise ValueError()
                vals=(name,category,entries["barcode"].get().strip(),
                      float(entries["purchase_price"].get() or 0),float(entries["selling_price"].get() or 0),
                      int(entries["quantity"].get() or 0),int(entries["min_stock"].get() or 0),
                      entries["expiry_date"].get().strip(),entries["supplier"].get().strip(),photo_path)
                if vals[3]<0 or vals[4]<0 or vals[5]<0 or vals[6]<0: raise ValueError()
                if product:
                    self.db.execute("""UPDATE products SET name=?,category=?,barcode=?,purchase_price=?,selling_price=?,
                        quantity=?,min_stock=?,expiry_date=?,supplier=?,photo=? WHERE id=?""",vals+(product["id"],))
                else:
                    self.db.execute("""INSERT INTO products(name,category,barcode,purchase_price,selling_price,quantity,min_stock,expiry_date,supplier,photo)
                        VALUES(?,?,?,?,?,?,?,?,?,?)""",vals)
                win.destroy(); refresh()
            except ValueError:
                messagebox.showerror("Invalid details","Enter a product name/category and valid non-negative numeric values.")
        ctk.CTkButton(win,text="Save Product",fg_color=GREEN,width=400,command=save).pack(pady=18)
    def selected_id(self, tree):
        selected=tree.selection()
        if not selected:
            messagebox.showwarning("Select a row","Please select a product first.")
            return None
        return int(tree.item(selected[0],"values")[0])
    def edit_selected_product(self, tree, refresh):
        pid=self.selected_id(tree)
        if pid is None:return
        p=self.db.query("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
        self.product_dialog(refresh,dict(p))
    def delete_selected_product(self, tree, refresh):
        pid=self.selected_id(tree)
        if pid is None:return
        if messagebox.askyesno("Confirm delete","Remove this product from the active inventory?"):
            self.db.execute("UPDATE products SET active=0 WHERE id=?",(pid,))
            refresh()

    def page_users(self):
        self.page_header("Customers & Staff", "Admin-only account management")
        tree=self.make_tree(self.main,("id","name","username","role","email","phone","created"),
                            ("ID","Full Name","Username","Role","Email","Phone","Registered"))
        def refresh():
            for x in tree.get_children():tree.delete(x)
            for u in self.db.query("SELECT * FROM users WHERE role IN ('customer','employee') ORDER BY id DESC"):
                tree.insert("","end",values=(u["id"],u["full_name"],u["username"],u["role"],u["email"],u["phone"],u["created_at"]))
        refresh()
        bar=ctk.CTkFrame(self.main,fg_color="transparent");bar.pack(fill="x",padx=28,pady=10)
        ctk.CTkButton(bar,text="＋ Add Employee",fg_color=GREEN,command=self.employee_dialog).pack(side="left")
        ctk.CTkButton(bar,text="Refresh",fg_color="#DDEFE4",text_color=GREEN,command=refresh).pack(side="left",padx=8)
        ctk.CTkLabel(self.main,text="Customer accounts are created from the sign-in screen. Admin can create employee accounts here.",
                     text_color=MUTED).pack(anchor="w",padx=30,pady=5)

    def employee_dialog(self):
        win=ctk.CTkToplevel(self);win.title("Add employee");win.geometry("430x520");win.transient(self);win.grab_set()
        fields=["Full name","Username","Password","Email","Phone"]
        entries={}
        ctk.CTkLabel(win,text="Create Employee Account",font=ctk.CTkFont(size=22,weight="bold"),text_color=TEXT).pack(padx=25,pady=20)
        for f in fields:
            ctk.CTkLabel(win,text=f,text_color=MUTED).pack(anchor="w",padx=25)
            e=ctk.CTkEntry(win,width=370,show="•" if f=="Password" else "")
            e.pack(padx=25,pady=(2,8));entries[f]=e
        def save():
            vals=[entries[x].get().strip() for x in fields]
            if not vals[0] or not vals[1] or not vals[2]:
                messagebox.showwarning("Missing data","Name, username and password are required.");return
            if not is_valid_phone_number(vals[4]):
                messagebox.showwarning("Invalid phone number","Phone number must be 11 digits.");return
            try:
                self.db.execute("INSERT INTO users(username,password,full_name,email,phone,role,created_at) VALUES(?,?,?,?,?,'employee',?)",
                    (vals[1],hash_password(vals[2]),vals[0],vals[3],vals[4],datetime.now().isoformat(timespec="minutes")))
                win.destroy();self.show_page("users")
            except sqlite3.IntegrityError:
                messagebox.showerror("Username exists","Choose a different username.")
        ctk.CTkButton(win,text="Create Employee",fg_color=GREEN,command=save).pack(pady=15)

    def page_orders(self):
        role=self.current_user["role"]
        self.page_header("Orders", "Review order records and fulfilment status")
        tree=self.make_tree(self.main,("id","customer","employee","total","status","date"),
                            ("Order ID","Customer","Employee / Cashier","Total (Rs.)","Status","Date"))
        sql="""SELECT o.*,c.full_name customer,e.full_name employee FROM orders o
               LEFT JOIN users c ON c.id=o.customer_id LEFT JOIN users e ON e.id=o.employee_id"""
        params=()
        if role=="employee":
            sql+=" WHERE o.employee_id=?";params=(self.current_user["id"],)
        sql+=" ORDER BY o.id DESC"
        for o in self.db.query(sql,params):
            tree.insert("","end",values=(o["id"],o["customer"] or "Walk-in",o["employee"] or "Online",
                f"{o['total']:.2f}",o["status"],o["created_at"]))
        if role=="admin":
            bar=ctk.CTkFrame(self.main,fg_color="transparent");bar.pack(fill="x",padx=28,pady=10)
            ctk.CTkButton(bar,text="Mark selected as completed",fg_color=GREEN,
                command=lambda:self.set_order_status(tree)).pack(side="left")

    def set_order_status(self,tree):
        sel=tree.selection()
        if not sel:messagebox.showwarning("Select order","Select an order.");return
        oid=int(tree.item(sel[0],"values")[0])
        self.db.execute("UPDATE orders SET status='Completed' WHERE id=?",(oid,))
        self.show_page("orders")

    def page_reports(self):
        self.page_header("Reports & Analytics", "High-level sales and inventory summary")
        total=self.db.query("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0]
        count=self.db.query("SELECT COUNT(*) FROM orders").fetchone()[0]
        cost=self.db.query("SELECT COALESCE(SUM(oi.quantity*p.purchase_price),0) FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id").fetchone()[0]
        cards=ctk.CTkFrame(self.main,fg_color="transparent");cards.pack(fill="x",padx=25)
        for i,(a,b,c,col) in enumerate([("Gross Sales",f"Rs. {total:,.2f}","Recorded order value", ACCENT_GREEN),
                                        ("Orders",count,"All transactions", ACCENT_TEAL),
                                        ("Estimated Cost",f"Rs. {cost:,.2f}","Based on current purchase prices", ACCENT_AMBER)]):
            self.stat_card(cards,a,b,c,col).grid(row=0,column=i,sticky="nsew",padx=6)
            cards.grid_columnconfigure(i,weight=1)
        panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=30,pady=20)
        ctk.CTkLabel(panel,text="Inventory Summary",font=ctk.CTkFont(size=18,weight="bold"),text_color=TEXT).pack(anchor="w",padx=18,pady=16)
        for p in self.db.query("SELECT name,quantity,min_stock,selling_price FROM products WHERE active=1 ORDER BY name"):
            state="LOW STOCK" if p["quantity"]<=p["min_stock"] else "In stock"
            ctk.CTkLabel(panel,text=f"{p['name']}   |   Qty: {p['quantity']}   |   Price: Rs. {p['selling_price']:.2f}   |   {state}",
                         text_color=RED if state=="LOW STOCK" else TEXT).pack(anchor="w",padx=22,pady=4)

    def page_profile(self):
        self.page_header("My Profile", "Update your personal details and profile picture")
        u=self.db.query("SELECT * FROM users WHERE id=?",(self.current_user["id"],)).fetchone()
        panel=self.card(self.main);panel.pack(anchor="nw",padx=30,pady=5,fill="x")
        ctk.CTkLabel(panel,text=f"Account role: {u['role'].capitalize()}",text_color=GREEN,
                     font=ctk.CTkFont(size=13,weight="bold")).pack(anchor="w",padx=25,pady=(20,5))
        fields=[("Full name","full_name"),("Email","email"),("Phone","phone"),("Address","address")]
        entries={}
        for label,key in fields:
            ctk.CTkLabel(panel,text=label,text_color=MUTED).pack(anchor="w",padx=25,pady=(8,0))
            e=ctk.CTkEntry(panel,width=500,height=38);e.pack(anchor="w",padx=25,pady=(2,2))
            e.insert(0,u[key] or "");entries[key]=e
        photo_label=ctk.CTkLabel(panel,text=("Profile photo saved" if u["photo"] else "No profile photo selected"),
                                 text_color=MUTED)
        photo_label.pack(anchor="w",padx=25,pady=8)
        photo={"path":u["photo"] or ""}
        def pick():
            path=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.webp")])
            if path:
                photo["path"]=self.copy_upload(path,u["role"])
                photo_label.configure(text="New profile photo selected: "+os.path.basename(photo["path"]))
        def save():
            vals=[entries[k].get().strip() for _,k in fields]
            if not vals[0]:
                messagebox.showwarning("Required","Full name is required.");return
            if not is_valid_phone_number(vals[2]):
                messagebox.showwarning("Invalid phone number","Phone number must be 11 digits.");return
            self.db.execute("UPDATE users SET full_name=?,email=?,phone=?,address=?,photo=? WHERE id=?",
                            (*vals,photo["path"],u["id"]))
            self.current_user=dict(self.db.query("SELECT * FROM users WHERE id=?",(u["id"],)).fetchone())
            messagebox.showinfo("Saved","Profile updated successfully.")
            self.show_workspace()
        ctk.CTkButton(panel,text="Upload / Change Photo",fg_color=LIGHT_GREEN,text_color=GREEN,
                      command=pick).pack(anchor="w",padx=25,pady=8)
        ctk.CTkButton(panel,text="Save Profile",fg_color=GREEN,command=save).pack(anchor="w",padx=25,pady=(5,22))

    def product_rows(self, search=""):
        ll=ProductLinkedList()
        for r in self.db.query("SELECT * FROM products WHERE active=1 AND quantity>0 ORDER BY name"):
            ll.append(r)
        items=ll.to_list()
        if search:
            s=search.lower()
            items=[p for p in items if s in p["name"].lower() or s in p["category"].lower()]
        return items

    def page_shop(self):
        self.page_header("Discover Groceries", "Fresh essentials, everyday value — shop by product")
        bar=ctk.CTkFrame(self.main,fg_color="transparent");bar.pack(fill="x",padx=28)
        search=ctk.CTkEntry(bar,width=330,height=40,placeholder_text="Search products or categories...")
        search.pack(side="left",pady=5)
        ctk.CTkButton(bar,text="View Cart",fg_color=GREEN,command=lambda:self.show_page("cart")).pack(side="right")
        area=ctk.CTkScrollableFrame(self.main,fg_color="transparent")
        area.pack(fill="both",expand=True,padx=24,pady=12)
        def render(*_):
            for w in area.winfo_children():w.destroy()
            items=self.product_rows(search.get().strip())
            if not items:
                ctk.CTkLabel(area,text="No available products found.",text_color=MUTED).pack(pady=30);return
            for i,p in enumerate(items):
                card=self.card(area)
                card.grid(row=i//3,column=i%3,sticky="nsew",padx=7,pady=7)
                area.grid_columnconfigure(i%3,weight=1)
                ctk.CTkLabel(card,text=p["category"].upper(),text_color=GREEN,
                             font=ctk.CTkFont(size=10,weight="bold")).pack(anchor="w",padx=15,pady=(14,4))
                ctk.CTkLabel(card,text=p["name"],text_color=TEXT,
                             font=ctk.CTkFont(size=16,weight="bold"),wraplength=220).pack(anchor="w",padx=15,pady=4)
                ctk.CTkLabel(card,text=f"Rs. {p['selling_price']:,.2f}",text_color=GREEN,
                             font=ctk.CTkFont(size=18,weight="bold")).pack(anchor="w",padx=15,pady=4)
                ctk.CTkLabel(card,text=f"{p['quantity']} available",text_color=MUTED).pack(anchor="w",padx=15)
                ctk.CTkButton(card,text="Add to cart",fg_color=GREEN,
                              command=lambda x=p:self.add_to_cart(x)).pack(fill="x",padx=15,pady=14)
        search.bind("<KeyRelease>",render)
        render()

    def add_to_cart(self,p):
        pid=p["id"]
        current=self.cart.get(pid,0)
        if current>=p["quantity"]:
            messagebox.showwarning("Stock limit","You cannot add more than available stock.");return
        self.cart[pid]=current+1
        messagebox.showinfo("Added",f"{p['name']} added to cart.")

    def page_cart(self):
        self.page_header("Shopping Cart", "Review your items before placing the order")
        panel=self.card(self.main);panel.pack(fill="both",expand=True,padx=30,pady=5)
        tree=self.make_tree(panel,("id","name","qty","price","total"),("Product ID","Product","Quantity","Unit Price","Line Total"),height=10)
        total=0
        for pid,qty in self.cart.items():
            p=self.db.query("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone()
            if p:
                line=p["selling_price"]*qty;total+=line
                tree.insert("","end",values=(pid,p["name"],qty,f"{p['selling_price']:.2f}",f"{line:.2f}"))
        footer=ctk.CTkFrame(panel,fg_color="transparent");footer.pack(fill="x",padx=18,pady=15)
        total_label=ctk.CTkLabel(footer,text=f"Order total: Rs. {total:,.2f}",text_color=TEXT,font=ctk.CTkFont(size=20,weight="bold"))
        total_label.pack(side="left")
        def remove():
            sel=tree.selection()
            if not sel:return
            pid=int(tree.item(sel[0],"values")[0]);self.cart.pop(pid,None);self.show_page("cart")
        ctk.CTkButton(footer,text="Remove selected",fg_color="#FCE9E7",text_color=RED,command=remove).pack(side="right",padx=5)
        ctk.CTkButton(footer,text="Place Order",fg_color=GREEN,command=lambda:self.checkout("customer")).pack(side="right",padx=5)

    def checkout(self, order_type="customer"):
        if not self.cart:
            messagebox.showwarning("Empty cart","Add products before checkout.");return
        total=0;items=[]
        for pid,qty in self.cart.items():
            p=self.db.query("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone()
            if not p or p["quantity"]<qty:
                messagebox.showerror("Stock changed",f"Insufficient stock for product ID {pid}. Refresh cart.");return
            items.append((p,qty));total+=p["selling_price"]*qty
        if not messagebox.askyesno("Confirm order",f"Confirm order for Rs. {total:,.2f}?"):return
        customer_id=self.current_user["id"] if self.current_user["role"]=="customer" else None
        employee_id=self.current_user["id"] if self.current_user["role"]=="employee" else None
        cur=self.db.execute("INSERT INTO orders(customer_id,employee_id,order_type,total,status,created_at) VALUES(?,?,?,?,?,?)",
            (customer_id,employee_id,order_type,total,"Completed",datetime.now().isoformat(timespec="minutes")))
        oid=cur.lastrowid
        for p,qty in items:
            self.db.execute("INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,line_total) VALUES(?,?,?,?,?,?)",
                (oid,p["id"],p["name"],qty,p["selling_price"],p["selling_price"]*qty))
            self.db.execute("UPDATE products SET quantity=quantity-? WHERE id=?",(qty,p["id"]))
        self.cart={}
        messagebox.showinfo("Order successful",f"Order #{oid} placed successfully.\nTotal: Rs. {total:,.2f}")
        if self.current_user["role"]=="customer":self.show_page("myorders")
        else:self.show_page("pos")

    def page_myorders(self):
        self.page_header("My Orders", "Your recent grocery purchases")
        tree=self.make_tree(self.main,("id","total","status","date"),("Order ID","Total (Rs.)","Status","Order Date"))
        for o in self.db.query("SELECT * FROM orders WHERE customer_id=? ORDER BY id DESC",(self.current_user["id"],)):
            tree.insert("","end",values=(o["id"],f"{o['total']:.2f}",o["status"],o["created_at"]))
        ctk.CTkLabel(self.main,text="Select an order to view its items in your order history (order details are stored in the database).",
                     text_color=MUTED).pack(anchor="w",padx=30,pady=8)

    def page_pos(self):
        self.page_header("Point of Sale", "Create in-store sales and process customer checkout")
        bar=ctk.CTkFrame(self.main,fg_color="transparent");bar.pack(fill="x",padx=28)
        search=ctk.CTkEntry(bar,width=330,height=40,placeholder_text="Search product to add...")
        search.pack(side="left",pady=5)
        ctk.CTkButton(bar,text="Add selected product",fg_color=GREEN,
                      command=lambda:self.pos_add_selected(tree)).pack(side="left",padx=8)
        area=self.card(self.main);area.pack(fill="both",expand=True,padx=30,pady=10)
        tree=self.make_tree(area,("id","name","category","stock","price"),("ID","Product","Category","Available","Price (Rs.)"),height=12)
        def refresh(*_):
            for x in tree.get_children():tree.delete(x)
            for p in self.product_rows(search.get().strip()):
                tree.insert("","end",values=(p["id"],p["name"],p["category"],p["quantity"],p["selling_price"]))
        search.bind("<KeyRelease>",refresh);refresh()
        ctk.CTkButton(self.main,text="Checkout current cart",fg_color=GREEN,
                      command=lambda:self.checkout("employee")).pack(anchor="e",padx=32,pady=(0,16))

    def pos_add_selected(self,tree):
        pid=self.selected_id(tree)
        if pid is None:return
        p=self.db.query("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
        self.add_to_cart(dict(p))

if __name__ == "__main__":
    app = SmartGroceryApp()
    app.mainloop()
