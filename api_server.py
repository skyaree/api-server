import random
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import init_db, get_db, Player, InventoryItem

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

ROLL_COST = 20
ITEMS = {
    "Меч Новичка": {"rarity": 0.50},
    "Щит Героя": {"rarity": 0.30},
    "Эпический Буст": {"rarity": 0.15},
    "Легендарный Артефакт": {"rarity": 0.05}
}

def get_or_create_player(db: Session, telegram_id: int):
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()
    
    if not player:
        player = Player(telegram_id=telegram_id, money=100)
        db.add(player)
        db.commit()
        db.refresh(player)
    return player

def roll_for_item_logic(db: Session, player: Player):
    
    if player.money < ROLL_COST:
        return {"item": None, "message": "Недостаточно средств."}
        
    player.money -= ROLL_COST
    
    roll = random.random()
    cumulative_rarity = 0
    chosen_item = None
    
    sorted_items = sorted(ITEMS.items(), key=lambda item: item[1]['rarity'], reverse=True)
    
    for name, data in sorted_items:
        cumulative_rarity += data['rarity']
        if roll <= cumulative_rarity:
            chosen_item = name
            break
            
    new_item = InventoryItem(player_id=player.id, item_name=chosen_item, item_level=1)
    db.add(new_item)
    
    db.commit()
    db.refresh(player)
    
    return {"item": chosen_item, "money": player.money}

@app.get("/")
def read_root():
    return {"status": "ok", "service": "RNG Game API"}

@app.get("/player/{telegram_id}")
def get_player_status(telegram_id: int, db: Session = Depends(get_db)):
    player = get_or_create_player(db, telegram_id)
    return {
        "status": "success", 
        "telegram_id": player.telegram_id, 
        "money": player.money
    }

@app.post("/game/roll/{telegram_id}")
def do_roll(telegram_id: int, db: Session = Depends(get_db)):
    player = get_or_create_player(db, telegram_id)
    result = roll_for_item_logic(db, player)
    
    if result.get("item"):
        return {"status": "success", **result}
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))

@app.get("/inventory/{telegram_id}")
def get_inventory(telegram_id: int, db: Session = Depends(get_db)):
    player = get_or_create_player(db, telegram_id)
    
    items_list = db.query(InventoryItem).filter(InventoryItem.player_id == player.id).all()
    
    item_counts = {}
    for item in items_list:
        key = f"{item.item_name} (ур. {item.item_level})"
        item_counts[key] = item_counts.get(key, 0) + 1
        
    formatted_inventory = [{"name": name, "count": count} for name, count in item_counts.items()]
    
    return {
        "status": "success", 
        "money": player.money,
        "inventory": formatted_inventory
    }
