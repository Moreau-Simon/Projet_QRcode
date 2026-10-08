FROM python:3.11-slim
WORKDIR /app
# Crée un fichier requirements.txt factice pour l'instant (à remplir plus tard avec fastapi, uvicorn, requests...)
RUN echo "fastapi\nuvicorn\nrequests" > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Script d'attente/test basique
RUN echo 'print("Ambassadeur Python prêt à router !")' > main.py
EXPOSE 8000
# Commande par défaut (à remplacer par uvicorn main:app --host 0.0.0.0 --port 8000 quand le code sera prêt)
CMD ["tail", "-f", "/dev/null"] 
