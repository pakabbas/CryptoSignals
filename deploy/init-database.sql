-- One-time setup on the GCP VM (MySQL already installed).
-- Run as MySQL admin, e.g.:
--   sudo mysql < /var/www/cryptosignals/deploy/init-database.sql
--
-- Reuses the existing application user (e.g. leadpilot) for the new database.

CREATE DATABASE IF NOT EXISTS `crypto_signals`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON `crypto_signals`.* TO 'leadpilot'@'localhost';
GRANT ALL PRIVILEGES ON `crypto_signals`.* TO 'leadpilot'@'127.0.0.1';
FLUSH PRIVILEGES;
