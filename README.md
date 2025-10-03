# Grocery-Management

Requirements:

- Python 3.10+
- MySQL Server 8+
- pip install -r requirements.txt

Environment (.env):

- DB_HOST=localhost
- DB_USER=root
- DB_PASSWORD=your_password
- DB_NAME=project_cs

First run:

1. Start MySQL.
2. Create database `project_cs` (or set DB_NAME accordingly).
3. Run `python project_CS.py` and create the owner account when prompted.
4. Login as owner to manage users and stock.

Backups (Windows Task Scheduler):

- Create `backup.bat` that calls `python backup.py` daily.
