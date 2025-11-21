import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Переменная окружения DATABASE_URL не задана!")

Engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    money = Column(Integer, default=100)
    
    inventory = relationship("InventoryItem", back_populates="owner") 
    
    def __repr__(self):
        return f"<Player(id={self.id}, tg_id={self.telegram_id}, money={self.money})>"

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    item_name = Column(String)
    item_level = Column(Integer, default=1)
    
    owner = relationship("Player", back_populates="inventory")
    
    def to_dict(self):
        return {
            "name": self.item_name,
            "level": self.item_level
        }

def init_db():
    Base.metadata.create_all(bind=Engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
