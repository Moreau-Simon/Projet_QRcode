from flask import Flask, request, jsonify
from pyzbar.pyzbar import decode
import cv2
import numpy as np

app = Flask(__name__)

def rotate_image(image, angle):
    """Fait pivoter l'image selon un angle donné."""
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    # Calculer la matrice de rotation
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Appliquer la rotation
    return cv2.warpAffine(image, M, (w, h))

@app.route("/scan", methods=["POST"])
def scan_barcode():
    try:
        # Vérifier si un fichier est présent dans la requête
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Aucun fichier envoyé"}), 400
            
        file = request.files['file']
        
        # Lire les données de l'image
        contents = file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({"status": "error", "message": "Format d'image invalide."}), 400

        # 1. Passage en niveaux de gris pour faciliter la détection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. Amélioration du contraste
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)

        # 3. Essayer de lire le code sous différents angles
        for angle in range(0, 180, 15):
            rotated = rotate_image(gray, angle)
            barcodes = decode(rotated)
            
            if barcodes:
                barcode_data = barcodes[0].data.decode('utf-8')
                barcode_type = barcodes[0].type
                
                return jsonify({
                    "status": "success", 
                    "data": barcode_data, 
                    "type": barcode_type,
                    "angle_detecte": angle
                }), 200

        # Si aucun code n'est trouvé
        return jsonify({"status": "error", "message": "Aucun code-barres détecté sur l'image."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Flask tourne par défaut sur le port 5000
    app.run(host="0.0.0.0", port=5000)