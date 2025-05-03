import mysql.connector as sql
from datetime import date
import time as t
def create_tables(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stock (
                p_id INT PRIMARY KEY, 
                name VARCHAR(100) NOT NULL,
                price INT NOT NULL, 
                quantity INT,
                brand VARCHAR(100),
                supplier VARCHAR(100))""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Profits (
                p_id INT PRIMARY KEY,
                profit INT,
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
                total_price INT,
                gst INT,
                FOREIGN KEY (cust_id) REFERENCES Cust_info(cust_id))""")
        print("Tables 'Stock', 'Profits', 'Cust_info', and 'Bills' created or already exist.")
    except sql.Error as e:
        print(f"Error creating tables: {e}")
def connect_to_database():
    try:
        mydb = sql.connect(host='localhost', user='root', password='1401', database='project_cs', charset='utf8')
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
def admin_privileges(cursor, db_connection):
    password = input("Enter admin password: ")
    if password == "1234":
        while True:
            print("Admin Privileges")
            print("4. Check Stock")
            print("5. Check Customer Info")
            print("6. Update Customer Info")
            print("7. Insert New Product")
            print("8. Check Reorder Level")
            print("9. Check Total GST")
            print("10. Check Total Profits")
            print("e. Exit Admin Privileges")
            choice = str(input("Enter your choice: "))
            if choice == '3':
                create_tables(cursor)
            elif choice == '4':
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
            elif choice.lower() in ('e','exit'):
                break
            else:
                print("Invalid choice. Please select a valid option.")
    else:
        print("Incorrect password")
def genrate():
    import base64
    info = [base64.b64decode(data).decode('utf-8') for data in ['QWRpdHlhIFNoYXJtYQ==', 'UHVsa2l0IEFnZ2Fyd2Fs']]
    print(info)
def check_total_profits(cursor):
    print("Checking Total Profits")
    try:
        cursor.execute("""
            SELECT SUM(p.price * p.quantity) AS total_sales, SUM(pr.profit * p.quantity) AS total_profits
            FROM Stock p
            LEFT JOIN Profits pr ON p.p_id = pr.p_id
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
def bill(cursor, db_connection):
    print("Making Bills")
    try:
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
        final_p = 0
        total_profit = 0
        while True:
            try:
                cursor.execute("""
                    SELECT Stock.p_id, Stock.name, Stock.price, Stock.quantity, Stock.brand, Stock.supplier
                    FROM Stock
                """)
                result = cursor.fetchall()
                print(f"{'P_ID':<10} {'Name':<20} {'Price':<10} {'Quantity':<10} {'Brand':<20} {'Supplier':<20}")
                print("=" * 90)
                for rec in result:
                    p_id, name, price, quantity, brand, supplier= rec
                    print(f"{p_id:<10} {name:<20} {price:<10} {quantity:<10} {brand:<20} {supplier:<20}")
            except sql.Error as e:
                print(f"Error fetching stock details: {e}")
            prod_id = input("Enter product ID (press 'e' or 'exit' to finalize bill): ")
            if prod_id.lower() in ('e', 'exit'):
                break
            elif prod_id.isdigit():
                quantity = int(input("Enter quantity: "))
                if quantity <= 0:
                    print("Quantity must be greater than zero.")
                    continue
                select_query = """
                    SELECT price, quantity FROM Stock WHERE p_id = %s
                """
                cursor.execute(select_query, (prod_id,))
                result = cursor.fetchone()
                if result:
                    price, stock_quantity = result
                    if quantity <= stock_quantity:
                        total_price = price * quantity
                        cursor.execute("SELECT profit FROM Profits WHERE p_id = %s", (prod_id,))
                        profit = cursor.fetchone()[0]
                        item_profit = profit * quantity
                        final_p += total_price
                        total_profit += item_profit
                        new_quantity = stock_quantity - quantity
                        update_stock_query = "UPDATE Stock SET quantity = %s WHERE p_id = %s"
                        cursor.execute(update_stock_query, (new_quantity, prod_id))
                        db_connection.commit()
                        print(f"Added {quantity} items to bill. Total: {total_price}")
                    else:
                        print("Insufficient stock.")
                else:
                    print("Product not found.")
            else:
                print("Invalid product ID.")
        gst = int(final_p * 0.18)
        grand_total = final_p + gst
        bill_date = date.today()
        insert_bill_query = """
            INSERT INTO Bills (cust_id, bill_date, total_price, gst)
            VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_bill_query, (cust_id, bill_date, final_p, gst))
        db_connection.commit()
        bill_id = cursor.lastrowid
        print(f'\nBill ID: {bill_id}')
        print(f'Customer ID: {cust_id}')
        print(f'Total Before GST: {final_p}')
        print(f'Applied GST: {gst}')
        print(f'Total After GST: {grand_total}')
        print(f'Bill Date: {bill_date}')
    except sql.Error as e:
        print(f"Error processing bill: {e}")
    except ValueError as ve:
        print(f"Invalid input: {ve}")
def main():
    db_connection, cursor = connect_to_database()
    if not db_connection or not cursor:
        return
    while True:
        print("Main Menu")
        print("1. Generate Bill")
        print("2. Admin Privileges")
        print("e. Exit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            bill(cursor, db_connection)
        elif choice == '2':
            admin_privileges(cursor, db_connection)
        elif choice in ('e', 'exit'):
            genrate()
            print("Exiting...")
            db_connection.close()
            break
        else:
            print("Incorrect Command.")
if __name__ == "__main__":
    main()