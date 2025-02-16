import os
from typing import Annotated, Any, Dict, Union

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Float, String
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Load environment variables
load_dotenv()

# Load environment variables from .env file (only in development)
if os.getenv('ENVIRONMENT') != 'production':
    load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

#@app.on_event("startup")
#def on_startup():
    #create_db_and_tables()

# Pydantic schema for validation
class ItemSchema(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

# Database model using JSON
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    data: Dict[str, Any] = Field(default={}, sa_type=JSON)

@app.get("/")
def read_root():
    return {"Hello": "API"}

@app.get("/items/{item_id}")
def read_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, **item.data}

@app.post("/items/")
async def create_item(item_schema: ItemSchema, session: SessionDep):
    # Create Item with validated data as JSON
    item = Item(data=item_schema.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"id": item.id, **item.data}

@app.put("/items/{item_id}")
def update_item(item_id: int, item_schema: ItemSchema, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update JSON data
    item.data = item_schema.model_dump()
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"id": item.id, **item.data}