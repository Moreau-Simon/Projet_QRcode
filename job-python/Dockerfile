# Utiliser une image Python officielle légère
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système requises pour OpenCV et Pyzbar
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY main.py .

# Exposer le port interne du Job (Flask utilise 5000 par défaut)
EXPOSE 5000

# Commande pour démarrer Flask
CMD ["python", "main.py"]