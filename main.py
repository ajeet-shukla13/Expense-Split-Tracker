from fastapi import FastAPI
from app.routers import users, groups 

app = FastAPI()

app.include_router(users.router) 
app.include_router(groups.router)
