-- One-time setup on the GCP VM (MySQL already installed).
-- Run as MySQL admin, e.g.:
--   sudo mysql < /var/www/cryptosignals/deploy/init-database.sql
--
-- Grants the existing leadpilot@localhost user access to the new database.

CREATE DATABASE IF NOT EXISTS `crypto_signals`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON `crypto_signals`.* TO 'leadpilot'@'localhost';
FLUSH PRIVILEGES;
