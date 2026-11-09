-- ==============================================================================
-- Script d'initialisation de PostgreSQL (exécuté au premier démarrage du conteneur)
-- ==============================================================================

-- 1. Création de l'utilisateur applicatif dédié (non-root)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'data_user') THEN
        CREATE USER data_user WITH ENCRYPTED PASSWORD 'data_secure_password';
    END IF;
END
$$;

-- 2. Attribution des privilèges sur la base de données
GRANT CONNECT ON DATABASE ma_base_de_donnees TO data_user;

-- 3. Droits sur le schéma public
GRANT USAGE, CREATE ON SCHEMA public TO data_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO data_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO data_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO data_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO data_user;

-- 4. Création de la table 'scans' pour stocker les données métier
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    barcode_data VARCHAR(255) UNIQUE NOT NULL,
    scan_count INT DEFAULT 1,
    last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Attribution des droits sur la table et la séquence associée
GRANT ALL PRIVILEGES ON TABLE scans TO data_user;
GRANT USAGE, SELECT ON SEQUENCE scans_id_seq TO data_user;
