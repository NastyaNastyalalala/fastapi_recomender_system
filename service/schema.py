from pydantic import BaseModel

#data validation through models (BaseModel from pydantic)
class PostGet(BaseModel):
	id: int
	text: str
	topic: str

	class Config:
		orm_mode = True