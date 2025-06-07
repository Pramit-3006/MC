from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    topics = Column(String)
    approved = Column(Boolean, default=False)
    abstract_uploaded = Column(Boolean, default=False)
    abstract_file = Column(String, nullable=True)
