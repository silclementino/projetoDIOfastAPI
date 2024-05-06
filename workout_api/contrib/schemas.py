from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, UUID4, Field

class BaseSchema(BaseModel):
    class Config:
        extra = 'forbid'
        from_attributes = True

class OutMixin(BaseModel):
    id: Annotated[UUID4, Field(description='Identificador')]
    created_at: Annotated[datetime, Field(description='data de criaçao')]