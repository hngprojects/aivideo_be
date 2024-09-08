from faker import Faker
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.blog import Blog
import random

# Initialize Faker
fake = Faker()

def generate_fake_blog():
    return {
        "title": fake.sentence(nb_words=6),
        "content": fake.text(max_nb_chars=200),
        "image_url": fake.image_url(),
        "cover_image_url": fake.image_url(),
        "is_deleted": False,
        "category": fake.word()
    }

def populate_database(db: Session, num_entries: int):
    for _ in range(num_entries):
        fake_blog = generate_fake_blog()
        db_blog = Blog(**fake_blog)
        db.add(db_blog)
    db.commit()

def main():
    db = next(get_db())

    try:
        populate_database(db, num_entries=100)  # Generate 100 fake blogs
        print("Database populated with fake blogs.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
