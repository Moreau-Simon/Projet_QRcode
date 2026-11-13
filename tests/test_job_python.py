import os
import io
import unittest
import importlib.util
import numpy as np

# Chargement dynamique du module job-python
MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "job-python", "main.py"))
spec = importlib.util.spec_from_file_location("job_main", MODULE_PATH)
job_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job_module)


class TestJobPython(unittest.TestCase):

    def setUp(self):
        self.app = job_module.app.test_client()
        self.app.testing = True

    def test_rotate_image(self):
        """Vérifie que la fonction de rotation conserve les dimensions de l'image."""
        # Création d'une image factice 120x80 pixels, 3 canaux
        dummy_img = np.zeros((120, 80, 3), dtype=np.uint8)
        rotated = job_module.rotate_image(dummy_img, 45)

        self.assertIsNotNone(rotated)
        self.assertEqual(rotated.shape, dummy_img.shape)

    def test_analyser_code_barre_ean13_valide(self):
        """Vérifie le calcul de la clé de contrôle EAN-13 et l'origine GS1 (France)."""
        code = "3017620422003"  # EAN-13 valide (France)
        analyse = job_module.analyser_code_barre(code, "EAN13")

        self.assertTrue(analyse["est_valide"])
        self.assertEqual(analyse["longueur"], 13)
        self.assertEqual(analyse["details"].get("cle_calculee"), 3)
        self.assertEqual(analyse["details"].get("origine_gs1"), "France")

    def test_analyser_code_barre_ean13_invalide(self):
        """Vérifie qu'un code EAN-13 avec une clé erronée est rejeté."""
        code_invalide = "3017620422009"  # Clé attendue: 3, clé fournie: 9
        analyse = job_module.analyser_code_barre(code_invalide, "EAN13")

        self.assertFalse(analyse["est_valide"])

    def test_analyser_code_barre_code39(self):
        """Vérifie la détection et les métadonnées d'un code industriel Code39."""
        code = "PC-UPJV-67430"
        analyse = job_module.analyser_code_barre(code, "CODE39")

        self.assertTrue(analyse["est_valide"])
        self.assertEqual(analyse["symbologie"], "CODE39")
        self.assertIn("Inventaire", analyse["details"].get("type_usage", ""))

    def test_analyser_code_barre_code128(self):
        """Vérifie la catégorisation d'un code logistique Code128."""
        code = "PALETTE-98765"
        analyse = job_module.analyser_code_barre(code, "CODE128")

        self.assertTrue(analyse["est_valide"])
        self.assertIn("Logistique", analyse["details"].get("type_usage", ""))

    def test_scan_endpoint_sans_fichier(self):
        """Vérifie que l'endpoint /scan renvoie une erreur 400 sans fichier."""
        response = self.app.post("/scan", data={})
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertEqual(json_data.get("status"), "error")

    def test_scan_endpoint_fichier_invalide(self):
        """Vérifie que l'endpoint /scan rejette les fichiers non-images."""
        data = {
            "file": (io.BytesIO(b"fichier non image corrompu"), "test.txt")
        }
        response = self.app.post("/scan", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
