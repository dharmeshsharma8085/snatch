from app.database.database import Base, engine
from app.models.device import Device
# Import all models
from app.models.incident import Incident
from app.models.user import User


def create_tables():
    Base.metadata.create_all(bind=engine)

    print("SNATCH database tables created successfully!")

    print("Registered tables:")
    for table in Base.metadata.sorted_tables:
        print(f"- {table.name}")


if __name__ == "__main__":
    create_tables()