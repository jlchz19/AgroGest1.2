import sqlite3

def add_column():
    conn = sqlite3.connect('instance/finca_ganadera.db')
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(empleado);")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'descripcion' not in columns:
        print("Adding 'descripcion' column to 'empleado' table...")
        cursor.execute("ALTER TABLE empleado ADD COLUMN descripcion TEXT;")
        conn.commit()
        print("Column added successfully.")
    else:
        print("Column 'descripcion' already exists.")
        
    conn.close()

if __name__ == '__main__':
    add_column()
