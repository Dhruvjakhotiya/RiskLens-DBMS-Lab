-- Demonstration queries: INSERT, SELECT, UPDATE, DELETE, JOIN, LEFT JOIN, GROUP BY.
INSERT INTO patients (demo_identifier, full_name, date_of_birth, sex)
VALUES ('DEMO-SQL', 'SQL Demonstration', '1990-01-01', 'Prefer not to say');
SELECT p.demo_identifier, h.recorded_at, h.glucose
FROM patients p INNER JOIN health_records h ON h.patient_id = p.patient_id
WHERE p.is_active = 1 ORDER BY h.recorded_at DESC;
SELECT p.demo_identifier, COUNT(a.assessment_id) AS assessment_count
FROM patients p LEFT JOIN risk_assessments a ON a.patient_id = p.patient_id
GROUP BY p.patient_id ORDER BY assessment_count DESC;
UPDATE patients SET full_name = 'SQL Demonstration Updated' WHERE demo_identifier = 'DEMO-SQL';
DELETE FROM patients WHERE demo_identifier = 'DEMO-SQL';
