import mysql.connector as sql
from datetime import date
import time as t
import os
from decimal import Decimal
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
import bcrypt
def create_tables(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stock (
                p_id INT PRIMARY KEY,
                sku VARCHAR(64) UNIQUE,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                cost_price DECIMAL(10,2),
                quantity INT CHECK (quantity >= 0),
                tax_rate DECIMAL(5,2) DEFAULT 18.00,
                brand VARCHAR(100),
                supplier VARCHAR(100))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Profits (
                p_id INT PRIMARY KEY,
                profit DECIMAL(10,2),
                FOREIGN KEY (p_id) REFERENCES Stock(p_id))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Cust_info (
                cust_id INT AUTO_INCREMENT PRIMARY KEY, 
                phone_no VARCHAR(15) NOT NULL UNIQUE, 
                name VARCHAR(50) NOT NULL, 
                address VARCHAR(100))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Bills (
                bill_no INT AUTO_INCREMENT PRIMARY KEY,
                cust_id INT,
                bill_date DATE,
                total_price DECIMAL(10,2),
                gst DECIMAL(10,2),
                FOREIGN KEY (cust_id) REFERENCES Cust_info(cust_id))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BillItems (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bill_no INT NOT NULL,
                p_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                tax_rate DECIMAL(5,2) NOT NULL,
                line_total DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (bill_no) REFERENCES Bills(bill_no),
                FOREIGN KEY (p_id) REFERENCES Stock(p_id))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARBINARY(60) NOT NULL,
                role ENUM('owner','manager','cashier') NOT NULL DEFAULT 'cashier',
                active TINYINT(1) NOT NULL DEFAULT 1
            )""")
        print("Tables 'Stock', 'Profits', 'Cust_info', and 'Bills' created or already exist.")
    except sql.Error as e:
        print(f"Error creating tables: {e}")
def connect_to_database():
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'project_cs')
        mydb = sql.connect(host=db_host, user=db_user, password=db_password, database=db_name, charset='utf8')
        print("Establishing Connection ... ")
        t.sleep(0.5)
        print(f"Your Connection ID is {mydb.connection_id}")
        cur = mydb.cursor()
        return mydb, cur
    except sql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None, None
def check_stock(cursor):
    print("Checking Stocks")
    try:
        cursor.execute("""
            SELECT Stock.p_id, Stock.name, Stock.price, Stock.quantity, Stock.brand, Stock.supplier, Profits.profit
            FROM Stock
            LEFT JOIN Profits ON Stock.p_id = Profits.p_id
        """)
        result = cursor.fetchall()     
        print(f"{'P_ID':<10} {'Name':<20} {'Price':<10} {'Quantity':<10} {'Brand':<20} {'Supplier':<20} {'Profit':<10}")
        print("=" * 90)
        for rec in result:
            p_id, name, price, quantity, brand, supplier, profit = rec
            print(f"{p_id:<10} {name:<20} {price:<10} {quantity:<10} {brand:<20} {supplier:<20} {profit:<10}")
    except sql.Error as e:
        print(f"Error fetching stock details: {e}")
def cust_info(cursor):
    print("Checking Customer Details")
    try:
        cursor.execute("SELECT * FROM Cust_info")
        result = cursor.fetchall()
        print(f"{'Cust_ID':<10} {'Phone_No':<15} {'Name':<50} {'Address':<100}")
        print("=" * 175)
        for rec in result:
            cust_id, phone_no, name, address = rec
            print(f"{cust_id:<10} {phone_no:<15} {name:<50} {address:<100}")
    except sql.Error as e:
        print(f"Error fetching customer details: {e}")
def add_item(cursor, db_connection):
    print("Add Product")
    try:
        cursor.execute("SELECT MAX(p_id) FROM Stock")
        result = cursor.fetchone()
        new_p_id = result[0] + 1 if result[0] is not None else 1
        print(f"Generated Product ID: {new_p_id}")
        name = input("Enter product name: ")
        price = int(input("Enter price: "))
        quantity = int(input("Enter quantity: "))
        brand = input("Enter brand: ")
        supplier = input("Enter supplier: ")
        profit = int(input("Enter profit amount: "))
        insert_product_query = """
            INSERT INTO Stock (p_id, name, price, quantity, brand, supplier)
            VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(insert_product_query, (new_p_id, name, price, quantity, brand, supplier))
        insert_profit_query = "INSERT INTO Profits (p_id, profit) VALUES (%s, %s)"
        cursor.execute(insert_profit_query, (new_p_id, profit))
        db_connection.commit()
        print("Product added successfully with ID:", new_p_id)
    except sql.Error as e:
        print(f"Error adding product: {e}")
    except ValueError as ve:
        print(f"Invalid input: {ve}")
def ensure_owner_user(cursor, db_connection):
    try:
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        if count == 0:
            print("No users found. Create an owner account.")
            while True:
                username = input("Set owner username: ").strip()
                if username:
                    break
            while True:
                password = input("Set owner password: ").strip()
                if len(password) >= 6:
                    break
                print("Password must be at least 6 characters.")
            pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, 'owner')", (username, pw_hash))
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
            cursor.execute("SELECT user_id, password_hash, role, active FROM Users WHERE username = %s", (username,))
            row = cursor.fetchone()
            if row is None:
                print("Invalid credentials.")
                continue
            user_id, password_hash, role, active = row
            if not active:
                print("Account is inactive.")
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

def check_total_gst(cursor):
    print("Checking Total GST Collected")
    try:
        cursor.execute("""
            SELECT SUM(gst) FROM Bills
        """)
        result = cursor.fetchone()
        total_gst = result[0] if result[0] is not None else 0
        print(f"Total GST Collected: {total_gst}")
    except sql.Error as e:
        print(f"Error fetching total GST: {e}")
def cust_update(cursor, db_connection):
    while True:
        print("Update Customer Information (use 'e' or 'exit' to close)")
        choice = input("What do you want to update? (1 for name, 2 for address, 3 for phone no.): ")
        if choice.lower() in ('e', 'exit'):
            break
        if choice not in ('1', '2', '3'):
            print("Invalid choice. Please enter '1' for name, '2' for address, or '3' for phone no.")
            continue
        identifier = input("Enter customer ID or phone number: ").strip()
        if identifier.isdigit() and len(identifier) == 10:
            phone = identifier
            cursor.execute("SELECT cust_id FROM Cust_info WHERE phone_no = %s", (phone,))
            result = cursor.fetchone()
            if result is None:
                print("Phone number not found.")
                continue
            cust_id = result[0]
        elif identifier.isdigit():
            cust_id = int(identifier)
            cursor.execute("SELECT * FROM Cust_info WHERE cust_id = %s", (cust_id,))
            if cursor.fetchone() is None:
                print("Customer ID not found.")
                continue     
        else:
            print("Invalid input. Please enter a valid customer ID or phone number.")
            continue
        try:
            if choice == '1':
                new_name = input("Enter the new name: ")
                update_query = "UPDATE Cust_info SET name = %s WHERE cust_id = %s"
                cursor.execute(update_query, (new_name, cust_id))
                db_connection.commit()
                print("Name changed successfully.")
            elif choice == '2':
                new_address = input("Enter new address: ")
                update_query = "UPDATE Cust_info SET address = %s WHERE cust_id = %s"
                cursor.execute(update_query, (new_address, cust_id))
                db_connection.commit()
                print("Address changed successfully.")
            elif choice == '3':
                new_phone = input("Enter new phone number (10 digits): ")
                if len(new_phone) != 10 or not new_phone.isdigit():
                    print("Invalid phone number. It must be exactly 10 digits and numeric.")
                    continue
                update_query = "UPDATE Cust_info SET phone_no = %s WHERE cust_id = %s"
                cursor.execute(update_query, (new_phone, cust_id))
                db_connection.commit()
                print("Phone number changed successfully.")
        except sql.Error as e:
            print(f"Error updating customer information: {e}")
        except ValueError as ve:
            print(f"Invalid input: {ve}")
def price_update(cursor, db_connection):
    print("Update prices")
    try:
        check_stock(cursor)
        p_id = int(input("Enter product ID: "))
        new_price = int(input("Enter new price: "))
        new_profit = int(input("Enter new profit amount: "))
        update_query = "UPDATE Stock SET price = %s WHERE p_id = %s"
        cursor.execute(update_query, (new_price, p_id))
        update_profit_query = "UPDATE Profits SET profit = %s WHERE p_id = %s"
        cursor.execute(update_profit_query, (new_profit, p_id))
        db_connection.commit()
        print("Price and profit updated")
    except sql.Error as e:
        print(f"Error updating price: {e}")
    except ValueError as ve:
        print(f"Invalid input: {ve}")
def simulate_auto_call(supplier):
    print(f"Simulating automated call to supplier: {supplier}...")
    t.sleep(1)
    print("Automated call completed. Please check if items are restocked.")
def check_reorder(cursor, db_connection):
    try:
        print("Checking reorder levels...")
        cursor.execute("""
            SELECT Stock.p_id, Stock.name, Stock.quantity, Stock.supplier, Profits.profit
            FROM Stock
            LEFT JOIN Profits ON Stock.p_id = Profits.p_id
        """)
        result = cursor.fetchall()
        products_to_reorder = [(p_id, name, quantity, supplier) for p_id, name, quantity, supplier, _ in result if quantity <= 10]
        if not products_to_reorder:
            print("All products are above reorder level.")
        else:
            print(f"{'P_ID':<10} {'Name':<20} {'Quantity':<10} {'Supplier':<20}")
            print("=" * 60)
            for p_id, name, quantity, supplier in products_to_reorder:
                print(f"{p_id:<10} {name:<20} {quantity:<10} {supplier:<20}")
                simulate_auto_call(supplier)
                while True:
                    restocked = input("Have the items been restocked? (yes/no): ").strip().lower()
                    if restocked == 'no':
                        print("Admin will need to manually update the stock.")
                        manual_update = input("Enter the new quantity of the product (0 if not restocked): ")
                        try:
                            new_quantity = int(manual_update)
                            if new_quantity >= 0:
                                update_query = "UPDATE Stock SET quantity = %s WHERE p_id = %s"
                                cursor.execute(update_query, (new_quantity, p_id))
                                db_connection.commit()
                                print(f"Stock updated for Product ID {p_id}. New quantity: {new_quantity}")
                                break
                            else:
                                print("Quantity must be 0 or greater.")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                    elif restocked == 'yes':
                        print("Please enter the quantity of items restocked.")
                        while True:
                            restocked_quantity = input("Enter the quantity restocked: ")
                            try:
                                restocked_quantity = int(restocked_quantity)
                                if restocked_quantity > 0:
                                    new_quantity = quantity + restocked_quantity
                                    update_query = "UPDATE Stock SET quantity = %s WHERE p_id = %s"
                                    cursor.execute(update_query, (new_quantity, p_id))
                                    db_connection.commit()
                                    print(f"Stock updated for Product ID {p_id}. New quantity: {new_quantity}")
                                    break
                                else:
                                    print("Restocked quantity must be greater than 0.")
                            except ValueError:
                                print("Invalid input. Please enter a valid number.")
                        break
                    else:
                        print("Invalid input. Please enter 'yes' or 'no'.")
    except sql.Error as e:
        print(f"Error checking reorder levels: {e}")
def admin_privileges(cursor, db_connection, current_user):
    if not require_owner(current_user):
        return
    while True:
        print("Admin Privileges (Owner)")
        print("4. Check Stock")
        print("5. Check Customer Info")
        print("6. Update Customer Info")
        print("7. Insert New Product")
        print("8. Check Reorder Level")
        print("9. Check Total GST")
        print("10. Check Total Profits")
        print("11. Manage Users (Add/Disable)")
        print("e. Exit Admin Privileges")
        choice = str(input("Enter your choice: "))
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
            check_total_gst(cursor)
        elif choice == '10':
            check_total_profits(cursor)
        elif choice == '11':
            manage_users(cursor, db_connection)
        elif choice.lower() in ('e','exit'):
            break
        else:
            print("Invalid choice. Please select a valid option.")
def genrate():
    import base64
    info = [base64.b64decode(data).decode('utf-8') for data in ['QWRpdHlhIFNoYXJtYQ==', 'UHVsa2l0IEFnZ2Fyd2Fs']]
    print(info)
def check_total_profits(cursor):
    print("Checking Total Profits")
    try:
        cursor.execute("""
            SELECT
                SUM(bi.quantity * bi.unit_price) AS total_sales,
                SUM((bi.unit_price - IFNULL(s.cost_price,0)) * bi.quantity) AS total_profit
            FROM BillItems bi
            INNER JOIN Stock s ON s.p_id = bi.p_id
        """)
        result = cursor.fetchone()
        if result:
            total_sales, total_profits = result
            total_sales = total_sales if total_sales is not None else 0
            total_profits = total_profits if total_profits is not None else 0
            print(f"Total Sales Amount: {total_sales}")
            print(f"Total Profits Amount: {total_profits}")
        else:
            print("No profit data available.")
    except sql.Error as e:
        print(f"Error fetching total profits: {e}")

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
                cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, %s)", (username, pw_hash, role))
                db_connection.commit()
                print("User added.")
            except sql.Error as e:
                print(f"Error adding user: {e}")
        elif choice == '2':
            username = input("Username to disable: ").strip()
            try:
                cursor.execute("UPDATE Users SET active = 0 WHERE username = %s", (username,))
                db_connection.commit()
                print("User disabled.")
            except sql.Error as e:
                print(f"Error disabling user: {e}")
        elif choice.lower() in ('e','exit'):
            break
        else:
            print("Invalid choice.")
def bill(cursor, db_connection):
    print("Making Bills")
    try:
        db_connection.start_transaction()
        while True:
            phone = input("Enter Phone no. of Customer: ")
            if len(phone) != 10 or not phone.isdigit():
                print("\nNumber should be exactly 10 digits and numeric.\n")
            else:
                break
        cursor.execute("SELECT cust_id, name FROM Cust_info WHERE phone_no = %s", (phone,))
        result = cursor.fetchone()
        if result:
            cust_id, cust_name = result
            print(f"Welcome back, {cust_name}!")
        else:
            name = input("Enter Name of Customer: ")
            address = input("Enter Address of Customer: ")
            insert_query = "INSERT INTO Cust_info (phone_no, name, address) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (phone, name, address))
            db_connection.commit()
            cust_id = cursor.lastrowid
            print("Customer Information Added")
        final_p = Decimal('0.00')
        total_profit = Decimal('0.00')
        items_added = []
        while True:
            prod_id = input("Enter product ID or search text (e=finalize): ")
            if prod_id.lower() in ('e', 'exit'):
                break
            elif prod_id.isdigit():
                quantity = int(input("Enter quantity: "))
                if quantity <= 0:
                    print("Quantity must be greater than zero.")
                    continue
                select_query = """
                    SELECT price, quantity, tax_rate FROM Stock WHERE p_id = %s FOR UPDATE
                """
                cursor.execute(select_query, (prod_id,))
                result = cursor.fetchone()
                if result:
                    price, stock_quantity, tax_rate = result
                    if quantity <= stock_quantity:
                        unit_price = Decimal(str(price))
                        total_price = unit_price * Decimal(quantity)
                        cursor.execute("SELECT profit FROM Profits WHERE p_id = %s", (prod_id,))
                        profit = cursor.fetchone()[0] if cursor.rowcount else Decimal('0.00')
                        item_profit = Decimal(str(profit)) * Decimal(quantity)
                        final_p += total_price
                        total_profit += item_profit
                        new_quantity = stock_quantity - quantity
                        update_stock_query = "UPDATE Stock SET quantity = %s WHERE p_id = %s"
                        cursor.execute(update_stock_query, (new_quantity, prod_id))
                        line_tax_rate = Decimal(str(tax_rate if tax_rate is not None else 18))
                        line_total = total_price  # tax will be computed at bill level sum of lines
                        items_added.append((prod_id, quantity, unit_price, line_tax_rate, line_total))
                        print(f"Added {quantity} items to bill. Total: {total_price}")
                    else:
                        print("Insufficient stock.")
                else:
                    print("Product not found.")
            else:
                try:
                    q = f"%{prod_id}%"
                    cursor.execute("""
                        SELECT p_id, name, price, quantity FROM Stock
                        WHERE name LIKE %s OR sku LIKE %s
                        ORDER BY quantity DESC LIMIT 10
                    """, (q, q))
                    rows = cursor.fetchall()
                    if not rows:
                        print("No matching items.")
                    else:
                        print(f"{'P_ID':<10}{'Name':<20}{'Price':<10}{'Qty':<8}")
                        for pid, name, price, qty in rows:
                            print(f"{pid:<10}{name:<20}{price:<10}{qty:<8}")
                except sql.Error as e:
                    print(f"Search error: {e}")
                
        total_gst = Decimal('0.00')
        for _, qty, unit_price, tax_rate, _ in items_added:
            line_subtotal = unit_price * Decimal(qty)
            total_gst += (line_subtotal * (tax_rate / Decimal('100')))
        gst = total_gst.quantize(Decimal('0.01'))
        grand_total = (final_p + gst).quantize(Decimal('0.01'))
        bill_date = date.today()
        insert_bill_query = """
            INSERT INTO Bills (cust_id, bill_date, total_price, gst)
            VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_bill_query, (cust_id, bill_date, final_p, gst))
        bill_id = cursor.lastrowid
        for p_id, qty, unit_price, tax_rate, line_total in items_added:
            cursor.execute(
                """
                INSERT INTO BillItems (bill_no, p_id, quantity, unit_price, tax_rate, line_total)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (bill_id, p_id, qty, unit_price, tax_rate, line_total)
            )
        db_connection.commit()
        invoice_no = f"INV-{bill_date.year}-{bill_id:06d}"
        print_receipt(cursor, bill_id, invoice_no)
        print(f'\nBill ID: {bill_id}')
        print(f'Invoice No: {invoice_no}')
        print(f'Customer ID: {cust_id}')
        print(f'Total Before GST: {final_p}')
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

def print_receipt(cursor, bill_id, invoice_no):
    try:
        cursor.execute("""
            SELECT b.bill_no, b.bill_date, b.total_price, b.gst, c.name, c.phone_no, c.address
            FROM Bills b
            INNER JOIN Cust_info c ON c.cust_id = b.cust_id
            WHERE b.bill_no = %s
        """, (bill_id,))
        bill = cursor.fetchone()
        cursor.execute("""
            SELECT bi.p_id, s.name, bi.quantity, bi.unit_price, bi.tax_rate, bi.line_total
            FROM BillItems bi INNER JOIN Stock s ON s.p_id = bi.p_id
            WHERE bi.bill_no = %s
        """, (bill_id,))
        items = cursor.fetchall()
        os.makedirs('receipts', exist_ok=True)
        file_path = os.path.join('receipts', f'{invoice_no}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("GROCERY SHOP RECEIPT\n")
            f.write(f"Invoice: {invoice_no}\n")
            f.write(f"Date: {bill[1]}\n")
            f.write(f"Customer: {bill[4]}  Phone: {bill[5]}\n")
            f.write("\nItems:\n")
            f.write(f"{'P_ID':<8}{'Name':<20}{'Qty':<6}{'Price':<10}{'Tax%':<6}{'Line':<10}\n")
            for p_id, name, qty, price, tax_rate, line_total in items:
                f.write(f"{p_id:<8}{name:<20}{qty:<6}{price:<10}{tax_rate:<6}{line_total:<10}\n")
            f.write("\n")
            f.write(f"Subtotal: {bill[2]}\n")
            f.write(f"GST: {bill[3]}\n")
            f.write(f"Grand Total: {(bill[2] + bill[3])}\n")
        print(f"Receipt saved to {file_path}")
    except Exception as e:
        print(f"Error printing receipt: {e}")
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
        print("Main Menu")
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