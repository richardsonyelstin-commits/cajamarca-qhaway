"""Inspeccion de esquema y conteos en Supabase oglltrpvvifqvwmxmkjq."""

from scripts.verification.supabase_admin import execute_sql

tables = [
    "contracting_entities",
    "procurement_records",
    "budget_execution_records",
    "red_flags",
    "alerts",
    "citizen_reports",
]

for t in tables:
    cnt = execute_sql(f"SELECT count(*) FROM {t};")
    cols = execute_sql(
        f"SELECT column_name, data_type, is_nullable "
        f"FROM information_schema.columns "
        f"WHERE table_name = '{t}' "
        f"ORDER BY ordinal_position;"
    )
    print(f"=== TABLE: {t} (count: {cnt[0]['count']}) ===")
    for c in cols:
        print(f"  - {c['column_name']}: {c['data_type']} (nullable: {c['is_nullable']})")
