"""Database cleanup script - Cleans up old, incomplete, or orphaned data."""
import os
import sys
from datetime import datetime, timedelta
from database import Database
import sqlite3

def cleanup_database(days_old: int = 30, dry_run: bool = False):
    """Clean up database by removing old/incomplete data."""
    db = Database()
    session = db.get_session()
    
    stats = {
        'jobs_deleted': 0,
        'profiles_deleted': 0,
        'orphaned_profiles_deleted': 0,
        'incomplete_profiles_deleted': 0,
        'old_profiles_deleted': 0,
        'status_fixed': 0,
        'files_cleaned': 0
    }
    
    try:
        from database import Profile, Job
        
        print("🔍 Analyzing database...")
        
        # Get all jobs
        all_jobs = session.query(Job).all()
        all_profiles = session.query(Profile).all()
        
        print(f"   Found {len(all_jobs)} jobs and {len(all_profiles)} profiles")
        
        # 1. Clean up incomplete/failed jobs older than X days
        # Use naive datetime for comparison since database stores naive datetimes
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        print(f"\n📅 Cleaning up jobs older than {days_old} days...")
        
        old_jobs = session.query(Job).filter(
            (Job.status.in_(['pending', 'failed', 'cancelled'])) &
            (Job.created_at < cutoff_date)
        ).all()
        
        for job in old_jobs:
            if not dry_run:
                # Delete associated profiles first (cascade should handle this, but being explicit)
                session.query(Profile).filter_by(job_id=job.id).delete()
                session.delete(job)
                stats['jobs_deleted'] += 1
            else:
                stats['jobs_deleted'] += 1
                print(f"   [DRY RUN] Would delete job: {job.id} ({job.filename}) - {job.status}")
        
        if not dry_run:
            session.commit()
        
        # 2. Clean up orphaned profiles (profiles without a job)
        print("\n🔗 Cleaning up orphaned profiles...")
        all_job_ids = {job.id for job in session.query(Job).all()}
        orphaned_profiles = session.query(Profile).filter(
            ~Profile.job_id.in_(all_job_ids)
        ).all()
        
        for profile in orphaned_profiles:
            if not dry_run:
                session.delete(profile)
                stats['orphaned_profiles_deleted'] += 1
            else:
                stats['orphaned_profiles_deleted'] += 1
                print(f"   [DRY RUN] Would delete orphaned profile: {profile.id} ({profile.linkedin_url})")
        
        if not dry_run:
            session.commit()
        
        # 3. Clean up incomplete profiles (stuck in processing/pending for too long)
        print("\n⏳ Cleaning up stuck profiles...")
        # Use naive datetime for comparison since database stores naive datetimes
        stuck_cutoff = datetime.utcnow() - timedelta(days=7)  # 7 days old
        
        stuck_profiles = session.query(Profile).filter(
            (Profile.status.in_(['pending', 'processing'])) &
            (Profile.created_at < stuck_cutoff)
        ).all()
        
        for profile in stuck_profiles:
            if not dry_run:
                session.delete(profile)
                stats['incomplete_profiles_deleted'] += 1
            else:
                stats['incomplete_profiles_deleted'] += 1
                print(f"   [DRY RUN] Would delete stuck profile: {profile.id} ({profile.linkedin_url})")
        
        if not dry_run:
            session.commit()
        
        # 4. Fix lead_status inconsistencies (migrate old statuses)
        print("\n🔄 Fixing lead_status inconsistencies...")
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Update any remaining old statuses
        updates = cursor.execute("""
            UPDATE profiles 
            SET lead_status = 'raw_lead' 
            WHERE lead_status = 'pending' OR lead_status IS NULL
        """).rowcount
        
        updates += cursor.execute("""
            UPDATE profiles 
            SET lead_status = 'qualified' 
            WHERE lead_status = 'reached'
        """).rowcount
        
        if not dry_run:
            conn.commit()
            stats['status_fixed'] = updates
        else:
            stats['status_fixed'] = updates
            print(f"   [DRY RUN] Would fix {updates} lead_status values")
        
        conn.close()
        
        # 5. Clean up old upload files
        print("\n📁 Cleaning up old upload files...")
        uploads_dir = 'uploads'
        if os.path.exists(uploads_dir):
            cutoff_time = datetime.now() - timedelta(days=days_old)
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        if not dry_run:
                            os.remove(file_path)
                            stats['files_cleaned'] += 1
                        else:
                            stats['files_cleaned'] += 1
                            print(f"   [DRY RUN] Would delete old file: {filename}")
        
        # 6. Clean up old result files
        results_dir = 'results'
        if os.path.exists(results_dir):
            cutoff_time = datetime.now() - timedelta(days=days_old)
            for filename in os.listdir(results_dir):
                file_path = os.path.join(results_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        if not dry_run:
                            os.remove(file_path)
                            stats['files_cleaned'] += 1
                        else:
                            stats['files_cleaned'] += 1
                            print(f"   [DRY RUN] Would delete old file: {filename}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Cleanup Summary")
        print("=" * 60)
        print(f"   Jobs deleted: {stats['jobs_deleted']}")
        print(f"   Orphaned profiles deleted: {stats['orphaned_profiles_deleted']}")
        print(f"   Incomplete profiles deleted: {stats['incomplete_profiles_deleted']}")
        print(f"   Lead statuses fixed: {stats['status_fixed']}")
        print(f"   Old files cleaned: {stats['files_cleaned']}")
        print("=" * 60)
        
        if dry_run:
            print("\n⚠️  This was a DRY RUN - no changes were made")
            print("   Run without --dry-run to apply changes")
        else:
            print("\n✅ Database cleanup completed!")
        
        return stats
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return stats
    finally:
        session.close()


def show_database_stats():
    """Show current database statistics."""
    db = Database()
    session = db.get_session()
    
    try:
        from database import Profile, Job
        
        total_jobs = session.query(Job).count()
        total_profiles = session.query(Profile).count()
        
        # Jobs by status
        jobs_by_status = {}
        for status in ['pending', 'processing', 'completed', 'failed', 'cancelled']:
            count = session.query(Job).filter_by(status=status).count()
            if count > 0:
                jobs_by_status[status] = count
        
        # Profiles by status
        profiles_by_status = {}
        for status in ['pending', 'processing', 'completed', 'failed', 'cancelled']:
            count = session.query(Profile).filter_by(status=status).count()
            if count > 0:
                profiles_by_status[status] = count
        
        # Profiles by lead_status
        profiles_by_lead_status = {}
        for lead_status in ['raw_lead', 'qualified', 'contacted']:
            count = session.query(Profile).filter_by(lead_status=lead_status).count()
            if count > 0:
                profiles_by_lead_status[lead_status] = count
        
        # Orphaned profiles
        all_job_ids = {job.id for job in session.query(Job).all()}
        orphaned_count = session.query(Profile).filter(
            ~Profile.job_id.in_(all_job_ids) if all_job_ids else True
        ).count()
        
        print("=" * 60)
        print("📊 Database Statistics")
        print("=" * 60)
        print(f"\n📦 Jobs: {total_jobs}")
        if jobs_by_status:
            print("   By status:")
            for status, count in jobs_by_status.items():
                print(f"     {status}: {count}")
        
        print(f"\n👤 Profiles: {total_profiles}")
        if profiles_by_status:
            print("   By status:")
            for status, count in profiles_by_status.items():
                print(f"     {status}: {count}")
        
        if profiles_by_lead_status:
            print("   By lead_status:")
            for lead_status, count in profiles_by_lead_status.items():
                print(f"     {lead_status}: {count}")
        
        if orphaned_count > 0:
            print(f"\n⚠️  Orphaned profiles: {orphaned_count}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up database and old files')
    parser.add_argument('--days', type=int, default=30, help='Delete data older than N days (default: 30)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without making changes')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if args.stats:
        show_database_stats()
    else:
        print("=" * 60)
        print("Database Cleanup Tool")
        print("=" * 60)
        
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
        else:
            print(f"\n⚠️  WARNING: This will delete data older than {args.days} days!")
            print("   This includes:")
            print("   - Incomplete/failed jobs")
            print("   - Orphaned profiles")
            print("   - Stuck profiles")
            print("   - Old upload/result files")
        
        print("=" * 60)
        
        if not args.yes and not args.dry_run:
            try:
                response = input("\nContinue? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print("\n❌ Cleanup cancelled")
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\n\n❌ Cleanup cancelled")
                sys.exit(0)
        
        # Show stats before cleanup
        print("\n📊 Before cleanup:")
        show_database_stats()
        
        # Run cleanup
        print("\n🧹 Running cleanup...")
        stats = cleanup_database(days_old=args.days, dry_run=args.dry_run)
        
        # Show stats after cleanup (if not dry run)
        if not args.dry_run:
            print("\n📊 After cleanup:")
            show_database_stats()

