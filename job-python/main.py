from flask import Flask, request, jsonify
from pyzbar.pyzbar import decode
import cv2
import numpy as np

app = Flask(__name__)

def rotate_image(image, angle):
    """Fait pivoter l'image selon un angle donné."""
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h))

def analyser_code_barre(barcode_data: str, barcode_type: str) -> dict:
    """Analyse approfondie d'un code-barres (validité, format, métadonnées)."""
    analyse = {
        "symbologie": barcode_type,
        "longueur": len(barcode_data),
        "est_valide": True,
        "details": {}
    }
    
    if barcode_type in ("EAN13", "EAN_13"):
        if len(barcode_data) == 13 and barcode_data.isdigit():
            total = sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(barcode_data[:12]))
            checksum = (10 - (total % 10)) % 10
            cle_fournie = int(barcode_data[12])
            analyse["est_valide"] = (checksum == cle_fournie)
            analyse["details"]["cle_calculee"] = checksum
            analyse["details"]["cle_fournie"] = cle_fournie
            
            prefix = int(barcode_data[:3])
            if 300 <= prefix <= 379:
                analyse["details"]["origine_gs1"] = "France"
            elif 400 <= prefix <= 440:
                analyse["details"]["origine_gs1"] = "Allemagne"
            elif 500 <= prefix <= 509:
                analyse["details"]["origine_gs1"] = "Royaume-Uni"
            elif 0 <= prefix <= 139:
                analyse["details"]["origine_gs1"] = "États-Unis / Canada"
            else:
                analyse["details"]["origine_gs1"] = f"Préfixe GS1 {prefix}"
        else:
            analyse["est_valide"] = False
            analyse["details"]["erreur"] = "Format EAN-13 invalide (doit comporter 13 chiffres)"
            
    elif barcode_type in ("CODE39", "CODE_39"):
        analyse["details"]["type_usage"] = "Inventaire / Matériel industriel"
        analyse["details"]["alphanumerique"] = barcode_data.isalnum()
        
    elif barcode_type in ("CODE128", "CODE_128"):
        analyse["details"]["type_usage"] = "Logistique / Distribution standard"
        
    return analyse

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

        # 3. Essayer de lire le code sous différents angles (rotation dynamique)
        for angle in range(0, 180, 15):
            rotated = rotate_image(gray, angle)
            barcodes = decode(rotated)
            
            if barcodes:
                barcode_data = barcodes[0].data.decode('utf-8')
                barcode_type = barcodes[0].type
                
                # Analyse spécifique si code-barres
                analyse = {}
                if barcode_type != "QRCODE":
                    analyse = analyser_code_barre(barcode_data, barcode_type)
                
                return jsonify({
                    "status": "success", 
                    "data": barcode_data, 
                    "type": barcode_type,
                    "angle_detecte": angle,
                    "analyse": analyse
                }), 200

        # Si aucun code n'est trouvé
        return jsonify({"status": "error", "message": "Aucun code-barres détecté sur l'image."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Flask tourne par défaut sur le port 5000
    app.run(host="0.0.0.0", port=5000)
