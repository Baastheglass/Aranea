import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from agent import Agent

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()
    
@app.post("/generate")
async def generate_content(query: str = Body(..., embed=True)):
    response = agent.generate(query)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)