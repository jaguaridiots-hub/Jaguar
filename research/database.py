# research/database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "research.db")

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _get_schema_version(cursor):
    cursor.execute("SELECT value FROM meta WHERE key = 'schema_version'")
    row = cursor.fetchone()
    return int(row[0]) if row else 0

def _set_schema_version(cursor, version):
    cursor.execute("REPLACE INTO meta (key, value) VALUES ('schema_version', ?)", (str(version),))

def _add_column_if_not_exists(cursor, table, column, col_type):
    """Add a column only if it doesn't already exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

# ----------------------------------------------------------------------
# Migrations (idempotent)
# ----------------------------------------------------------------------
def _migrate_v3_to_v4(cursor):
    _add_column_if_not_exists(cursor, "trades", "snapshot_open", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "snapshot_open_checksum", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "decision", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "confidence", "REAL")
    _add_column_if_not_exists(cursor, "trades", "composite_score", "REAL")
    _add_column_if_not_exists(cursor, "trades", "brain_score", "REAL")
    _add_column_if_not_exists(cursor, "trades", "probability_score", "REAL")
    _set_schema_version(cursor, 4)

def _migrate_v4_to_v5(cursor):
    _add_column_if_not_exists(cursor, "trades", "master_decision", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "validator_score", "REAL")
    _add_column_if_not_exists(cursor, "trades", "market_regime", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "mtf_bias", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "smc_signal", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "liquidity_signal", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "fvg_signal", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "orderflow_signal", "TEXT")
    _set_schema_version(cursor, 5)

def _migrate_v5_to_v6(cursor):
    _add_column_if_not_exists(cursor, "trades", "run_id", "TEXT")
    _add_column_if_not_exists(cursor, "trades", "success", "INTEGER")
    _add_column_if_not_exists(cursor, "trades", "asset_class", "TEXT")
    _set_schema_version(cursor, 6)

def _migrate_v6_to_v7(cursor):
    # Canonical v7 schema – the only place where the full table layout is defined.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            uuid TEXT PRIMARY KEY,
            open_time TEXT,
            symbol TEXT,
            timeframe TEXT,
            mode TEXT,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            snapshot_open TEXT,
            snapshot_open_checksum TEXT,
            decision TEXT,
            confidence REAL,
            composite_score REAL,
            brain_score REAL,
            probability_score REAL,
            master_decision TEXT,
            validator_score REAL,
            market_regime TEXT,
            mtf_bias TEXT,
            smc_signal TEXT,
            liquidity_signal TEXT,
            fvg_signal TEXT,
            orderflow_signal TEXT,
            run_id TEXT,
            success INTEGER,
            asset_class TEXT,
            close_time TEXT,
            exit_price REAL,
            pnl REAL,
            r_multiple REAL,
            win_loss INTEGER,
            holding_time INTEGER,
            snapshot_close TEXT,
            snapshot_close_checksum TEXT
        )
    """)
    _set_schema_version(cursor, 7)

# ----------------------------------------------------------------------
# Schema validation & self‑healing
# ----------------------------------------------------------------------
def validate_schema(cursor):
    required = {
        "uuid", "open_time", "symbol", "timeframe", "mode",
        "entry_price", "stop_loss", "take_profit",
        "snapshot_open", "snapshot_open_checksum",
        "decision", "confidence", "composite_score",
        "brain_score", "probability_score", "master_decision",
        "validator_score", "market_regime",
        "mtf_bias", "smc_signal", "liquidity_signal",
        "fvg_signal", "orderflow_signal",
        "run_id", "success", "asset_class",
        "close_time", "exit_price", "pnl", "r_multiple",
        "win_loss", "holding_time",
        "snapshot_close", "snapshot_close_checksum",
    }
    cursor.execute("PRAGMA table_info(trades)")
    existing = {row[1] for row in cursor.fetchall()}
    return required - existing

def repair_schema(cursor, missing):
    migration_added_columns = {
        "v3→v4": {
            "snapshot_open", "snapshot_open_checksum", "decision",
            "confidence", "composite_score", "brain_score", "probability_score"
        },
        "v4→v5": {
            "master_decision", "validator_score", "market_regime",
            "mtf_bias", "smc_signal", "liquidity_signal", "fvg_signal", "orderflow_signal"
        },
        "v5→v6": {
            "run_id", "success", "asset_class"
        },
        "v6→v7": {
            "close_time", "exit_price", "pnl", "r_multiple",
            "win_loss", "holding_time", "snapshot_close", "snapshot_close_checksum"
        }
    }
    if missing & migration_added_columns["v3→v4"]:
        _migrate_v3_to_v4(cursor)
    if missing & migration_added_columns["v4→v5"]:
        _migrate_v4_to_v5(cursor)
    if missing & migration_added_columns["v5→v6"]:
        _migrate_v5_to_v6(cursor)
    if missing & migration_added_columns["v6→v7"]:
        _migrate_v6_to_v7(cursor)

# ----------------------------------------------------------------------
# init_db – creates all tables including Phase 33D columns
# ----------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
    if not c.fetchone():
        _migrate_v6_to_v7(c)
        _set_schema_version(c, 7)
        conn.commit()
    else:
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

        missing = validate_schema(c)
        if missing:
            print(f"⚠️  Schema drift detected – missing columns: {missing}")
            repair_schema(c, missing)
            conn.commit()
            still_missing = validate_schema(c)
            if still_missing:
                raise RuntimeError(f"Schema repair failed. Missing columns: {still_missing}")
            _set_schema_version(c, 7)
            conn.commit()
            print("✅ Schema repair complete. All required columns present.")

    # score_log table (Phase 33D enhanced)
    c.execute("""
        CREATE TABLE IF NOT EXISTS score_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT UNIQUE NOT NULL,
            timestamp TEXT,
            symbol TEXT,
            timeframe TEXT,
            mode TEXT,
            brain_score REAL,
            composite_score REAL,
            decision TEXT,
            contributions_json TEXT,
            regime TEXT,
            smc_signal TEXT,
            liquidity_signal TEXT,
            orderflow_signal TEXT,
            premium_discount TEXT,
            session_score REAL,
            volume_profile_score REAL,
            rejection_stage TEXT,
            rejection_reasons TEXT,
            threshold_required_score REAL,
            validator_approved INTEGER,
            engine_snapshot_json TEXT,
            mtf_loaded TEXT,
            trade_uuid TEXT,
            outcome TEXT DEFAULT 'REJECT',
            run_id TEXT,
            jaguar_version TEXT,
            FOREIGN KEY (trade_uuid) REFERENCES trades(uuid)
        )
    """)

    # Safe migration for existing score_log tables
    _add_column_if_not_exists(c, "score_log", "rejection_stage", "TEXT")
    _add_column_if_not_exists(c, "score_log", "rejection_reasons", "TEXT")
    _add_column_if_not_exists(c, "score_log", "threshold_required_score", "REAL")
    _add_column_if_not_exists(c, "score_log", "validator_approved", "INTEGER")
    _add_column_if_not_exists(c, "score_log", "engine_snapshot_json", "TEXT")
    _add_column_if_not_exists(c, "score_log", "mtf_loaded", "TEXT")

    # Research Campaign Runs
    c.execute("""
        CREATE TABLE IF NOT EXISTS research_runs (
            run_id TEXT PRIMARY KEY,
            jaguar_version TEXT,
            start_time TEXT,
            end_time TEXT,
            duration REAL,
            symbols TEXT,
            modes TEXT,
            timeframes TEXT,
            total_decisions INTEGER DEFAULT 0,
            executed_trades INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            avg_brain_score REAL,
            avg_composite_score REAL,
            avg_confidence REAL,
            notes TEXT
        )
    """)
    conn.commit()
    return conn

# ----------------------------------------------------------------------
# Lightweight connection for CRUD – NO init_db call
# ----------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Existing APIs (unchanged)
def insert_open_trade(data):
    conn = get_connection()
    c = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    c.execute(f"INSERT INTO trades ({columns}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()

def update_close_trade(uuid, close_data):
    conn = get_connection()
    c = conn.cursor()
    sets = ", ".join(f"{k} = ?" for k in close_data)
    values = list(close_data.values()) + [uuid]
    c.execute(f"UPDATE trades SET {sets} WHERE uuid = ?", values)
    conn.commit()
    conn.close()

def insert_decision_log(data: dict):
    conn = get_connection()
    c = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    c.execute(f"INSERT INTO score_log ({columns}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()

def update_decision_outcome(decision_id: str, outcome: str, trade_uuid: str = None):
    conn = get_connection()
    c = conn.cursor()
    if trade_uuid:
        c.execute("UPDATE score_log SET outcome = ?, trade_uuid = ? WHERE decision_id = ?",
                  (outcome, trade_uuid, decision_id))
    else:
        c.execute("UPDATE score_log SET outcome = ? WHERE decision_id = ?",
                  (outcome, decision_id))
    conn.commit()
    conn.close()

def update_decision_stage(decision_id: str, stage: str, threshold_required: float = None, reasons: str = None):
    conn = get_connection()
    c = conn.cursor()
    updates = ["rejection_stage = ?"]
    params = [stage]
    if threshold_required is not None:
        updates.append("threshold_required_score = ?")
        params.append(threshold_required)
    if reasons is not None:
        updates.append("rejection_reasons = ?")
        params.append(reasons)
    params.append(decision_id)
    c.execute(f"UPDATE score_log SET {', '.join(updates)} WHERE decision_id = ?", params)
    conn.commit()
    conn.close()

# ---- Campaign functions ----
def insert_research_run(run_id: str, jaguar_version: str, symbols: str, modes: str,
                        timeframes: str, notes: str = None, start_time: str = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO research_runs (run_id, jaguar_version, start_time, symbols, modes, timeframes, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (run_id, jaguar_version, start_time, symbols, modes, timeframes, notes))
    conn.commit()
    conn.close()

def update_research_run(run_id: str, end_time: str, duration: float, total_decisions: int,
                        executed_trades: int, wins: int, losses: int,
                        avg_brain: float, avg_composite: float, avg_confidence: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE research_runs SET
            end_time = ?, duration = ?,
            total_decisions = ?, executed_trades = ?, wins = ?, losses = ?,
            avg_brain_score = ?, avg_composite_score = ?, avg_confidence = ?
        WHERE run_id = ?
    """, (end_time, duration, total_decisions, executed_trades, wins, losses,
          avg_brain, avg_composite, avg_confidence, run_id))
    conn.commit()
    conn.close()

def get_campaign_stats(run_id: str):
    conn = get_connection()
    c = conn.cursor()
    total_dec = c.execute("SELECT COUNT(*) FROM score_log WHERE run_id = ?", (run_id,)).fetchone()[0]
    exec_trades = c.execute("SELECT COUNT(*) FROM score_log WHERE run_id = ? AND outcome IN ('WIN','LOSS')", (run_id,)).fetchone()[0]
    wins = c.execute("SELECT COUNT(*) FROM score_log WHERE run_id = ? AND outcome = 'WIN'", (run_id,)).fetchone()[0]
    losses = c.execute("SELECT COUNT(*) FROM score_log WHERE run_id = ? AND outcome = 'LOSS'", (run_id,)).fetchone()[0]
    avg_brain = c.execute("SELECT AVG(brain_score) FROM score_log WHERE run_id = ?", (run_id,)).fetchone()[0]
    avg_composite = c.execute("SELECT AVG(composite_score) FROM score_log WHERE run_id = ?", (run_id,)).fetchone()[0]
    avg_confidence = 0.0
    conn.close()
    return {
        "total_decisions": total_dec,
        "executed_trades": exec_trades,
        "wins": wins,
        "losses": losses,
        "avg_brain_score": avg_brain or 0.0,
        "avg_composite_score": avg_composite or 0.0,
        "avg_confidence": avg_confidence
    }
