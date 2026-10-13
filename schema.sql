CREATE DATABASE IF NOT EXISTS scam_mapper CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE scam_mapper;

CREATE TABLE IF NOT EXISTS reports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  incident_date DATE NULL,
  status ENUM('new','reviewed','closed') NOT NULL DEFAULT 'new',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_reports_created (created_at), INDEX idx_reports_status (status)
);
CREATE TABLE IF NOT EXISTS evidence (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  kind ENUM('phone','email','url','payment_id','other') NOT NULL,
  value_normalized VARCHAR(512) NOT NULL,
  value_display VARCHAR(512) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_evidence_kind_value (kind, value_normalized(191))
);
CREATE TABLE IF NOT EXISTS report_evidence (
  report_id BIGINT UNSIGNED NOT NULL,
  evidence_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (report_id, evidence_id),
  CONSTRAINT fk_re_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
  CONSTRAINT fk_re_evidence FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT UNSIGNED NULL,
  action VARCHAR(40) NOT NULL,
  details VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE SET NULL,
  INDEX idx_audit_created (created_at)
);

-- Reviewer accounts are private; create them with create_reviewer.py.
CREATE TABLE IF NOT EXISTS reviewers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Example analytics query: evidence shared by at least three distinct reports.
-- SELECT e.kind, e.value_display, COUNT(DISTINCT re.report_id) AS report_count
-- FROM evidence e JOIN report_evidence re ON re.evidence_id=e.id
-- GROUP BY e.id HAVING COUNT(DISTINCT re.report_id)>=3;
