import sqlite3
import os
from ccba_legal.harness import HarnessGuard

def test_sqlite_bypass():
    print("Starting sqlite bypass test...")
    db_path = "secret_credential.db"
    
    # Clean up from previous run if any
    if os.path.exists(db_path):
        os.remove(db_path)
        
    # Create the sensitive DB
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content')")
    conn.commit()
    conn.close()

    # Reconstruct 'secret_credential.db' using char():
    # 's'=115, 'e'=101, 'c'=99, 'r'=114, 'e'=101, 't'=116, '_'=95, 'c'=99, 'r'=114, 'e'=101, 'd'=100, 'e'=101, 'n'=110, 't'=116, 'i'=105, 'a'=97, 'l'=108, '.'=46, 'd'=100, 'b'=98
    chars = [115, 101, 99, 114, 101, 116, 95, 99, 114, 101, 100, 101, 110, 116, 105, 97, 108, 46, 100, 98]
    char_expr = " || ".join(f"char({c})" for c in chars)
    
    sql_attach = f"ATTACH DATABASE ({char_expr}) AS subdb"
    print("SQL command:", sql_attach)
    
    with HarnessGuard():
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute(sql_attach)
            print("ATTACH Succeeded!")
            # Verify we can read from it
            cursor = conn.execute("SELECT * FROM subdb.secrets")
            print("SUCCESS: Read database content:", cursor.fetchall())
            conn.close()
        except PermissionError as e:
            print("FAILED: PermissionError raised:", e)
        except Exception as e:
            print("FAILED: Unexpected error:", e)

    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_sqlite_bypass()
