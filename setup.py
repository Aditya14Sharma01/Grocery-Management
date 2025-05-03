import mysql.connector as sql
import time as t
def insert_sample_data(cursor, db_connection):
    sample_data = [
        (1, 'Rice', 50, 100, 'BestRice', 'GrainSupply Co.'),
        (2, 'Wheat Flour', 30, 200, 'GoldenGrain', 'FarmFresh Ltd.'),
        (3, 'Sugar', 40, 150, 'SweetSugar', 'Sweetness Inc.'),
        (4, 'Cooking Oil', 150, 50, 'HealthyOil', 'OilMart Supplies'),
        (5, 'Salt', 10, 300, 'PureSalt', 'MineralSuppliers'),
        (6, 'Spices Pack', 200, 40, 'SpiceKing', 'SpiceHouse'),
        (7, 'Tea', 250, 70, 'BrewBest', 'TeaTime Ltd.'),
        (8, 'Coffee', 300, 30, 'MorningJoy', 'CoffeeCo'),
        (9, 'Lentils', 80, 120, 'NutriLentils', 'PulseWorld'),
        (10, 'Biscuits', 20, 200, 'CrunchyBites', 'SnackMart'),
        (11, 'Bread', 25, 50, 'DailyBread', 'BakeryFresh'),
        (12, 'Butter', 60, 80, 'CreamyButter', 'DairyBest'),
        (13, 'Milk', 45, 150, 'FarmFresh Milk', 'DairyWorld'),
        (14, 'Eggs', 5, 500, 'HealthyEggs', 'EggSuppliers'),
        (15, 'Cheese', 150, 60, 'CheeseDelight', 'DairyBest')
    ]
    
    profit_data = [
        (1, 10),
        (2, 8),
        (3, 12),
        (4, 30),
        (5, 3),
        (6, 40),
        (7, 50),
        (8, 60),
        (9, 15),
        (10, 5),
        (11, 5),
        (12, 10),
        (13, 9),
        (14, 2),
        (15, 20)
    ]

    try:
        cursor.executemany("""
            INSERT INTO Stock (p_id, name, price, quantity, brand, supplier)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, sample_data)
        
        cursor.executemany("""
            INSERT INTO Profits (p_id, profit)
            VALUES (%s, %s)
        """, profit_data)
        
        db_connection.commit()
        print("Sample data inserted into 'Stock' and 'Profits' tables.")
    except sql.Error as e:
        print(f"Error inserting sample data: {e}")
        db_connection.rollback()

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
                FOREIGN KEY (cust_id) REFERENCES Cust_info(cust_id))""")
        print("Tables created successfully.")
    except sql.Error as e:
        print(f"Error creating tables: {e}")

def main():
    db_connection, cursor = connect_to_database()
    if db_connection is not None and cursor is not None:
        create_tables(cursor)
        insert_sample_data(cursor, db_connection)
        cursor.close()
        db_connection.close()

if __name__ == "__main__":
    main()
