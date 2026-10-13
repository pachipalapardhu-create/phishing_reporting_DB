USE scam_mapper;
-- Fictional examples for learning only. These are not real reports or identifiers.
INSERT INTO reports (title, description, incident_date, status) VALUES
('Sample parcel fee text', 'A sample message claimed a parcel was delayed and asked for a small redelivery payment.', '2026-01-12', 'reviewed'),
('Sample delivery payment request', 'A fictional report describing a second message with a similar payment handle.', '2026-02-03', 'reviewed'),
('Sample social media offer', 'A fictional account offered a prize and linked to a suspicious example website.', '2026-02-17', 'new');
INSERT INTO evidence (kind, value_normalized, value_display) VALUES
('payment_id','demo-pay-0001','demo-pay-0001'),
('url','https://parcel-example.invalid/pay','https://parcel-example.invalid/pay'),
('url','https://offer-example.invalid/claim','https://offer-example.invalid/claim');
INSERT IGNORE INTO report_evidence (report_id,evidence_id)
SELECT r.id,e.id FROM reports r JOIN evidence e ON
 (r.title='Sample parcel fee text' AND e.value_normalized IN ('demo-pay-0001','https://parcel-example.invalid/pay')) OR
 (r.title='Sample delivery payment request' AND e.value_normalized='demo-pay-0001') OR
 (r.title='Sample social media offer' AND e.value_normalized='https://offer-example.invalid/claim');
