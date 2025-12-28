"""Database models and operations for storing enrichment data."""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Optional, Dict, List

Base = declarative_base()


class Job(Base):
    """Job table for tracking enrichment jobs."""
    __tablename__ = 'jobs'
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    total_urls = Column(Integer, nullable=False)
    processed = Column(Integer, default=0)
    status = Column(String, default='pending')  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    profiles = relationship("Profile", back_populates="job", cascade="all, delete-orphan")


class Profile(Base):
    """Profile table for storing individual profile enrichment data."""
    __tablename__ = 'profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey('jobs.id'), nullable=False)
    linkedin_url = Column(String, nullable=False)
    status = Column(String, default='pending')  # pending, processing, completed, failed
    current_step = Column(String, nullable=True)  # step1, step2, step3, step4, step5, step6
    
    # Step outputs
    step1_browser_connected = Column(DateTime, nullable=True)
    step2_profile_opened = Column(DateTime, nullable=True)
    step3_name = Column(String, nullable=True)
    step3_company_name = Column(String, nullable=True)
    step3_company_linkedin_url = Column(String, nullable=True)
    step3_valid_experience = Column(String, default='true')  # 'true', 'false'
    step3_experience_reason = Column(Text, nullable=True)
    step3_extracted_at = Column(DateTime, nullable=True)
    step4_company_page_navigated = Column(DateTime, nullable=True)
    step4_website_url = Column(String, nullable=True)
    step4_extracted_at = Column(DateTime, nullable=True)
    step5_website_scraped = Column(DateTime, nullable=True)
    step5_company_description = Column(Text, nullable=True)
    step6_compiled_at = Column(DateTime, nullable=True)
    
    # Final result
    final_result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Generated messages (stored as JSON)
    generated_email = Column(Text, nullable=True)
    generated_linkedin_connection = Column(Text, nullable=True)
    generated_linkedin_followup = Column(Text, nullable=True)
    messages_generated_at = Column(DateTime, nullable=True)
    
    # Custom columns data (stored as JSON for flexible column management)
    custom_columns_data = Column(JSON, nullable=True)  # {"column_name": "value", ...}
    
    # CSV-provided data (to skip steps 1-4 if website is provided)
    csv_firstname = Column(String, nullable=True)
    csv_lastname = Column(String, nullable=True)
    csv_website = Column(String, nullable=True)
    csv_columns_data = Column(JSON, nullable=True)  # Store all CSV columns as JSON: {"column_name": "value", ...}
    csv_row_index = Column(Integer, nullable=True)  # Track which CSV row this profile came from (0-indexed)
    
    # Lead management status (for Leads page)
    lead_status = Column(String, default='raw_lead')  # raw_lead, qualified, contacted
    contacted_date = Column(DateTime, nullable=True)  # Date when lead was marked as contacted
    
    # LLM Analysis results (for pending leads)
    llm_analysis_what_they_do = Column(Text, nullable=True)  # "What they do" analysis
    llm_analysis_can_we_pitch = Column(Text, nullable=True)  # "Can we pitch Spheron?" analysis
    llm_analysis_raw_response = Column(JSON, nullable=True)  # Raw LLM response JSON
    llm_analysis_generated_at = Column(DateTime, nullable=True)  # When analysis was generated
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="profiles")


class LLMSettings(Base):
    """LLM Settings table for storing configuration for pending and reached sections."""
    __tablename__ = 'llm_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    section = Column(String, nullable=False)  # 'pending' or 'reached'
    provider = Column(String, nullable=False)  # 'openai' or 'gemini'
    api_key = Column(Text, nullable=True)  # Encrypted/stored API key
    model = Column(String, nullable=True)  # Model name (e.g., 'gpt-4', 'gemini-pro')
    system_prompt = Column(Text, nullable=True)  # System prompt for the LLM
    temperature = Column(String, default='0.7')  # Temperature setting
    max_tokens = Column(Integer, default=1000)  # Max tokens for response
    variables = Column(JSON, nullable=True)  # Additional variables/config (e.g., questions for pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    """Database operations."""
    
    def __init__(self, db_path: str = "enricher.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self._migrate_database()
        self.Session = sessionmaker(bind=self.engine)
    
    def _migrate_database(self):
        """Migrate database schema if needed."""
        import sqlite3
        import os
        
        if not os.path.exists(self.db_path):
            return  # New database, no migration needed
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check existing columns
            cursor.execute("PRAGMA table_info(profiles)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns
            if 'step3_valid_experience' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN step3_valid_experience TEXT DEFAULT 'true'")
                conn.commit()
            
            if 'step3_experience_reason' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN step3_experience_reason TEXT")
                conn.commit()
            
            # Add message generation columns
            if 'generated_email' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN generated_email TEXT")
                conn.commit()
            
            if 'generated_linkedin_connection' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN generated_linkedin_connection TEXT")
                conn.commit()
            
            if 'generated_linkedin_followup' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN generated_linkedin_followup TEXT")
                conn.commit()
            
            if 'messages_generated_at' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN messages_generated_at DATETIME")
                conn.commit()
            
            if 'custom_columns_data' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN custom_columns_data TEXT")
                conn.commit()
            
            if 'csv_firstname' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN csv_firstname TEXT")
                conn.commit()
            
            if 'csv_lastname' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN csv_lastname TEXT")
                conn.commit()
            
            if 'csv_website' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN csv_website TEXT")
                conn.commit()
            
            if 'csv_columns_data' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN csv_columns_data TEXT")
                conn.commit()
            
            if 'csv_row_index' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN csv_row_index INTEGER")
                conn.commit()
            
            if 'lead_status' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN lead_status VARCHAR DEFAULT 'raw_lead'")
                conn.commit()
            
            # Add contacted_date column
            if 'contacted_date' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN contacted_date DATETIME")
                conn.commit()
            
            # Migrate existing lead_status values to new system
            # pending -> raw_lead, reached -> qualified, left_swiped stays as is (or can be removed)
            cursor.execute("UPDATE profiles SET lead_status = 'raw_lead' WHERE lead_status = 'pending' OR lead_status IS NULL")
            cursor.execute("UPDATE profiles SET lead_status = 'qualified' WHERE lead_status = 'reached'")
            conn.commit()
            
            # Add LLM analysis columns
            if 'llm_analysis_what_they_do' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN llm_analysis_what_they_do TEXT")
                conn.commit()
            
            if 'llm_analysis_can_we_pitch' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN llm_analysis_can_we_pitch TEXT")
                conn.commit()
            
            if 'llm_analysis_raw_response' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN llm_analysis_raw_response TEXT")
                conn.commit()
            
            if 'llm_analysis_generated_at' not in columns:
                cursor.execute("ALTER TABLE profiles ADD COLUMN llm_analysis_generated_at DATETIME")
                conn.commit()
            
            # Check if llm_settings table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_settings'")
            if not cursor.fetchone():
                # Create llm_settings table
                cursor.execute("""
                    CREATE TABLE llm_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        section VARCHAR NOT NULL,
                        provider VARCHAR NOT NULL,
                        api_key TEXT,
                        model VARCHAR,
                        system_prompt TEXT,
                        temperature VARCHAR DEFAULT '0.7',
                        max_tokens INTEGER DEFAULT 1000,
                        variables TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Warning: Database migration failed: {e}")
            # Continue anyway - might be a new database
    
    def get_session(self):
        """Get a database session."""
        return self.Session()
    
    def create_job(self, job_id: str, filename: str, total_urls: int) -> Job:
        """Create a new job."""
        session = self.get_session()
        try:
            job = Job(
                id=job_id,
                filename=filename,
                total_urls=total_urls,
                processed=0,
                status='pending',
                created_at=datetime.utcnow()
            )
            session.add(job)
            session.commit()
            return job
        finally:
            session.close()
    
    def create_profile(self, job_id: str, linkedin_url: str, firstname: Optional[str] = None, lastname: Optional[str] = None, website: Optional[str] = None, csv_columns_data: Optional[Dict] = None, csv_row_index: Optional[int] = None) -> Profile:
        """Create a new profile record."""
        session = self.get_session()
        try:
            profile = Profile(
                job_id=job_id,
                linkedin_url=linkedin_url,
                status='pending',
                csv_firstname=firstname,
                csv_lastname=lastname,
                csv_website=website,
                csv_columns_data=csv_columns_data,
                csv_row_index=csv_row_index,
                created_at=datetime.utcnow()
            )
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile
        finally:
            session.close()
    
    def update_profile_step(self, profile_id: int, step: str, data: Dict) -> Profile:
        """Update profile with step data."""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter_by(id=profile_id).first()
            if not profile:
                return None
            
            profile.current_step = step
            profile.updated_at = datetime.utcnow()
            
            # Update step-specific fields
            if step == 'step1':
                profile.step1_browser_connected = datetime.utcnow()
            elif step == 'step2':
                profile.step2_profile_opened = datetime.utcnow()
            elif step == 'step3':
                profile.step3_name = data.get('name')
                profile.step3_company_name = data.get('company_name')
                profile.step3_company_linkedin_url = data.get('company_linkedin_url')
                profile.step3_valid_experience = 'true' if data.get('valid_experience', True) else 'false'
                profile.step3_experience_reason = data.get('experience_reason')
                profile.step3_extracted_at = datetime.utcnow()
            elif step == 'step4':
                profile.step4_company_page_navigated = datetime.utcnow()
                profile.step4_website_url = data.get('website')
                profile.step4_extracted_at = datetime.utcnow()
            elif step == 'step5':
                profile.step5_website_scraped = datetime.utcnow()
                profile.step5_company_description = data.get('company_description')
            elif step == 'step6':
                profile.step6_compiled_at = datetime.utcnow()
                profile.final_result = data
                profile.status = 'completed'
            
            session.commit()
            session.refresh(profile)
            return profile
        finally:
            session.close()
    
    def update_profile_status(self, profile_id: int, status: str, error: Optional[str] = None):
        """Update profile status."""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter_by(id=profile_id).first()
            if profile:
                profile.status = status
                if error:
                    profile.error = error
                profile.updated_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    def update_lead_status(self, profile_id: int, lead_status: str, set_contacted_date: bool = False) -> bool:
        """Update lead management status (raw_lead, qualified, contacted)."""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter_by(id=profile_id).first()
            if profile:
                profile.lead_status = lead_status
                # Set contacted_date when marking as contacted
                if lead_status == 'contacted' and set_contacted_date:
                    profile.contacted_date = datetime.utcnow()
                profile.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def update_job_progress(self, job_id: str, processed: int, status: Optional[str] = None):
        """Update job progress."""
        session = self.get_session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if job:
                job.processed = processed
                if status:
                    job.status = status
                if status == 'processing' and not job.started_at:
                    job.started_at = datetime.utcnow()
                if status in ['completed', 'failed']:
                    job.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        session = self.get_session()
        try:
            return session.query(Job).filter_by(id=job_id).first()
        finally:
            session.close()
    
    def get_job_by_filename(self, filename: str) -> Optional[Job]:
        """Get the most recent incomplete job by filename."""
        session = self.get_session()
        try:
            # Find jobs with same filename that are not completed
            job = session.query(Job).filter(
                Job.filename == filename,
                Job.status.in_(['pending', 'processing', 'failed', 'cancelled'])
            ).order_by(Job.created_at.desc()).first()
            return job
        finally:
            session.close()
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs, ordered by created_at descending."""
        session = self.get_session()
        try:
            return session.query(Job).order_by(Job.created_at.desc()).all()
        finally:
            session.close()
    
    def stop_job(self, job_id: str) -> bool:
        """Stop/cancel a job by setting status to 'cancelled'."""
        session = self.get_session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if job:
                if job.status == 'processing':
                    job.status = 'cancelled'
                    job.completed_at = datetime.utcnow()
                    session.commit()
                    return True
            return False
        finally:
            session.close()
    
    def get_profiles_for_job(self, job_id: str) -> List[Profile]:
        """Get all profiles for a job."""
        session = self.get_session()
        try:
            return session.query(Profile).filter_by(job_id=job_id).order_by(Profile.id).all()
        finally:
            session.close()
    
    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """Get profile by ID."""
        session = self.get_session()
        try:
            return session.query(Profile).filter_by(id=profile_id).first()
        finally:
            session.close()
    
    def update_profile_messages(
        self,
        profile_id: int,
        email: Optional[str] = None,
        linkedin_connection: Optional[str] = None,
        linkedin_followup: Optional[str] = None
    ) -> bool:
        """Update generated messages for a profile."""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter_by(id=profile_id).first()
            if profile:
                if email is not None:
                    profile.generated_email = email
                if linkedin_connection is not None:
                    profile.generated_linkedin_connection = linkedin_connection
                if linkedin_followup is not None:
                    profile.generated_linkedin_followup = linkedin_followup
                profile.messages_generated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating profile messages: {e}")
            return False
        finally:
            session.close()
    
    def update_profile_llm_analysis(
        self,
        profile_id: int,
        what_they_do: Optional[str] = None,
        can_we_pitch: Optional[str] = None,
        raw_response: Optional[Dict] = None
    ) -> bool:
        """Update LLM analysis results for a profile."""
        session = self.get_session()
        try:
            profile = session.query(Profile).filter_by(id=profile_id).first()
            if profile:
                if what_they_do is not None:
                    profile.llm_analysis_what_they_do = what_they_do
                if can_we_pitch is not None:
                    profile.llm_analysis_can_we_pitch = can_we_pitch
                if raw_response is not None:
                    profile.llm_analysis_raw_response = raw_response
                profile.llm_analysis_generated_at = datetime.utcnow()
                profile.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating LLM analysis: {e}")
            return False
        finally:
            session.close()
    
    def get_llm_settings(self, section: str) -> Optional[LLMSettings]:
        """Get LLM settings for a specific section (pending or reached)."""
        session = self.get_session()
        try:
            result = session.query(LLMSettings).filter_by(section=section).first()
            return result
        except Exception as e:
            print(f"Error querying LLM settings: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            session.close()
    
    def save_llm_settings(
        self,
        section: str,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[str] = None,
        max_tokens: Optional[int] = None,
        variables: Optional[Dict] = None
    ) -> LLMSettings:
        """Save or update LLM settings for a section."""
        session = self.get_session()
        try:
            settings = session.query(LLMSettings).filter_by(section=section).first()
            if settings:
                # Update existing
                settings.provider = provider
                if api_key is not None:
                    settings.api_key = api_key
                if model is not None:
                    settings.model = model
                if system_prompt is not None:
                    settings.system_prompt = system_prompt
                if temperature is not None:
                    settings.temperature = temperature
                if max_tokens is not None:
                    settings.max_tokens = max_tokens
                if variables is not None:
                    # Ensure variables is stored as JSON
                    if isinstance(variables, dict):
                        settings.variables = variables
                    else:
                        settings.variables = {}
                settings.updated_at = datetime.utcnow()
            else:
                # Create new
                settings = LLMSettings(
                    section=section,
                    provider=provider,
                    api_key=api_key or '',
                    model=model or '',
                    system_prompt=system_prompt or '',
                    temperature=temperature or '0.7',
                    max_tokens=max_tokens or 1000,
                    variables=variables or {}
                )
                session.add(settings)
            session.commit()
            # Refresh to get the latest data
            session.refresh(settings)
            return settings
        except Exception as e:
            session.rollback()
            print(f"Error saving LLM settings: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            session.close()
    
    def get_currently_processing_profile(self, job_id: str) -> Optional[Profile]:
        """Get the profile currently being processed."""
        session = self.get_session()
        try:
            return session.query(Profile).filter_by(
                job_id=job_id,
                status='processing'
            ).first()
        finally:
            session.close()

