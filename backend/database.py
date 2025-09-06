
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Thay đổi thông tin kết nối bên dưới cho phù hợp với PostgreSQL của bạn
# Ví dụ: postgresql://username:password@localhost:5432/dbname
SQLALCHEMY_DATABASE_URL = "postgresql://mbadmin:mbadmin123@34.16.74.45:5432/mbdb"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
