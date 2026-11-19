# 🛒 SMART GROCERY PRO

> **A smarter way to manage your everyday grocery business — Inventory • Sales • Customers**  
> **3rd Semester Academic Project** — Bachelor of Engineering in Software Engineering  
> **Institution:** Mehran University of Engineering and Technology (MUET), Shaheed Zulfiqar Ali Bhutto Campus, Khairpur Mirs

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter%20%7C%20Tkinter-176B4D?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![DSA](https://img.shields.io/badge/Data%20Structures-Singly%20Linked%20List-104A36?style=for-the-badge)](#data-structures--architecture)
[![Academic](https://img.shields.io/badge/MUET-3rd%20Semester%20Project-04A436?style=for-the-badge)](#academic-context)

---

## 📖 Table of Contents
1. [Project Overview](#-project-overview)
2. [Academic Context](#-academic-context)
3. [Key Features & Portals](#-key-features--portals)
4. [Data Structures & Architecture](#-data-structures--architecture)
5. [Application Screenshots & Walkthrough](#-application-screenshots--walkthrough)
6. [Tech Stack](#-tech-stack)
7. [Project Structure](#-project-structure)
8. [Installation & Setup Guide](#-installation--setup-guide)
9. [Demo Credentials](#-demo-credentials)
10. [Source Code (`main.py`)](#-source-code-mainpy)
11. [Author](#-author)

---

## 📌 Project Overview

**SMART GROCERY PRO** is a desktop grocery store management and customer shopping application built in **Python** using **CustomTkinter / Tkinter** and **SQLite3** (`smart_grocery.db`). It provides role-based workspaces for **Administrators / Staff** and **Customers**, featuring real-time dashboard metrics, low-stock alerts, order fulfillment, financial reports, profile photo uploads, and a custom **Singly Linked List** for product inventory traversal.

---

## 🎓 Academic Context

* **Program:** Bachelor of Engineering in Software Engineering (3rd Semester Project)
* **University:** Mehran University of Engineering and Technology (MUET), SZAB Campus, Khairpur Mirs
* **Key Focus Areas:** GUI design, role-based access control, SQLite database persistence, media handling (`uploads/`), and data structure implementation.

---

## ✨ Key Features & Portals

### 🔐 Login & Registration
* Sign in with username and password or register a new **Customer Account**.
* Role-based routing for **Admin / Employee** and **Customer** portals.

### 🧑‍💼 Admin Workspace
* **Dashboard Overview:** Tracks **Total Products**, **Customers**, **Employees**, **Total Revenue (Rs.)**, **Low Stock Alerts**, and **Recent Orders**.
* **Product Inventory:** Search and manage products (**+ Add Product**, **Edit Selected**, **Delete Selected**) with category, stock, cost price, selling price, minimum stock, and supplier details.
* **Customers & Staff:** View registered users and add new **Employee** accounts.
* **Orders:** Review customer orders and mark selected orders as **Completed**.
* **Reports & Analytics:** View **Gross Sales**, **Orders** count, **Estimated Cost**, and color-coded **Inventory Summary** (`In stock` vs. `LOW STOCK`).
* **My Profile:** Update profile details and upload/change profile photos.

### 🛍️ Customer Portal
* **Discover Groceries / Shop Products:** Browse items by category, search products, check stock availability, and add items to the cart.
* **Shopping Cart:** Review quantities, unit prices, and line totals, remove items, calculate order total, and place orders.
* **My Orders & My Profile:** Track orders and update personal details/profile photo.

---

## 🧠 Data Structures & Architecture

* **Custom Singly Linked List:** Product records are loaded into a custom singly linked list for traversal and search in the inventory view.
* **SQLite3 Database (`smart_grocery.db`):** Persists user accounts, products, orders, and order items locally.
* **Uploads Directory (`uploads/`):** Stores uploaded user profile images.

---

## 📸 Application Screenshots & Walkthrough

### 1. Login Screen
![Login Screen](screenshots/login.png)

### 2. Admin Dashboard
![Admin Dashboard](screenshots/admin_dashboard.png)

### 3. Product Inventory (Singly Linked List)
![Product Inventory](screenshots/admin_products.png)

### 4. Customers & Staff
![Customers and Staff](screenshots/admin_users.png)

### 5. Orders Management
![Orders Management](screenshots/admin_orders.png)

### 6. Reports & Analytics
![Reports and Analytics](screenshots/admin_reports.png)

### 7. Admin Profile
![Admin Profile](screenshots/admin_profile.png)

### 8. Customer Shop — Discover Groceries
![Customer Discover Groceries](screenshots/customer_shop.png)

### 9. Customer Shopping Cart
![Customer Shopping Cart](screenshots/customer_cart.png)

### 10. Customer Profile
![Customer Profile](screenshots/customer_profile.png)

---

## 🛠️ Tech Stack

* **Python 3.x**
* **CustomTkinter & Tkinter (`ttk`)**
* **SQLite3**
* **Custom Singly Linked List**

---

## 🗂️ Project Structure

```text
SMART_GROCERY_PRO/
├── main.py
├── requirements.txt
├── smart_grocery.db
├── uploads/
├── screenshots/
├── .gitignore
└── README.md
