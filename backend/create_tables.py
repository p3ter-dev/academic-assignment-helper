from database import engine
from models import Base

print("creating database tables...")
Base.metadata.create_all(bind=engine)
print("tables created successfully!")
