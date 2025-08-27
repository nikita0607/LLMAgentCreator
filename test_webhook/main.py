from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SquareRequest(BaseModel):
    number: int

class SquareResponse(BaseModel):
    result: int

@app.post("/get-square", response_model=SquareResponse)
def get_square(req: SquareRequest):
    return {"result": req.number * req.number}