from db import get_connection, init_db

def seed_data():
    conn = init_db()
    cursor = conn.cursor()
    # add demo rows here tomorrow before evaluation
    cursor.execute("INSERT INTO items (name) VALUES (?)", ("example",))
    conn.commit()

if __name__ == "__main__":
    seed_data()
    print("Seeded")