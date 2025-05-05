import os
import sys
import uvicorn

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now run the app
if __name__ == "__main__":
    print("Starting the Azure RAG Search API...")
    print(f"Python path: {sys.path}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 