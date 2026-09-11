from db import get_connection, init_db, save_resume

def seed_data():
    init_db()
    save_resume("sample_resume.txt", "Sample Name\nExperience: 5 years Python", {"name": "Sample Name", "skills": ["Python"]})

if __name__ == "__main__":
    seed_data()
    print("Seeded")