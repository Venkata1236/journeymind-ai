from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "JourneyMind AI API running"}

def main():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
