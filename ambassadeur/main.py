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
        # 1. Envoi de l'image au Job Python (analyse / décodage)
        job_response = requests.post(JOB_URL, files=files, timeout=TIMEOUT)
        result = job_response.json()

        if result.get("status") != "success":
            # Aucun code trouvé : réponse 200 pour que l'IHM continue sa boucle de capture
            return jsonify({"code": None, "error": result.get("message")}), 200

        code_lu = result.get("data")

        # 2. Envoi de la valeur lue au Dataware C# (Redis + PostgreSQL)
        data_response = requests.post(DATA_URL, json={"valeur": code_lu}, timeout=TIMEOUT)

        return jsonify({
            "code": code_lu,
            "type": result.get("type"),
            "status": "success",
            "database_info": data_response.json(),
        }), 200

    except requests.exceptions.RequestException as e:
        # Un des services (Job ou DATA) est injoignable
        return jsonify({"code": None, "error": f"Service injoignable : {e}"}), 502
    except Exception as e:
        return jsonify({"code": None, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)