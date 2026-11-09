from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

JOB_URL = "http://job-python:5000/scan"
DATA_URL = "http://data-csharp:5000/api/save"
TIMEOUT = 30  # secondes


@app.route("/api/scan", methods=["POST"])
def route_scan():
    # Vérifier la présence du fichier envoyé par l'IHM
    if "file" not in request.files:
        return jsonify({"code": None, "error": "Aucun fichier envoyé"}), 400

    file = request.files["file"]
    files = {"file": (file.filename, file.read(), file.content_type)}

    try:
        # 1. Étape 1 du Pipeline : Envoi de l'image au Job Python pour décodage et analyse
        job_response = requests.post(JOB_URL, files=files, timeout=TIMEOUT)
        result = job_response.json()

        if result.get("status") != "success":
            # Aucun code trouvé : renvoyer 200 avec code: None pour que l'IHM continue sa boucle caméra
            return jsonify({"code": None, "error": result.get("message")}), 200

        code_lu = result.get("data")
        code_type = result.get("type")
        analyse = result.get("analyse", {})

        # 2. Étape 2 du Pipeline : Routage selon le type de code détecté
        # Le scan d'un QR-Code renvoie les données vers la base associée (via Dataware C#).
        # Pour un code-barre, l'analyse a été effectuée par le Job Python, et on l'archive également dans la base.
        database_info = None
        try:
            data_response = requests.post(
                DATA_URL, 
                json={"valeur": code_lu}, 
                timeout=TIMEOUT
            )
            if data_response.ok:
                database_info = data_response.json()
            else:
                database_info = {"status": "error", "message": f"Erreur DATA: {data_response.status_code}"}
        except requests.exceptions.RequestException as e:
            database_info = {"status": "warning", "message": f"Service DATA temporairement injoignable: {e}"}

        # 3. Réponse finale renvoyée à l'IHM
        return jsonify({
            "status": "success",
            "code": code_lu,
            "type": code_type,
            "angle_detecte": result.get("angle_detecte"),
            "analyse": analyse,
            "database_info": database_info,
        }), 200

    except requests.exceptions.RequestException as e:
        # Service Job ou DATA injoignable
        return jsonify({"code": None, "error": f"Service injoignable : {e}"}), 502
    except Exception as e:
        return jsonify({"code": None, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
