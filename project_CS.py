#!/usr/bin/env python3
import mysql.connector as sql
from datetime import date
import time as t
import os
from decimal import Decimal, ROUND_HALF_UP
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
import bcrypt

# -------------------------
# Database helpers
# -------------------------
def connect_to_database():
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '1401')
        db_name = os.getenv('DB_NAME', 'project_cs')
        mydb = sql.connect(host=db_host, user=db_user, password=db_password, database=db_name, charset='utf8')
        print("Establishing Connection ... ")
        t.sleep(0.3)
        print(f"Your Connection ID is {mydb.connection_id}")
        cur = mydb.cursor()
        return mydb, cur
    except sql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None

def create_tables(cursor):
    """
    Create tables only if they don't already exist, using the schema you provided.
    This ensures new DBs get the same layout (matching your DESCRIBE output).
    """
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                p_id INT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price INT NOT NULL,
                quantity INT,
                brand VARCHAR(100),
                supplier VARCHAR(100)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profits (
                p_id INT PRIMARY KEY,
                profit INT,
                FOREIGN KEY (p_id) REFERENCES stock(p_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cust_info (
                cust_id INT AUTO_INCREMENT PRIMARY KEY,
                phone_no VARCHAR(15) NOT NULL UNIQUE,
                name VARCHAR(50) NOT NULL,
                address VARCHAR(100)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                bill_no INT AUTO_INCREMENT PRIMARY KEY,
                cust_id INT,
                bill_date DATE,
                total_price INT,
                FOREIGN KEY (cust_id) REFERENCES cust_info(cust_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billitems (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_no INT NOT NULL,
                p_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                tax_rate DECIMAL(5,2) NOT NULL,
                line_total DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (bill_no) REFERENCES bills(bill_no),
                FOREIGN KEY (p_id) REFERENCES stock(p_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARBINARY(60) NOT NULL,
                role ENUM('owner','manager','cashier') NOT NULL DEFAULT 'cashier',
                active TINYINT(1) NOT NULL DEFAULT 1
            )
        """)
        print("Checked/created tables: stock, profits, cust_info, bills, billitems, users.")
    except sql.Error as e:
        print(f"Error creating tables: {e}")

# -------------------------
# Utilities & small helpers
# -------------------------
def to_decimal(value):
    """Convert numeric DB values (often int) to Decimal safely."""
    return Decimal(str(value)).quantize(Decimal('0.01'))

def quantize_money(d: Decimal) -> Decimal:
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# -------------------------
# Admin & user functions
# -------------------------
def ensure_owner_user(cursor, db_connection):
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            print("No users found. Create an owner account.")
            while True:
                username = input("Set owner username: ").strip()
                if username:
                    break
            while True:
                password = input("Set owner password (min 6 chars): ").strip()
                if len(password) >= 6:
                    break
                print("Password must be at least 6 characters.")
            pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'owner')", (username, pw_hash))
            db_connection.commit()
            print("Owner account created.")
    except sql.Error as e:
        print(f"Error ensuring owner user: {e}")

def login(cursor):
    print("Login Required")
    for _ in range(3):
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        try:
            cursor.execute("SELECT user_id, password_hash, role, active FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()
            if row is None:
                print("Invalid credentials.")
                continue
            user_id, password_hash, role, active = row
            if not active:
                print("Account inactive.")
                continue
            if bcrypt.checkpw(password.encode('utf-8'), password_hash):
                print(f"Logged in as {username} ({role})")
                return {"user_id": user_id, "username": username, "role": role}
            else:
                print("Invalid credentials.")
        except sql.Error as e:
            print(f"Login error: {e}")
            break
    return None

def require_owner(current_user):
    if not current_user or current_user.get('role') != 'owner':
        print("Access denied. Owner permissions required.")
        return False
    return True

# -------------------------
# Stock / Product functions
# -------------------------
def check_stock(cursor):
    print("Checking Stocks")
    try:
        cursor.execute("""
            SELECT s.p_id, s.name, s.price, s.quantity, s.brand, s.supplier, p.profit
            FROM stock s
            LEFT JOIN profits p ON s.p_id = p.p_id
            ORDER BY s.p_id
        """)
        result = cursor.fetchall()
        print(f"{'P_ID':<6} {'Name':<25} {'Price':<8} {'Qty':<6} {'Brand':<15} {'Supplier':<15} {'Profit':<8}")
        print("=" * 90)
        for rec in result:
            p_id, name, price, quantity, brand, supplier, profit = rec
            print(f"{p_id:<6} {name:<25} {price:<8} {quantity if quantity is not None else 0:<6} {brand or '':<15} {supplier or '':<15} {profit if profit is not None else '':<8}")
    except sql.Error as e:
        print(f"Error fetching stock details: {e}")

def add_item(cursor, db_connection):
    print("Add Product")
    try:
        cursor.execute("SELECT MAX(p_id) FROM stock")
        result = cursor.fetchone()
        new_p_id = result[0] + 1 if result and result[0] is not None else 1
        print(f"Generated Product ID: {new_p_id}")
        name = input("Enter product name: ").strip()
        price = int(input("Enter price (integer): "))
        quantity = int(input("Enter quantity: "))
        brand = input("Enter brand: ").strip()
        supplier = input("Enter supplier: ").strip()
        profit = int(input("Enter profit amount (integer): "))
        insert_product_query = """
            INSERT INTO stock (p_id, name, price, quantity, brand, supplier)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_product_query, (new_p_id, name, price, quantity, brand, supplier))
        cursor.execute("INSERT INTO profits (p_id, profit) VALUES (%s, %s)", (new_p_id, profit))
        db_connection.commit()
        print("Product added successfully with ID:", new_p_id)
    except sql.Error as e:
        print(f"Error adding product: {e}")
    except ValueError as ve:
        print(f"Invalid input: {ve}")

# -------------------------
# Customer functions
# -------------------------
def cust_info(cursor):
    print("Checking Customer Details")
    try:
        cursor.execute("SELECT cust_id, phone_no, name, address FROM cust_info ORDER BY cust_id")
        result = cursor.fetchall()
        print(f"{'Cust_ID':<8} {'Phone_No':<15} {'Name':<30} {'Address':<40}")
        print("=" * 100)
        for cust_id, phone_no, name, address in result:
            print(f"{cust_id:<8} {phone_no:<15} {name:<30} {address or '':<40}")
    except sql.Error as e:
        print(f"Error fetching customer details: {e}")

def cust_update(cursor, db_connection):
    while True:
        print("Update Customer Information (e to exit)")
        choice = input("What to update? (1 name, 2 address, 3 phone): ").strip()
        if choice.lower() in ('e', 'exit'):
            break
        if choice not in ('1','2','3'):
            print("Invalid choice.")
            continue
        identifier = input("Enter customer ID or phone number: ").strip()
        cust_id = None
        if identifier.isdigit() and len(identifier) == 10:
            phone = identifier
            cursor.execute("SELECT cust_id FROM cust_info WHERE phone_no = %s", (phone,))
            row = cursor.fetchone()
            if not row:
                print("Phone number not found.")
                continue
            cust_id = row[0]
        elif identifier.isdigit():
            cust_id = int(identifier)
            cursor.execute("SELECT 1 FROM cust_info WHERE cust_id = %s", (cust_id,))
            if cursor.fetchone() is None:
                print("Customer ID not found.")
                continue
        else:
            print("Invalid input.")
            continue

        try:
            if choice == '1':
                new_name = input("Enter the new name: ").strip()
                cursor.execute("UPDATE cust_info SET name = %s WHERE cust_id = %s", (new_name, cust_id))
                db_connection.commit()
                print("Name updated.")
            elif choice == '2':
                new_address = input("Enter new address: ").strip()
                cursor.execute("UPDATE cust_info SET address = %s WHERE cust_id = %s", (new_address, cust_id))
                db_connection.commit()
                print("Address updated.")
            elif choice == '3':
                new_phone = input("Enter new phone number (10 digits): ").strip()
                if len(new_phone) != 10 or not new_phone.isdigit():
                    print("Invalid phone number.")
                    continue
                cursor.execute("UPDATE cust_info SET phone_no = %s WHERE cust_id = %s", (new_phone, cust_id))
                db_connection.commit()
                print("Phone updated.")
        except sql.Error as e:
            print(f"Error updating customer information: {e}")

# -------------------------
# Stock reorder & profits
# -------------------------
def simulate_auto_call(supplier):
    print(f"Simulating automated call to supplier: {supplier}...")
    t.sleep(1)
    print("Automated call completed.")

def check_reorder(cursor, db_connection):
    try:
        print("Checking reorder levels...")
        cursor.execute("""
            SELECT s.p_id, s.name, s.quantity, s.supplier, COALESCE(p.profit, 0)
            FROM stock s
            LEFT JOIN profits p ON s.p_id = p.p_id
            ORDER BY s.p_id
        """)
        result = cursor.fetchall()
        products_to_reorder = [(p_id, name, quantity or 0, supplier or '') for p_id, name, quantity, supplier, _ in result if (quantity or 0) <= 10]
        if not products_to_reorder:
            print("All products are above reorder level.")
            return
        print(f"{'P_ID':<6} {'Name':<25} {'Quantity':<8} {'Supplier':<20}")
        print("="*60)
        for p_id, name, quantity, supplier in products_to_reorder:
            print(f"{p_id:<6} {name:<25} {quantity:<8} {supplier:<20}")
            simulate_auto_call(supplier)
            while True:
                restocked = input("Have the items been restocked? (yes/no): ").strip().lower()
                if restocked == 'no':
                    print("Admin will need to manually update the stock.")
                    manual_update = input("Enter the new quantity of the product (0 if not restocked): ").strip()
                    try:
                        new_quantity = int(manual_update)
                        if new_quantity >= 0:
                            cursor.execute("UPDATE stock SET quantity = %s WHERE p_id = %s", (new_quantity, p_id))
                            db_connection.commit()
                            print(f"Stock updated for Product ID {p_id}. New quantity: {new_quantity}")
                            break
                        else:
                            print("Quantity must be >= 0.")
                    except ValueError:
                        print("Invalid number.")
                elif restocked == 'yes':
                    restocked_quantity = input("Enter the quantity restocked: ").strip()
                    try:
                        restocked_quantity = int(restocked_quantity)
                        if restocked_quantity > 0:
                            cursor.execute("SELECT quantity FROM stock WHERE p_id = %s", (p_id,))
                            cur_qty = cursor.fetchone()[0] or 0
                            new_quantity = cur_qty + restocked_quantity
                            cursor.execute("UPDATE stock SET quantity = %s WHERE p_id = %s", (new_quantity, p_id))
                            db_connection.commit()
                            print(f"Stock updated for Product ID {p_id}. New quantity: {new_quantity}")
                            break
                        else:
                            print("Restocked quantity must be > 0.")
                    except ValueError:
                        print("Invalid number.")
                else:
                    print("Please answer 'yes' or 'no'.")
    except sql.Error as e:
        print(f"Error checking reorder levels: {e}")

def check_total_profits(cursor):
    print("Checking Total Profits")
    try:
        cursor.execute("""
            SELECT
                SUM(bi.quantity * bi.unit_price) AS total_sales,
                SUM((bi.unit_price - COALESCE(s.price,0)) * bi.quantity) AS total_profit
            FROM billitems bi
            INNER JOIN stock s ON s.p_id = bi.p_id
        """)
        result = cursor.fetchone()
        if result:
            total_sales, total_profits = result
            total_sales = total_sales or 0
            total_profits = total_profits or 0
            print(f"Total Sales Amount: {total_sales}")
            print(f"Total Profits Amount: {total_profits}")
        else:
            print("No profit data available.")
    except sql.Error as e:
        print(f"Error fetching total profits: {e}")

# -------------------------
# User management
# -------------------------
def manage_users(cursor, db_connection):
    while True:
        print("User Management")
        print("1. Add user")
        print("2. Disable user")
        print("e. Back")
        choice = input("Choose: ").strip()
        if choice == '1':
            username = input("Username: ").strip()
            role = input("Role (owner/manager/cashier): ").strip()
            if role not in ('owner','manager','cashier'):
                print("Invalid role.")
                continue
            password = input("Password: ").strip()
            pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            try:
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, pw_hash, role))
                db_connection.commit()
                print("User added.")
            except sql.Error as e:
                print(f"Error adding user: {e}")
        elif choice == '2':
            username = input("Username to disable: ").strip()
            try:
                cursor.execute("UPDATE users SET active = 0 WHERE username = %s", (username,))
                db_connection.commit()
                print("User disabled.")
            except sql.Error as e:
                print(f"Error disabling user: {e}")
        elif choice.lower() in ('e','exit'):
            break
        else:
            print("Invalid choice.")

# -------------------------
# Billing
# -------------------------
def bill(cursor, db_connection):
    print("Making Bills")
    try:
        db_connection.start_transaction()
        # Get or create customer
        while True:
            phone = input("Enter Phone no. of Customer: ").strip()
            if len(phone) != 10 or not phone.isdigit():
                print("Number should be exactly 10 digits.")
            else:
                break
        cursor.execute("SELECT cust_id, name FROM cust_info WHERE phone_no = %s", (phone,))
        result = cursor.fetchone()
        if result:
            cust_id, cust_name = result
            print(f"Welcome back, {cust_name}!")
        else:
            name = input("Enter Name of Customer: ").strip()
            address = input("Enter Address of Customer: ").strip()
            cursor.execute("INSERT INTO cust_info (phone_no, name, address) VALUES (%s, %s, %s)", (phone, name, address))
            db_connection.commit()
            cust_id = cursor.lastrowid
            print("Customer Information Added")

        final_p = Decimal('0.00')         # subtotal (sum of unit * qty)
        total_profit = Decimal('0.00')
        items_added = []

        while True:
            prod_id = input("Enter product ID or search text (e=finalize): ").strip()
            if prod_id.lower() in ('e', 'exit'):
                break
            if prod_id.isdigit():  # treat as p_id
                p_id = int(prod_id)
                quantity = int(input("Enter quantity: ").strip())
                if quantity <= 0:
                    print("Quantity must be > 0.")
                    continue
                select_query = "SELECT price, quantity FROM stock WHERE p_id = %s FOR UPDATE"
                cursor.execute(select_query, (p_id,))
                row = cursor.fetchone()
                if not row:
                    print("Product not found.")
                    continue
                price_db, stock_qty = row
                if stock_qty is None:
                    stock_qty = 0
                if quantity > stock_qty:
                    print("Insufficient stock.")
                    continue
                unit_price = to_decimal(price_db)  # stock.price is int; convert to Decimal
                line_subtotal = unit_price * Decimal(quantity)
                # profit from profits table (profit stored as integer)
                cursor.execute("SELECT profit FROM profits WHERE p_id = %s", (p_id,))
                prof_row = cursor.fetchone()
                profit_amount = Decimal(prof_row[0]) if prof_row and prof_row[0] is not None else Decimal('0')
                item_profit = profit_amount * Decimal(quantity)
                final_p += line_subtotal
                total_profit += item_profit
                # Update stock quantity
                new_quantity = stock_qty - quantity
                cursor.execute("UPDATE stock SET quantity = %s WHERE p_id = %s", (new_quantity, p_id))
                # tax_rate default (because stock doesn't have tax_rate column)
                line_tax_rate = Decimal('18.00')
                line_total = quantize_money(line_subtotal)  # we write line_total without tax (consistent with previous approach)
                items_added.append((p_id, quantity, unit_price, line_tax_rate, line_total))
                print(f"Added {quantity} x product {p_id} -> line total {line_total}")
            else:
                # search by name
                q = f"%{prod_id}%"
                try:
                    cursor.execute("""
                        SELECT p_id, name, price, quantity FROM stock
                        WHERE name LIKE %s
                        ORDER BY quantity DESC LIMIT 10
                    """, (q,))
                    rows = cursor.fetchall()
                    if not rows:
                        print("No matching items.")
                    else:
                        print(f"{'P_ID':<6}{'Name':<25}{'Price':<8}{'Qty':<6}")
                        for pid, name, price, qty in rows:
                            print(f"{pid:<6}{name:<25}{price:<8}{qty if qty is not None else 0:<6}")
                except sql.Error as e:
                    print(f"Search error: {e}")

        # compute GST (sum of line_subtotals * tax_rate)
        total_gst = Decimal('0.00')
        for _, qty, unit_price, tax_rate, _ in items_added:
            line_subtotal = unit_price * Decimal(qty)
            total_gst += (line_subtotal * (tax_rate / Decimal('100')))

        gst = quantize_money(total_gst)
        grand_total = quantize_money(final_p + gst)

        # bills.total_price column is INT in your DB schema. We'll store subtotal as INT (rounded).
        # Keep a record of the float/decimal totals in billitems and receipts.
        bill_total_for_db = int(final_p.to_integral_value(rounding=ROUND_HALF_UP))

        insert_bill_query = "INSERT INTO bills (cust_id, bill_date, total_price) VALUES (%s, %s, %s)"
        bill_date = date.today()
        cursor.execute(insert_bill_query, (cust_id, bill_date, bill_total_for_db))
        bill_id = cursor.lastrowid

        for p_id, qty, unit_price, tax_rate, line_total in items_added:
            cursor.execute("""
                INSERT INTO billitems (bill_no, p_id, quantity, unit_price, tax_rate, line_total)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (bill_id, p_id, qty, str(unit_price), str(tax_rate), str(line_total)))

        db_connection.commit()

        invoice_no = f"INV-{bill_date.year}-{bill_id:06d}"
        print_receipt(cursor, bill_id, invoice_no, gst)
        print("\n--- Bill Summary ---")
        print(f'Bill ID: {bill_id}')
        print(f'Invoice No: {invoice_no}')
        print(f'Customer ID: {cust_id}')
        print(f'Total Before GST: {quantize_money(final_p)}')
        print(f'Applied GST: {gst}')
        print(f'Total After GST: {grand_total}')
        print(f'Bill Date: {bill_date}')

    except sql.Error as e:
        print(f"Error processing bill: {e}")
        try:
            db_connection.rollback()
        except Exception:
            pass
    except ValueError as ve:
        print(f"Invalid input: {ve}")

def print_receipt(cursor, bill_id, invoice_no, gst_amount):
    try:
        cursor.execute("""
            SELECT b.bill_no, b.bill_date, b.total_price, c.name, c.phone_no, c.address
            FROM bills b
            INNER JOIN cust_info c ON c.cust_id = b.cust_id
            WHERE b.bill_no = %s
        """, (bill_id,))
        bill = cursor.fetchone()
        cursor.execute("""
            SELECT bi.p_id, s.name, bi.quantity, bi.unit_price, bi.tax_rate, bi.line_total
            FROM billitems bi INNER JOIN stock s ON s.p_id = bi.p_id
            WHERE bi.bill_no = %s
        """, (bill_id,))
        items = cursor.fetchall()
        os.makedirs('receipts', exist_ok=True)
        file_path = os.path.join('receipts', f'{invoice_no}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("GROCERY SHOP RECEIPT\n")
            f.write(f"Invoice: {invoice_no}\n")
            f.write(f"Date: {bill[1]}\n")
            f.write(f"Customer: {bill[3]}  Phone: {bill[4]}\n")
            f.write("\nItems:\n")
            f.write(f"{'P_ID':<8}{'Name':<25}{'Qty':<6}{'Price':<10}{'Tax%':<6}{'Line':<10}\n")
            for p_id, name, qty, price, tax_rate, line_total in items:
                f.write(f"{p_id:<8}{name:<25}{qty:<6}{price:<10}{tax_rate:<6}{line_total:<10}\n")
            f.write("\n")
            # bill[2] is total_price as stored (int). We'll show computed GST and grand total using gst_amount.
            f.write(f"Subtotal (stored int): {bill[2]}\n")
            f.write(f"GST: {gst_amount}\n")
            # compute grand total for receipt
            # gather subtotal from billitems for exact display:
            cursor.execute("SELECT SUM(line_total) FROM billitems WHERE bill_no = %s", (bill_id,))
            line_sum = cursor.fetchone()[0] or Decimal('0.00')
            grand_total = quantize_money(Decimal(line_sum) + gst_amount)
            f.write(f"Grand Total: {grand_total}\n")
        print(f"Receipt saved to {file_path}")
    except Exception as e:
        print(f"Error printing receipt: {e}")

# -------------------------
# Admin menu and main
# -------------------------
def admin_privileges(cursor, db_connection, current_user):
    if not require_owner(current_user):
        return
    while True:
        print("\nAdmin Privileges (Owner)")
        print("4. Check Stock")
        print("5. Check Customer Info")
        print("6. Update Customer Info")
        print("7. Insert New Product")
        print("8. Check Reorder Level")
        print("9. Check Total Profits")
        print("11. Manage Users (Add/Disable)")
        print("e. Exit Admin Privileges")
        choice = input("Enter your choice: ").strip()
        if choice == '4':
            check_stock(cursor)
        elif choice == '5':
            cust_info(cursor)
        elif choice == '6':
            cust_update(cursor, db_connection)
        elif choice == '7':
            add_item(cursor, db_connection)
        elif choice == '8':
            check_reorder(cursor, db_connection)
        elif choice == '9':
            check_total_profits(cursor)
        elif choice == '11':
            manage_users(cursor, db_connection)
        elif choice.lower() in ('e','exit'):
            break
        else:
            print("Invalid choice.")

def genrate():
    import base64
    info = [base64.b64decode(data).decode('utf-8') for data in []]
    print(info)

def main():
    db_connection, cursor = connect_to_database()
    if not db_connection or not cursor:
        return
    create_tables(cursor)
    ensure_owner_user(cursor, db_connection)
    current_user = login(cursor)
    if not current_user:
        print("Exiting due to failed login.")
        db_connection.close()
        return
    while True:
        print("\nMain Menu")
        print("1. Generate Bill")
        if current_user.get('role') == 'owner':
            print("2. Admin Privileges")
        print("e. Exit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            bill(cursor, db_connection)
        elif choice == '2' and current_user.get('role') == 'owner':
            admin_privileges(cursor, db_connection, current_user)
        elif choice in ('e', 'exit'):
            genrate()
            print("Exiting...")
            db_connection.close()
            break
        else:
            print("Incorrect Command.")

if __name__ == "__main__":
    main()
