from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional
class CreateUserRequest(BaseModel):
    email_id:EmailStr
    password:str
    contact_no:str
    profile_image:str

class CreateUserResponse(BaseModel):
    id:UUID

class GetUserRequest(BaseModel):
    ...

class GetUserResponse(BaseModel):
    id:UUID
    email_id:Optional[str]
    contact_no:Optional[str]
    profile_image:str


class UpdateUserRequest(BaseModel):
    email_id:EmailStr
    contact_no:str
    profile_image:str

class UpdateUserResponse(BaseModel):
    ...
class DelteUserRequest(BaseModel):
    ...
class DeleteUserResponse(BaseModel):
    ...