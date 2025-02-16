"""convert_to_json_storage

Revision ID: 57731470966c
Revises: 549a1e94aa4f
Create Date: 2025-02-16 20:35:42.854851

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = '57731470966c'
down_revision: Union[str, None] = '549a1e94aa4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Create Base for the old model
Base = declarative_base()

# Define the old model structure
class OldItem(Base):
    __tablename__ = 'item'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255))
    price = sa.Column(sa.Float)
    is_offer = sa.Column(sa.Boolean)

def upgrade() -> None:
    # Add the new JSON column first
    op.add_column('item', sa.Column('data', sa.JSON(), nullable=True))
    
    # Get bind and create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Convert existing data to JSON format
        for item in session.query(OldItem).all():
            data = json.dumps({
                'name': item.name,
                'price': float(item.price) if item.price is not None else None,
                'is_offer': bool(item.is_offer) if item.is_offer is not None else None
            })
            # Update the data column with serialized JSON
            session.execute(
                sa.text('UPDATE item SET data = :data WHERE id = :id'),
                {'data': data, 'id': item.id}
            )
        
        session.commit()
        
        # Now make the data column non-nullable
        op.alter_column('item', 'data',
                       existing_type=sa.JSON(),
                       nullable=False)
        
        # Drop old columns
        op.drop_index('ix_item_name', table_name='item')
        op.drop_column('item', 'price')
        op.drop_column('item', 'is_offer')
        op.drop_column('item', 'name')
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def downgrade() -> None:
    # Add back the old columns
    op.add_column('item', sa.Column('name', sa.VARCHAR(length=255), nullable=True))
    op.add_column('item', sa.Column('is_offer', sa.BOOLEAN(), nullable=True))
    op.add_column('item', sa.Column('price', sa.DOUBLE_PRECISION(precision=53), nullable=True))
    
    # Get bind and create session
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Convert JSON data back to columns
        session.execute(
            sa.text('''
                UPDATE item 
                SET name = data->>'name',
                    price = (data->>'price')::float,
                    is_offer = (data->>'is_offer')::boolean
            ''')
        )
        
        session.commit()
        
        # Make columns non-nullable where needed
        op.alter_column('item', 'name', nullable=False)
        op.alter_column('item', 'price', nullable=False)
        
        # Recreate index
        op.create_index('ix_item_name', 'item', ['name'], unique=False)
        
        # Finally drop the JSON column
        op.drop_column('item', 'data')
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
