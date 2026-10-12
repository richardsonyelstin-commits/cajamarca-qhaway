-- Migracion 0004: Siembra inicial del universo dorado de 14 entidades (ADR 0006)
INSERT INTO contracting_entities (
    entity_id, official_name, entity_level, province, ruc, consucode_id, department, verified_at, active
) VALUES
    ('ce-f5f5d8fc32518855', 'GOBIERNO REGIONAL DE CAJAMARCA', 'regional', NULL, '20453744168', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-2caad0e1b7467492', 'MUNICIPALIDAD PROVINCIAL DE CAJAMARCA', 'provincial_municipality', 'CAJAMARCA', '20143623042', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-b4a52d15b3cffe4f', 'MUNICIPALIDAD PROVINCIAL DE CAJABAMBA', 'provincial_municipality', 'CAJABAMBA', '20148288853', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-2b779c1e84ff4365', 'MUNICIPALIDAD PROVINCIAL DE CELENDIN', 'provincial_municipality', 'CELENDIN', '20148289825', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-45fad1d64ba4bf0f', 'MUNICIPALIDAD PROVINCIAL DE CHOTA', 'provincial_municipality', 'CHOTA', '20220499767', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-3337df921084c80a', 'MUNICIPALIDAD PROVINCIAL DE CONTUMAZA', 'provincial_municipality', 'CONTUMAZA', '20191657447', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-360cf7aadccadabb', 'MUNICIPALIDAD PROVINCIAL DE CUTERVO', 'provincial_municipality', 'CUTERVO', '20174691267', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-dfd10c914365bbe3', 'MUNICIPALIDAD PROVINCIAL DE HUALGAYOC', 'provincial_municipality', 'HUALGAYOC', '20148260843', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-1817b32570ae7027', 'MUNICIPALIDAD PROVINCIAL DE JAEN', 'provincial_municipality', 'JAEN', '20201987297', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-697eb5a0a1b4e6c6', 'MUNICIPALIDAD PROVINCIAL SAN IGNACIO', 'provincial_municipality', 'SAN IGNACIO', '20148261572', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-ad540c85ce98e1d8', 'MUNICIPALIDAD PROVINCIAL DE SAN MARCOS', 'provincial_municipality', 'SAN MARCOS', '20175083937', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-3511b005adba63bf', 'MUNICIPALIDAD PROVINCIAL SAN MIGUEL', 'provincial_municipality', 'SAN MIGUEL', '20143625843', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-d7fc753b1fb5ff5b', 'MUNICIPALIDAD PROVINCIAL DE SAN PABLO', 'provincial_municipality', 'SAN PABLO', '20172446800', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE),
    ('ce-f29ffd64eff3fe9a', 'MUNICIPALIDAD PROVINCIAL DE SANTA CRUZ', 'provincial_municipality', 'SANTA CRUZ', '20200367376', NULL, 'CAJAMARCA', '2026-08-20T00:00:00+00:00', TRUE)
ON CONFLICT (entity_id) DO UPDATE SET
    official_name = EXCLUDED.official_name,
    entity_level  = EXCLUDED.entity_level,
    province      = EXCLUDED.province,
    ruc           = EXCLUDED.ruc,
    consucode_id  = EXCLUDED.consucode_id,
    department    = EXCLUDED.department,
    verified_at   = EXCLUDED.verified_at,
    active        = EXCLUDED.active;
