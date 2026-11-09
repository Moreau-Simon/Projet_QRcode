# Projet_QRcode

Application conteneurisée basée sur une architecture micro-services en pipeline, permettant la détection robuste, l'analyse approfondie et la persistance de **QR codes** et **codes-barres** à partir d'un flux vidéo ou d'images fixes (même inclinées).

---

## Architecture du Projet

Le système est entièrement encapsulé dans une stack Docker orchestrée par `docker-compose`. La stack respecte une politique stricte d'isolation réseau : **seul le port 8080 est exposé sur la machine hôte**, servant de point d'entrée unique via l'IHM.

```mermaid
flowchart TD
    subgraph Host ["Machine Hôte / Navigateur"]
        Client["Utilisateur / Navigateur"]
    end

    subgraph DockerStack ["Stack Docker (Réseau interne)"]
        direction TB

        subgraph S_IHM ["1. IHM (Nginx / React 18)"]
            IHM["Nginx:80 (Exposé sur l'hôte :8080)<br/>Interface Web & Reverse Proxy"]
        end

        subgraph S_AMB ["2. Routeur (Python 3.11 Flask)"]
            AMB["Ambassadeur:8000<br/>Orchestration & Distribution"]
        end

        subgraph S_JOB ["3. Traitement Image & Analyse (Python 3.11)"]
            JOB["Job-Python:5000<br/>OpenCV + Pyzbar<br/>Rotation dynamique & Analyse code-barre"]
        end

        subgraph S_DATA ["4. Dataware (C# ASP.NET Core 8)"]
            DATA["Data-CSharp:5000<br/>Gestion persistance & Cache"]
        end

        subgraph S_CACHE ["5. Cache mémoire"]
            REDIS[("Redis:6379<br/>Cache TTL 1h")]
        end

        subgraph S_DB ["6. Base de données relationnelle"]
            PSQL[("PostgreSQL 15:5432<br/>Volume persistant pgdata")]
        end
    end

    Client -- "HTTP Port 8080" --> IHM
    IHM -- "proxy_pass /api/ -> :8000" --> AMB
    AMB -- "POST /scan (multipart image)" --> JOB
    JOB -- "JSON {code, type, angle, analyse}" --> AMB
    AMB -- "POST /api/save {valeur}" --> DATA
    DATA <--> REDIS
    DATA <--> PSQL
    AMB -- "Réponse consolidée JSON" --> IHM
    IHM -- "Affichage résultat" --> Client
```

---

## Détail des Micro-services et Composants

| Service | Technologie | Rôle & Responsabilité | Port interne | Port hôte |
| :--- | :--- | :--- | :--- | :--- |
| **IHM** | Nginx Alpine, React 18, CSS moderne | Interface utilisateur (webcam en temps réel ou upload d'image) et reverse proxy vers l'Ambassadeur. | 80 | **8080** |
| **Ambassadeur** | Python 3.11, Flask, Requests | Routeur / Orchestrateur interne. Reçoit le scan de l'IHM, interroge le Job d'analyse, puis achemine les résultats au Dataware C#. | 8000 | *Aucun* |
| **Job Python** | Python 3.11, OpenCV headless, Pyzbar | Traitement d'image : prétraitement (niveaux de gris, contraste), rotation dynamique multi-angles (0° à 180°), décodage et analyse approfondie des codes-barres. | 5000 | *Aucun* |
| **DATA C#** | C# .NET 8 (ASP.NET Core Minimal API) | Datawarehouse d'accès aux données. Gère les opérations de lecture/écriture avec stratégie de cache-aside. | 5000 | *Aucun* |
| **Redis** | Redis 7 Alpine | Cache en mémoire pour accélérer les requêtes fréquentes et réduire la charge SQL. | 6379 | *Aucun* |
| **PostgreSQL** | PostgreSQL 15 Alpine | Stockage relationnel persistant des codes scannés, du compteur d'occurrences et de l'horodatage. | 5432 | *Aucun* |

---

## Fonctionnalités Clés

1. **Point d'entrée unique sécurisé (Port 8080) :**
   Tous les services internes (Python, C#, Redis, PostgreSQL) sont isolés sur le réseau Docker privé. Seule l'IHM Nginx est accessible depuis l'extérieur, redirigeant les requêtes `/api/*` vers l'Ambassadeur.

2. **Lecture multi-angles par rotation dynamique :**
   Les codes-barres physiques photographiés ou scannés de travers sont souvent indétectables pour les bibliothèques standards. Le **Job Python** teste automatiquement des rotations de l'image de 0° à 180° par pas de 15°, garantissant la lecture quel que soit l'angle d'inclinaison.

3. **Analyse Python approfondie des codes-barres :**
   - **EAN-13** : Validation de la clé de contrôle (algorithme modulo 10) et détection du pays d'origine via le préfixe GS1 (ex. 300-379 : France, 400-440 : Allemagne, etc.).
   - **Code 39 / Code 128** : Validation du format alphanumérique et identification du type d'usage (inventaire industriel, logistique).

4. **Persistance et mise en cache à double niveau :**
   - Chaque scan incrémente le compteur `scan_count` dans **PostgreSQL** et met à jour la date `last_scan`.
   - Le résultat est automatiquement mis en cache dans **Redis** avec une durée de vie (TTL) d'une heure.
   - Les requêtes de consultation (`GET /api/scan/{valeur}`) interrogent d'abord Redis et ne sollicitent PostgreSQL qu'en cas de cache-miss.

---

## Arborescence du Projet

```text
Projet_QRcode/
├── ambassadeur/
│   ├── Dockerfile             # Image Python slim pour le routeur
│   ├── main.py                # Pipeline d'orchestration Flask
│   └── requirements.txt       # Flask, requests
├── data-csharp/
│   ├── Dockerfile             # Multi-stage build .NET 8 SDK -> ASP.NET Runtime
│   ├── DataService.csproj     # Dépendances Npgsql et StackExchange.Redis
│   └── Program.cs             # Minimal API C#, mapping PostgreSQL et Redis
├── ihm/
│   ├── Dockerfile             # Image Nginx Alpine
│   ├── index.html             # Application React 18 (Modes Caméra et Image)
│   ├── nginx.conf             # Configuration proxy_pass et fichiers statiques
│   └── style.css              # Feuille de style responsive
├── job-python/
│   ├── Dockerfile             # Python slim avec libzbar0 et libglib2.0
│   ├── main.py                # Décodage OpenCV/Pyzbar et analyse code-barre
│   └── requirements.txt       # Flask, pyzbar, opencv-python-headless, numpy
├── picture/                   # Images d'exemples et de tests
│   ├── code-barre_PC-UPJV_67430(1).jpg
│   └── code-barre_PC-UPJV_67430(2).jpg
├── docker-compose.yml         # Définition et orchestration de la stack
└── README.md                  # Documentation du projet
```

---

## Installation et Lancement

### Prérequis
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré.
* [Git](https://git-scm.com/) pour cloner le projet.

### 1. Démarrage de la stack
À la racine du projet, lancez la construction et le démarrage de l'ensemble des conteneurs :

```bash
docker-compose up --build -d
```
*(ou `docker compose up --build -d` selon votre version de Docker)*

### 2. Vérification de l'état des conteneurs
Assurez-vous que tous les services sont actifs et sains (`healthy`) :

```bash
docker-compose ps
```

---

## Utilisation & Tests

Une fois la stack démarrée, ouvrez votre navigateur web à l'adresse :
**[http://localhost:8080](http://localhost:8080)**

Deux modes d'utilisation sont proposés :
* **Mode Caméra :** Active votre webcam pour analyser le flux vidéo en continu toutes les 1,5 secondes.
  *(Fonctionne sur `localhost` ; les navigateurs bloquent la caméra sans HTTPS sur une IP distante)*.
* **Mode Image :** Permet de téléverser une image fixe (JPG, PNG, WEBP).
  Vous pouvez tester immédiatement ce mode avec les images fournies dans le dossier `picture/` (ex. `code-barre_PC-UPJV_67430(1).jpg` qui est décodé grâce à une rotation à 30°).

---

## Endpoints de l'API

Tous les appels transitent par le port **8080** via le reverse proxy Nginx :

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/scan` | Envoie un fichier image (`multipart/form-data`) pour analyse par le pipeline complet. |
| `GET` | `/api/scan/{valeur}` | Interroge l'historique et le nombre de scans d'un code (interroge Redis d'abord, puis PostgreSQL). |

---

## Commandes Utiles de Maintenance

* **Afficher les logs en temps réel d'un service précis :**
  ```bash
  docker-compose logs -f ambassadeur
  docker-compose logs -f job-python
  docker-compose logs -f data-csharp
  ```

* **Arrêter la stack sans perdre les données de la base :**
  ```bash
  docker-compose down
  ```

* **Arrêter la stack et réinitialiser complètement la base de données (suppression du volume) :**
  ```bash
  docker-compose down -v
  ```

* **Accéder au terminal interactif d'un conteneur :**
  ```bash
  docker-compose exec ihm sh
  docker-compose exec psql psql -U mon_utilisateur -d ma_base_de_donnees
  ```
