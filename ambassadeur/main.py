from fastapi import FastAPI, File, UploadFile
import requests

app = FastAPI()

@app.post("/api/scan")
async def route_scan(file: UploadFile = File(...)):
    file_bytes = await file.read()
    files = {'file': (file.filename, file_bytes, file.content_type)}
    
    try:
        # Appel vers le conteneur Job Python (Flask sur le port 5000)
        response = requests.post("http://job-python:5000/scan", files=files)
        result = response.json()
        
        # Adaptation au format de réponse de votre script Flask
        if result.get("status") == "success":
            code_lu = result.get("data")
            
            # (Plus tard) Appel vers l'API C# :
            # requests.post("http://data-csharp:5000/api/save", json={"valeur": code_lu})
            
            return {"code": code_lu, "status": "success"}
        else:
            return {"code": None, "error": result.get("message")}
            
    except Exception as e:
        return {"code": None, "error": str(e)}
