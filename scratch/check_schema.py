import sqlite3

def check():
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    print("=== Scarichi Table Info ===")
    cursor.execute("PRAGMA table_info(Scarichi)")
    for col in cursor.fetchall():
        print(col)
        
    print("\n=== Sample Scarichi Row ===")
    cursor.execute("SELECT * FROM Scarichi LIMIT 2")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == '__main__':
    check()
