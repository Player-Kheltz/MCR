from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Modelo de dados para itens
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

# In-memory database simulation
items_db = {}

@app.post("/items/")
async def create_item(item: Item):
    if item.name in items_db:
        raise HTTPException(status_code=400, detail="Item already exists")
    items_db[item.name] = item
    return item

@app.get("/items/{item_name}")
async def read_item(item_name: str):
    item = items_db.get(item_name)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_name}")
async def update_item(item_name: str, item: Item):
    if item_name not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_name] = item
    return item

@app.delete("/items/{item_name}")
async def delete_item(item_name: str):
    if item_name not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_name]
    return {"detail": "Item deleted"}