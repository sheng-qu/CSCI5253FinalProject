"""One-time bootstrap: seed Postgres from the Phase 6 joblib artifact.
Usage:
    python -m db.bootstrap
"""

import json
import os

import joblib
import psycopg

ARTIFACT_PATH = os.environ["ARTIFACT_PATH"]
DATABASE_URL = os.environ["DATABASE_URL"]


def _upsert_entity_stats(cur, art):
    gs = art["graph_state"]
    # Build a unified row per (entity_type, entity_value).
    rows: dict[tuple[str, str], dict] = {}

    for entity_type, table in gs["nbr_fraud_rate"].items():
        for value, rate in table.items():
            rows.setdefault((entity_type, str(value)), {})["nbr_fraud_rate"] = rate

    for col, table in gs["degree"].items():
        entity_type, _, neighbor = col.partition("__nunique_")
        for value, deg in table.items():
            d = rows.setdefault((entity_type, str(value)), {})
            d.setdefault("degree_map", {})[neighbor] = deg

    for entity_type, table in gs["amt_stats"].items():
        for value, (mean, std) in table.items():
            d = rows.setdefault((entity_type, str(value)), {})
            d["amt_mean"] = mean
            d["amt_std"] = std

    print(f"Upserting {len(rows):,} entity_stats rows ...")
    for (etype, evalue), fields in rows.items():
        cur.execute(
            """
            INSERT INTO entity_stats
                (entity_type, entity_value, nbr_fraud_rate, degree_map, amt_mean, amt_std)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (entity_type, entity_value) DO UPDATE SET
                nbr_fraud_rate = EXCLUDED.nbr_fraud_rate,
                degree_map     = EXCLUDED.degree_map,
                amt_mean       = EXCLUDED.amt_mean,
                amt_std        = EXCLUDED.amt_std,
                updated_at     = now()
            """,
            (
                etype,
                evalue,
                fields.get("nbr_fraud_rate"),
                json.dumps(fields.get("degree_map", {})),
                fields.get("amt_mean"),
                fields.get("amt_std"),
            ),
        )


def _insert_velocity_snapshot(cur, art):
    snapshot = art["graph_state"]["velocity_snapshot"]
    total = 0
    for entity_type, table in snapshot.items():
        for value, timestamps in table.items():
            for ts in timestamps:
                cur.execute(
                    """
                    INSERT INTO velocity_events (entity_type, entity_value, transaction_dt)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (entity_type, str(value), int(ts)),
                )
                total += 1
    print(f"Inserted ~{total:,} velocity_events rows.")


def main():
    print(f"Loading artifact: {ARTIFACT_PATH}")
    art = joblib.load(ARTIFACT_PATH)

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            _upsert_entity_stats(cur, art)
            _insert_velocity_snapshot(cur, art)
        conn.commit()
    print("Bootstrap complete.")


if __name__ == "__main__":
    main()
