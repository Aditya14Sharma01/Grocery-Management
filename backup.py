import os
import datetime
import subprocess

def main():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'project_cs')
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('backups', exist_ok=True)
    out_file = os.path.join('backups', f'{db_name}_{ts}.sql')
    cmd = [
        'mysqldump',
        f'-h{db_host}',
        f'-u{db_user}',
        f'-p{db_password}',
        db_name
    ]
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            subprocess.run(cmd, check=True, stdout=f)
        print(f'Backup saved to {out_file}')
    except Exception as e:
        print(f'Backup failed: {e}')

if __name__ == '__main__':
    main()


