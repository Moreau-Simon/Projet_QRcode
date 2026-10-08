# Projet_QRcode

Application conteneurisée basée sur une architecture micro-services, permettant la détection et le décodage robustes de QR codes et codes-barres à partir d'images, avec n'importe quels angles d'inclinaison.


## Architecture du Projet

Le système est entièrement encapsulé dans une stack Docker et communique avec l'extérieur via un point d'entrée unique sur le port 8080. Le pipeline est découpé en plusieurs micro-services interconnectés :

* **IHM (Interface Homme-Machine) :** Point d'entrée utilisateur exposé sur le port 8080.

* **Ambassadeur Python :** Routeur interne qui fait la passerelle entre l'IHM et les services de traitement : il envoie l'image au Job, puis le code lu au service DATA.

* **Job Python :** Micro-service d'analyse d'image (propulsé par Flask) chargé de manipuler (rotation dynamique) et de lire les codes-barres/QR codes.

* **DATA C# :** Micro-service datawarehouse développé en ASP.NET gérant les accès aux informations liées aux codes scannés.

* **Bases de données :** Une instance Redis pour le système de cache et une instance PostgreSQL pour le stockage relationnel.


## Technologies Utilisées

* **Infrastructure :** Docker, Docker Compose
* **IHM :** HTML/CSS, React 18, Nginx
* **Ambassadeur :** Python 3.11, Flask, Requests
* **Job :** Python 3.11, Flask, OpenCV (headless), Pyzbar, Numpy
* **DATA :** C# / .NET 8 (ASP.NET), Npgsql, StackExchange.Redis
* **Bases de données :** PostgreSQL 15, Redis


## Installation et Lancement

### Prérequis

* Docker et Docker Compose (Docker Desktop) installés et en cours d'exécution.
* Git pour cloner le dépôt.
* Une connexion internet : l'interface charge React depuis un CDN et les images Docker sont téléchargées au premier lancement.

### Démarrage de la stack

1. Clonez ce dépôt sur votre machine locale :
```bash
git clone <URL_DU_DEPOT>
cd Projet_QRcode
```

2. Construisez les images et lancez les conteneurs en arrière-plan (le premier build peut prendre quelques minutes) :
```bash
docker compose up --build -d
```

3. Vérifiez que tous les services sont démarrés :
```bash
docker compose ps
```

### Accès à l'application

Une fois la stack lancée, l'interface utilisateur est accessible depuis votre navigateur (sans HTTPS) à l'adresse suivante :
`http://localhost:8080`

Deux modes de lecture sont disponibles : **Caméra** (analyse en continu) et **Image** (envoi d'un fichier).

> **Remarque :** l'accès à la caméra ne fonctionne que depuis `localhost`. Depuis un autre appareil via l'adresse IP, le navigateur la bloque sans HTTPS ; utilisez alors le mode **Image**.

### Commandes utiles

* Consulter les logs d'un service (ex. `data-csharp`) :
```bash
docker compose logs -f data-csharp
```

* Arrêter la stack (les données PostgreSQL sont conservées dans le volume `pgdata`) :
```bash
docker compose down
```

* Arrêter la stack **et supprimer les données** enregistrées :
```bash
docker compose down -v
```
