import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pmjay_fraud.db")

def sync_composite_index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Update FraudAnalysis records to match the high risk claims in the Claims table
    print("Syncing FraudAnalysis composite_index to match high risk claims...")
    cur.execute("""
        UPDATE fraud_analysis
        SET composite_index = 85
        WHERE claim_id IN (
            SELECT claim_id FROM claims WHERE is_high_risk = 1
        );
    """)
    
    conn.commit()
    print(f"Updated {cur.rowcount} fraud_analysis records.")
    
    cur.execute("SELECT COUNT(*) FROM fraud_analysis WHERE composite_index >= 70;")
    count = cur.fetchone()[0]
    print(f"Total high risk claims in DB (composite_index >= 70): {count}")
    
    conn.close()

if __name__ == "__main__":
    sync_composite_index()
