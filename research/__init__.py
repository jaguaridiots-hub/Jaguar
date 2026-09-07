# research/__init__.py
"""
Jaguar Quant X – Institutional Research Suite
"""
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Meta table
    c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()

    # 1. Normal version‑based migrations
    version = _get_schema_version(c)
    if version < 4:
        _migrate_v3_to_v4(c)
    if version < 5:
        _migrate_v4_to_v5(c)
    if version < 6:
        _migrate_v5_to_v6(c)
    if version < 7:
        _migrate_v6_to_v7(c)
    _set_schema_version(c, 7)
    conn.commit()

    # 2. Validate & repair physical schema
    missing = validate_schema(c)
    if missing:
        print(f"⚠️ Schema drift detected: missing {missing}. Auto‑repairing…")
        repair_schema(c, missing)
        conn.commit()
        print("✅ Schema repair complete.")

    return conn
