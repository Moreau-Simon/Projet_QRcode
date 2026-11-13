import os
import io
import unittest
from unittest.mock import patch, MagicMock
import importlib.util
import requests

# Chargement dynamique du module ambassadeur
MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ambassadeur", "main.py"))
spec = importlib.util.spec_from_file_location("ambassadeur_main", MODULE_PATH)
ambassadeur_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ambassadeur_module)


class TestAmbassadeur(unittest.TestCase):

    def setUp(self):
        self.app = ambassadeur_module.app.test_client()
        self.app.testing = True

    def test_scan_sans_fichier(self):
        """Vérifie que la route /api/scan rejette les requêtes sans fichier joint."""
        response = self.app.post("/api/scan", data={})
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertIn("Aucun fichier envoyé", json_data.get("error", ""))

    @patch("requests.post")
    def test_scan_succes_avec_mock(self, mock_post):
        """Vérifie le routage complet d'un scan réussi (Job -> Data C# -> IHM)."""
        # 1. Mock de la réponse du Job Python
        job_mock = MagicMock()
        job_mock.ok = True
        job_mock.json.return_value = {
            "status": "success",
            "data": "67430",
            "type": "CODE39",
            "angle_detecte": 30,
            "analyse": {"symbologie": "CODE39", "est_valide": True}
        }

        # 2. Mock de la réponse du Dataware C#
        data_mock = MagicMock()
        data_mock.ok = True
        data_mock.json.return_value = {
            "status": "success",
            "source": "postgres",
            "scan_count": 5
        }

        # Séquence de réponses pour requests.post
        mock_post.side_effect = [job_mock, data_mock]

        data = {
            "file": (io.BytesIO(b"fake_image_data"), "test.jpg", "image/jpeg")
        }
        response = self.app.post("/api/scan", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data.get("status"), "success")
        self.assertEqual(json_data.get("code"), "67430")
        self.assertEqual(json_data.get("type"), "CODE39")
        self.assertEqual(json_data.get("angle_detecte"), 30)
        self.assertIsNotNone(json_data.get("database_info"))

    @patch("requests.post")
    def test_scan_aucun_code_detecte(self, mock_post):
        """Vérifie la réponse lorsque le Job ne trouve aucun code (200 avec code: None pour continuer le stream)."""
        job_mock = MagicMock()
        job_mock.ok = True
        job_mock.json.return_value = {
            "status": "error",
            "message": "Aucun code détecté"
        }
        mock_post.return_value = job_mock

        data = {
            "file": (io.BytesIO(b"image_sans_code"), "vide.jpg", "image/jpeg")
        }
        response = self.app.post("/api/scan", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIsNone(json_data.get("code"))
        self.assertIn("Aucun code", json_data.get("error"))

    @patch("requests.post")
    def test_scan_service_injoignable(self, mock_post):
        """Vérifie la gestion d'erreur (502 Bad Gateway) si un microservice est injoignable."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        data = {
            "file": (io.BytesIO(b"image_data"), "scan.jpg", "image/jpeg")
        }
        response = self.app.post("/api/scan", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 502)
        json_data = response.get_json()
        self.assertIn("Service injoignable", json_data.get("error", ""))


if __name__ == "__main__":
    unittest.main()
