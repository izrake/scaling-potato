"""Database migration script to add new columns."""
import sqlite3
import os
from database import Database

def migrate_database():
    """Add missing columns to existing database."""
    db_path = "enricher.db"
    
    if not os.path.exists(db_path):
        print("Database doesn't exist yet. It will be created with the correct schema.")
        return
    
    print("Migrating database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add step3_valid_experience if it doesn't exist
        if 'step3_valid_experience' not in columns:
            print("Adding step3_valid_experience column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN step3_valid_experience TEXT DEFAULT 'true'")
            conn.commit()
            print("✓ Added step3_valid_experience column")
        else:
            print("✓ step3_valid_experience column already exists")
        
        # Add step3_experience_reason if it doesn't exist
        if 'step3_experience_reason' not in columns:
            print("Adding step3_experience_reason column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN step3_experience_reason TEXT")
            conn.commit()
            print("✓ Added step3_experience_reason column")
        else:
            print("✓ step3_experience_reason column already exists")
        
        # Add message generation columns
        if 'generated_email' not in columns:
            print("Adding generated_email column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN generated_email TEXT")
            conn.commit()
            print("✓ Added generated_email column")
        else:
            print("✓ generated_email column already exists")
        
        if 'generated_linkedin_connection' not in columns:
            print("Adding generated_linkedin_connection column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN generated_linkedin_connection TEXT")
            conn.commit()
            print("✓ Added generated_linkedin_connection column")
        else:
            print("✓ generated_linkedin_connection column already exists")
        
        if 'generated_linkedin_followup' not in columns:
            print("Adding generated_linkedin_followup column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN generated_linkedin_followup TEXT")
            conn.commit()
            print("✓ Added generated_linkedin_followup column")
        else:
            print("✓ generated_linkedin_followup column already exists")
        
        if 'messages_generated_at' not in columns:
            print("Adding messages_generated_at column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN messages_generated_at DATETIME")
            conn.commit()
            print("✓ Added messages_generated_at column")
        else:
            print("✓ messages_generated_at column already exists")
        
        if 'custom_columns_data' not in columns:
            print("Adding custom_columns_data column...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN custom_columns_data TEXT")
            conn.commit()
            print("✓ Added custom_columns_data column")
        else:
            print("✓ custom_columns_data column already exists")
        
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

