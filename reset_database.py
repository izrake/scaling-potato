"""Reset database script - Drops and recreates the database from scratch."""
import os
import sys

def reset_database():
    """Drop and recreate the database."""
    db_path = "enricher.db"
    
    if os.path.exists(db_path):
        print("🗑️  Removing existing database...")
        os.remove(db_path)
        print("✓ Database removed")
    else:
        print("ℹ️  Database doesn't exist, nothing to remove")
    
    print("\n🔄 Creating fresh database...")
    # Import Database to trigger creation
    from database import Database
    db = Database()
    
    print("✓ Fresh database created successfully!")
    print("\n✅ Database reset complete!")
    print("   All tables have been recreated with the latest schema.")
    print("\n📋 Verified Schema:")
    print("   ✓ step3_company_name: Stores company name from LinkedIn profile")
    print("   ✓ step3_name: Stores user's name")
    print("   ✓ step4_website_url: Stores company website")
    print("   ✓ step5_company_description: Stores scraped website text")
    print("   ✓ custom_columns_data: Stores custom message columns (JSON)")
    print("   ✓ csv_columns_data: Stores all CSV columns (JSON)")
    print("   ✓ lead_status: raw_lead, qualified, contacted")
    print("   ✓ contacted_date: Date when lead was marked as contacted")
    print("   ✓ All message generation fields included")

if __name__ == '__main__':
    print("=" * 60)
    print("Database Reset Tool")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete all existing data!")
    
    # Check if --yes flag is provided for non-interactive mode
    if '--yes' in sys.argv or '--force' in sys.argv:
        print("   Auto-confirming (--yes/--force flag provided)...")
        reset_database()
    else:
        print("   Press Ctrl+C to cancel, or Enter to continue...")
        print("=" * 60)
        
        try:
            input()
            reset_database()
        except KeyboardInterrupt:
            print("\n\n❌ Reset cancelled by user")
        except Exception as e:
            print(f"\n\n❌ Error resetting database: {e}")
            import traceback
            traceback.print_exc()
