"""Admin Web Interface for LinkedIn Enricher
Allows admins to upload CSV files with LinkedIn URLs and process them."""
import os
import csv
import json
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Optional
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
from database import Database, Profile, LLMSettings
from enricher_with_db import LinkedInEnricherWithDB
from message_generator import MessageGenerator
from llm_service import LLMService

app = Flask(__name__)
# Enable CORS for React frontend
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.urandom(24)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Initialize database
db = Database()

# Store progress callbacks for SSE
progress_callbacks: Dict[str, List] = {}

# Store active job threads for cancellation
active_job_threads: Dict[str, threading.Thread] = {}
job_cancellation_flags: Dict[str, bool] = {}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'


def parse_csv_file(file_path: str) -> List[Dict]:
    """Parse CSV file and extract LinkedIn URLs with all CSV columns."""
    profiles_data = []
    
    try:
        df = pd.read_csv(file_path)
        
        # Find columns (for backward compatibility)
        url_column = None
        firstname_column = None
        lastname_column = None
        website_column = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if url_column is None and any(keyword in col_lower for keyword in ['linkedin', 'url', 'profile', 'link']):
                url_column = col
            if firstname_column is None and any(keyword in col_lower for keyword in ['firstname', 'first_name', 'first name', 'fname']):
                firstname_column = col
            if lastname_column is None and any(keyword in col_lower for keyword in ['lastname', 'last_name', 'last name', 'lname', 'surname']):
                lastname_column = col
            if website_column is None and any(keyword in col_lower for keyword in ['website', 'web', 'site', 'url']) and 'linkedin' not in col_lower:
                website_column = col
        
        # If no specific LinkedIn column found, use first column
        if url_column is None:
            url_column = df.columns[0]
        
        print(f"Detected CSV columns: {list(df.columns)}")
        print(f"Using '{url_column}' as LinkedIn URL column")
        
        # Extract data for each row
        for idx, row in df.iterrows():
            url_str = str(row[url_column]).strip() if pd.notna(row[url_column]) else ''
            # More flexible LinkedIn URL detection
            if url_str and ('linkedin.com' in url_str.lower() or 'linkedin' in url_str.lower()):
                firstname = str(row[firstname_column]).strip() if firstname_column and pd.notna(row.get(firstname_column)) else None
                lastname = str(row[lastname_column]).strip() if lastname_column and pd.notna(row.get(lastname_column)) else None
                website = str(row[website_column]).strip() if website_column and pd.notna(row.get(website_column)) else None
                
                # Clean website URL
                if website:
                    website = website.strip()
                    if website and not website.startswith(('http://', 'https://')):
                        website = 'https://' + website
                
                # Ensure LinkedIn URL has proper format
                if not url_str.startswith(('http://', 'https://')):
                    url_str = 'https://' + url_str.lstrip('/')
                
                # Store ALL CSV columns in a dictionary
                csv_columns_data = {}
                for col in df.columns:
                    value = row[col]
                    # Convert to string and clean up
                    if pd.notna(value):
                        csv_columns_data[col] = str(value).strip()
                    else:
                        csv_columns_data[col] = None
                
                profiles_data.append({
                    'linkedin_url': url_str,
                    'firstname': firstname if firstname else None,
                    'lastname': lastname if lastname else None,
                    'website': website if website else None,
                    'csv_columns_data': csv_columns_data  # Store all columns
                })
        
        print(f"Parsed {len(profiles_data)} profiles from CSV")
        return profiles_data
    
    except Exception as e:
        print(f"Error parsing CSV with pandas: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: try standard CSV reader
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Get headers
                
                print(f"CSV Headers: {headers}")
                
                # Find column indices
                url_idx = 0
                firstname_idx = None
                lastname_idx = None
                website_idx = None
                
                for i, header in enumerate(headers):
                    header_lower = header.lower().strip()
                    if any(keyword in header_lower for keyword in ['linkedin', 'url', 'profile', 'link']):
                        url_idx = i
                    if firstname_idx is None and any(keyword in header_lower for keyword in ['firstname', 'first_name', 'first name', 'fname']):
                        firstname_idx = i
                    if lastname_idx is None and any(keyword in header_lower for keyword in ['lastname', 'last_name', 'last name', 'lname', 'surname']):
                        lastname_idx = i
                    if website_idx is None and any(keyword in header_lower for keyword in ['website', 'web', 'site']) and 'linkedin' not in header_lower:
                        website_idx = i
                
                print(f"Using column index {url_idx} for LinkedIn URLs")
                
                for row_num, row in enumerate(reader, start=2):
                    if row and len(row) > url_idx:
                        url_str = str(row[url_idx]).strip() if row[url_idx] else ''
                        # More flexible LinkedIn URL detection
                        if url_str and ('linkedin.com' in url_str.lower() or 'linkedin' in url_str.lower()):
                            firstname = str(row[firstname_idx]).strip() if firstname_idx and len(row) > firstname_idx and row[firstname_idx] else None
                            lastname = str(row[lastname_idx]).strip() if lastname_idx and len(row) > lastname_idx and row[lastname_idx] else None
                            website = str(row[website_idx]).strip() if website_idx and len(row) > website_idx and row[website_idx] else None
                            
                            if website and not website.startswith(('http://', 'https://')):
                                website = 'https://' + website
                            
                            # Ensure LinkedIn URL has proper format
                            if not url_str.startswith(('http://', 'https://')):
                                url_str = 'https://' + url_str.lstrip('/')
                            
                            # Store ALL CSV columns in a dictionary
                            csv_columns_data = {}
                            for i, col in enumerate(headers):
                                if i < len(row):
                                    value = row[i]
                                    csv_columns_data[col] = str(value).strip() if value else None
                                else:
                                    csv_columns_data[col] = None
                            
                            profiles_data.append({
                                'linkedin_url': url_str,
                                'firstname': firstname if firstname else None,
                                'lastname': lastname if lastname else None,
                                'website': website if website else None,
                                'csv_columns_data': csv_columns_data  # Store all columns
                            })
                        elif url_str:
                            print(f"Row {row_num}: Skipping non-LinkedIn URL: {url_str[:50]}")
        except Exception as e2:
            print(f"Error with fallback CSV parsing: {e2}")
            import traceback
            traceback.print_exc()
        
        print(f"Fallback parsing found {len(profiles_data)} profiles")
        return profiles_data


def process_job_background(job_id: str, config: Dict):
    """Process job in background thread."""
    try:
        job = db.get_job(job_id)
        if not job:
            return
        
        # Initialize cancellation flag
        job_cancellation_flags[job_id] = False
        
        db.update_job_progress(job_id, 0, 'processing')
        
        # Get all profiles for this job
        profiles = db.get_profiles_for_job(job_id)
        
        # Filter out already completed profiles for resume functionality
        profiles_to_process = [p for p in profiles if p.status != 'completed']
        completed_count = len(profiles) - len(profiles_to_process)
        
        if completed_count > 0:
            print(f"Resuming job: {completed_count} profiles already completed, processing {len(profiles_to_process)} remaining")
        
        debug_port = config.get('debug_port', 9222)
        max_parallel = config.get('max_parallel', 5)
        wait_time = config.get('wait_time', 5)
        
        # Process each profile (skip already completed ones)
        for i, profile in enumerate(profiles_to_process):
            # Check for cancellation
            if job_cancellation_flags.get(job_id, False):
                print(f"Job {job_id} cancelled by user")
                db.update_job_progress(job_id, i, 'cancelled')
                # Mark remaining profiles as cancelled
                for remaining_profile in profiles[i:]:
                    if remaining_profile.status == 'pending':
                        db.update_profile_status(remaining_profile.id, 'cancelled', 'Job was cancelled by user')
                break
            
            try:
                # Create progress callback
                def progress_callback(step: str, data: dict):
                    # Check for cancellation during processing
                    if job_cancellation_flags.get(job_id, False):
                        return
                    # Store progress in database
                    if step in ['step1', 'step2', 'step3', 'step4', 'step5', 'step6']:
                        db.update_profile_step(profile.id, step, data)
                    # Notify SSE clients
                    notify_progress(job_id, profile.id, step, data)
                
                # Initialize enricher with database
                enricher = LinkedInEnricherWithDB(
                    debug_port=debug_port,
                    max_parallel=1,
                    wait_time=wait_time,
                    db=db,
                    profile_id=profile.id,
                    progress_callback=progress_callback
                )
                
                # Update profile status
                db.update_profile_status(profile.id, 'processing')
                
                # Check again before processing
                if job_cancellation_flags.get(job_id, False):
                    enricher.disconnect()
                    db.update_profile_status(profile.id, 'cancelled', 'Job was cancelled by user')
                    break
                
                # Check if website is provided from CSV - if so, skip to step 5
                if profile.csv_website:
                    # Skip steps 1-4, go directly to step 5
                    result = enricher.enrich_profile_skip_to_step5(
                        profile.linkedin_url,
                        profile.csv_firstname,
                        profile.csv_lastname,
                        profile.csv_website
                    )
                else:
                    # Normal enrichment process (all steps)
                    result = enricher.enrich_profile(profile.linkedin_url)
                
                # Check for cancellation after processing
                if job_cancellation_flags.get(job_id, False):
                    enricher.disconnect()
                    db.update_profile_status(profile.id, 'cancelled', 'Job was cancelled by user')
                    break
                
                # Save final result
                db.update_profile_step(profile.id, 'step6', result.model_dump())
                db.update_profile_status(profile.id, 'completed')
                
                # Disconnect
                enricher.disconnect()
                
                # Update job progress (include already completed profiles)
                db.update_job_progress(job_id, completed_count + i + 1)
                
            except Exception as e:
                error_msg = str(e)
                db.update_profile_status(profile.id, 'failed', error_msg)
                print(f"Error processing {profile.linkedin_url}: {error_msg}")
                import traceback
                traceback.print_exc()
                
                # If it's a Chrome connection error, provide helpful message
                if "Chrome" in error_msg or "9222" in error_msg or "remote-debugging" in error_msg:
                    print(f"\n⚠️  Chrome Connection Issue:")
                    print(f"   Please ensure Chrome is running with remote debugging enabled.")
                    print(f"   Run: ./setup_chrome.sh")
                    print(f"   Or manually start Chrome with: --remote-debugging-port=9222\n")
        
        # Mark job as completed only if not cancelled
        if not job_cancellation_flags.get(job_id, False):
            # Get final count of completed profiles
            final_profiles = db.get_profiles_for_job(job_id)
            completed_final = sum(1 for p in final_profiles if p.status == 'completed')
            db.update_job_progress(job_id, completed_final, 'completed')
        
        # Cleanup
        if job_id in job_cancellation_flags:
            del job_cancellation_flags[job_id]
        if job_id in active_job_threads:
            del active_job_threads[job_id]
        
    except Exception as e:
        db.update_job_progress(job_id, 0, 'failed')
        print(f"Job processing failed: {e}")
        # Cleanup
        if job_id in job_cancellation_flags:
            del job_cancellation_flags[job_id]
        if job_id in active_job_threads:
            del active_job_threads[job_id]


def notify_progress(job_id: str, profile_id: int, step: str, data: dict):
    """Notify all SSE clients about progress."""
    if job_id in progress_callbacks:
        for queue in progress_callbacks[job_id]:
            try:
                queue.append({
                    'job_id': job_id,
                    'profile_id': profile_id,
                    'step': step,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            except:
                pass


@app.route('/')
def index():
    """Main admin page - now serves API only, frontend is separate."""
    return jsonify({'message': 'LinkedIn Enricher API', 'version': '1.0.0'})


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CSV file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(file_path)
        
        # Parse CSV
        profiles_data = parse_csv_file(file_path)
        
        if not profiles_data:
            # Try to provide more helpful error message
            try:
                df = pd.read_csv(file_path)
                return jsonify({
                    'error': f'No LinkedIn URLs found in CSV file. Found columns: {list(df.columns)}. Please ensure your CSV has a column with LinkedIn URLs.'
                }), 400
            except:
                return jsonify({
                    'error': 'No LinkedIn URLs found in CSV file. Please check that your CSV file contains LinkedIn URLs in one of the columns.'
                }), 400
        
        # Check if there's an existing incomplete job with the same filename
        existing_job = db.get_job_by_filename(filename)
        resume_mode = False
        
        if existing_job:
            # Check if we should resume
            existing_profiles = db.get_profiles_for_job(existing_job.id)
            completed_count = sum(1 for p in existing_profiles if p.status == 'completed')
            
            # If job is incomplete and has some progress, offer to resume
            if existing_job.status != 'completed' and completed_count < len(existing_profiles):
                resume_mode = True
                job_id = existing_job.id
                
                # Get already processed row indices
                processed_indices = {p.csv_row_index for p in existing_profiles if p.csv_row_index is not None and p.status == 'completed'}
                
                # Only create profiles for rows that haven't been processed
                new_profiles_count = 0
                for idx, profile_data in enumerate(profiles_data):
                    if idx not in processed_indices:
                        db.create_profile(
                            job_id,
                            profile_data['linkedin_url'],
                            firstname=profile_data.get('firstname'),
                            lastname=profile_data.get('lastname'),
                            website=profile_data.get('website'),
                            csv_columns_data=profile_data.get('csv_columns_data'),
                            csv_row_index=idx
                        )
                        new_profiles_count += 1
                
                # Update job total if needed (in case CSV has more rows now)
                if len(profiles_data) > existing_job.total_urls:
                    from database import Job
                    session = db.get_session()
                    try:
                        job = session.query(Job).filter_by(id=existing_job.id).first()
                        if job:
                            job.total_urls = len(profiles_data)
                            session.commit()
                    finally:
                        session.close()
                
                return jsonify({
                    'job_id': job_id,
                    'total_urls': len(profiles_data),
                    'processed': completed_count,
                    'resumed': True,
                    'new_profiles_added': new_profiles_count,
                    'message': f'Resuming job. {completed_count} already processed, {new_profiles_count} new rows added.'
                })
        
        # Create new job
        job_id = str(uuid.uuid4())
        db.create_job(job_id, filename, len(profiles_data))
        
        # Create profiles in database with row indices
        for idx, profile_data in enumerate(profiles_data):
            db.create_profile(
                job_id,
                profile_data['linkedin_url'],
                firstname=profile_data.get('firstname'),
                lastname=profile_data.get('lastname'),
                website=profile_data.get('website'),
                csv_columns_data=profile_data.get('csv_columns_data'),
                csv_row_index=idx
            )
        
        return jsonify({
            'job_id': job_id,
            'total_urls': len(profiles_data),
            'processed': 0,
            'resumed': False,
            'message': f'File uploaded successfully. Found {len(profiles_data)} LinkedIn URLs.'
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/process/<job_id>', methods=['POST'])
def process_job(job_id: str):
    """Start processing a job."""
    job = db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status == 'processing':
        return jsonify({'error': 'Job is already being processed'}), 400
    
    # Get configuration from request (handle both JSON and empty body)
    try:
        config = request.get_json() or {}
    except:
        config = {}
    
    # Check if this is a resume (has completed profiles)
    profiles = db.get_profiles_for_job(job_id)
    completed_count = sum(1 for p in profiles if p.status == 'completed')
    is_resume = completed_count > 0
    
    # Start processing in background thread
    thread = threading.Thread(target=process_job_background, args=(job_id, config))
    thread.daemon = True
    thread.start()
    
    # Store thread reference for potential cancellation
    active_job_threads[job_id] = thread
    
    message = 'Job processing started'
    if is_resume:
        message = f'Job resumed. {completed_count} profiles already completed, processing remaining {len(profiles) - completed_count} profiles.'
    
    return jsonify({
        'status': 'processing',
        'message': message,
        'resumed': is_resume,
        'already_processed': completed_count,
        'remaining': len(profiles) - completed_count
    })


@app.route('/resume-job/<job_id>', methods=['POST'])
def resume_job(job_id: str):
    """Resume a failed or incomplete job."""
    job = db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status == 'processing':
        return jsonify({'error': 'Job is already being processed'}), 400
    
    if job.status == 'completed':
        return jsonify({'error': 'Job is already completed'}), 400
    
    # Get profiles to see progress
    profiles = db.get_profiles_for_job(job_id)
    completed_count = sum(1 for p in profiles if p.status == 'completed')
    remaining_count = len(profiles) - completed_count
    
    if remaining_count == 0:
        # All profiles are completed, just mark job as completed
        db.update_job_progress(job_id, completed_count, 'completed')
        return jsonify({
            'status': 'completed',
            'message': 'All profiles are already completed',
            'processed': completed_count
        })
    
    # Get configuration from request
    try:
        config = request.get_json() or {}
    except:
        config = {}
    
    # Start processing in background thread
    thread = threading.Thread(target=process_job_background, args=(job_id, config))
    thread.daemon = True
    thread.start()
    
    # Store thread reference for potential cancellation
    active_job_threads[job_id] = thread
    
    return jsonify({
        'status': 'processing',
        'message': f'Job resumed. Processing {remaining_count} remaining profiles.',
        'resumed': True,
        'already_processed': completed_count,
        'remaining': remaining_count
    })


@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """Get job status."""
    job = db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Get current processing profile
    current_profile = db.get_currently_processing_profile(job_id)
    current_profile_data = None
    if current_profile:
        current_profile_data = {
            'id': current_profile.id,
            'linkedin_url': current_profile.linkedin_url,
            'current_step': current_profile.current_step,
            'name': current_profile.step3_name,
            'company': current_profile.step3_company_name,
            'valid_experience': current_profile.step3_valid_experience == 'true' if current_profile.step3_valid_experience else True,
            'experience_reason': current_profile.step3_experience_reason,
            'website': current_profile.step4_website_url,
            'company_description': current_profile.step5_company_description,
            'status': current_profile.status
        }
    
    return jsonify({
        'id': job.id,
        'status': job.status,
        'processed': job.processed,
        'total': job.total_urls,
        'filename': job.filename,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'current_profile': current_profile_data
    })


@app.route('/stream/<job_id>')
def stream_progress(job_id: str):
    """Server-Sent Events stream for real-time progress updates."""
    def generate():
        # Register callback queue
        queue = []
        progress_callbacks.setdefault(job_id, []).append(queue)
        
        try:
            # Send initial status
            job = db.get_job(job_id)
            if job:
                yield f"data: {json.dumps({'type': 'status', 'status': job.status, 'processed': job.processed, 'total': job.total_urls})}\n\n"
            
            # Stream updates
            while True:
                if queue:
                    event = queue.pop(0)
                    yield f"data: {json.dumps(event)}\n\n"
                else:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    import time
                    time.sleep(1)
        finally:
            # Cleanup
            if job_id in progress_callbacks:
                if queue in progress_callbacks[job_id]:
                    progress_callbacks[job_id].remove(queue)
                if not progress_callbacks[job_id]:
                    del progress_callbacks[job_id]
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/profiles/<job_id>', methods=['GET'])
def get_profiles(job_id: str):
    """Get all profiles for a job with their current data."""
    profiles = db.get_profiles_for_job(job_id)
    
    profiles_data = []
    for profile in profiles:
        profiles_data.append({
            'id': profile.id,
            'linkedin_url': profile.linkedin_url,
            'status': profile.status,
            'current_step': profile.current_step,
            'name': profile.step3_name,
            'company_name': profile.step3_company_name,
            'company_linkedin_url': profile.step3_company_linkedin_url,
            'valid_experience': profile.step3_valid_experience == 'true' if profile.step3_valid_experience else True,
            'experience_reason': profile.step3_experience_reason,
            'website': profile.step4_website_url,
            'company_description': profile.step5_company_description,  # Send full description
            'error': profile.error,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
            # Generated messages
            'generated_email': profile.generated_email,
            'generated_linkedin_connection': profile.generated_linkedin_connection,
            'generated_linkedin_followup': profile.generated_linkedin_followup,
            'messages_generated_at': profile.messages_generated_at.isoformat() if profile.messages_generated_at else None,
            'csv_columns_data': (json.loads(profile.csv_columns_data) if isinstance(profile.csv_columns_data, str) and profile.csv_columns_data else profile.csv_columns_data) or {}
        })
    
    return jsonify({'profiles': profiles_data})


@app.route('/generate-messages/<int:profile_id>', methods=['POST'])
def generate_messages(profile_id: int):
    """Generate sales messages for a profile using OpenAI."""
    try:
        profile = db.get_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Check if profile is completed and has required data
        if profile.status != 'completed':
            return jsonify({'error': 'Profile must be completed to generate messages'}), 400
        
        if not profile.step3_name:
            return jsonify({'error': 'Profile name is required'}), 400
        
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured. Set OPENAI_API_KEY environment variable.'}), 500
        
        # Initialize message generator
        generator = MessageGenerator(api_key=api_key)
        
        # Generate messages
        messages = generator.generate_messages(
            client_name=profile.step3_name,
            company_name=profile.step3_company_name,
            company_description=profile.step5_company_description,
            website=profile.step4_website_url
        )
        
        # Save messages to database
        db.update_profile_messages(
            profile_id=profile_id,
            email=messages.get('email'),
            linkedin_connection=messages.get('linkedin_connection'),
            linkedin_followup=messages.get('linkedin_followup')
        )
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Error generating messages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate messages: {str(e)}'}), 500


@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id: str):
    """Get job results."""
    profiles = db.get_profiles_for_job(job_id)
    
    results = []
    errors = []
    
    for profile in profiles:
        if profile.final_result:
            results.append(profile.final_result)
        elif profile.error:
            errors.append({
                'url': profile.linkedin_url,
                'error': profile.error
            })
    
    return jsonify({
        'results': results,
        'errors': errors,
        'status': db.get_job(job_id).status if db.get_job(job_id) else 'unknown'
    })


@app.route('/download/<job_id>/<format>', methods=['GET'])
def download_results(job_id: str, format: str):
    """Download results in specified format (csv or json)."""
    job = db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    profiles = db.get_profiles_for_job(job_id)
    results = [p.final_result for p in profiles if p.final_result]
    
    if format == 'json':
        output = json.dumps(results, indent=2, ensure_ascii=False)
        return output, 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': f'attachment; filename={job_id}_results.json'
        }
    
    elif format == 'csv':
        if not results:
            return jsonify({'error': 'No results to export'}), 400
        
        csv_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_results.csv")
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        return send_file(csv_file, as_attachment=True, download_name=f"{job_id}_results.csv")
    
    else:
        return jsonify({'error': 'Invalid format. Use csv or json'}), 400


@app.route('/active-jobs', methods=['GET'])
def get_active_jobs():
    """Get all jobs with their status."""
    try:
        jobs = db.get_all_jobs()
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job.id,
                'filename': job.filename,
                'status': job.status,
                'processed': job.processed,
                'total': job.total_urls,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error': job.error
            })
        return jsonify({'jobs': jobs_data})
    except Exception as e:
        print(f"Error getting active jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get jobs: {str(e)}'}), 500


@app.route('/stop-job/<job_id>', methods=['POST'])
def stop_job(job_id: str):
    """Stop/cancel a running job."""
    try:
        job = db.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status not in ['processing', 'pending']:
            return jsonify({'error': f'Job is already {job.status}'}), 400
        
        # Set cancellation flag
        job_cancellation_flags[job_id] = True
        
        # Update job status in database
        success = db.stop_job(job_id)
        
        if success:
            return jsonify({
                'status': 'cancelled',
                'message': 'Job cancellation requested'
            })
        else:
            return jsonify({'error': 'Failed to stop job'}), 500
            
    except Exception as e:
        print(f"Error stopping job: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to stop job: {str(e)}'}), 500


@app.route('/enriched-profiles', methods=['GET'])
def get_enriched_profiles():
    """Get enriched (completed) profiles from the database with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        session = db.get_session()
        try:
            # Calculate offset
            offset = (page - 1) * limit
            
            # Get lead_status filter
            lead_status_filter = request.args.get('lead_status', None)
            
            # Build base query
            base_query = session.query(Profile).filter_by(status='completed')
            
            # Apply lead_status filter
            if lead_status_filter:
                query = base_query.filter_by(lead_status=lead_status_filter)
            else:
                # Default to raw_lead if no filter specified
                query = base_query.filter((Profile.lead_status == 'raw_lead') | (Profile.lead_status == None))
            
            # Get total count with same filter
            total = query.count()
            total_pages = (total + limit - 1) // limit  # Ceiling division
            
            # Get paginated profiles (latest 50 first, then next pages)
            profiles = query.order_by(Profile.updated_at.desc()).offset(offset).limit(limit).all()
            
            profiles_data = []
            for profile in profiles:
                profiles_data.append({
                    'id': profile.id,
                    'linkedin_url': profile.linkedin_url,
                    'name': profile.step3_name,
                    'csv_firstname': profile.csv_firstname,
                    'csv_lastname': profile.csv_lastname,
                    'csv_website': profile.csv_website,
                    'csv_columns_data': (json.loads(profile.csv_columns_data) if isinstance(profile.csv_columns_data, str) and profile.csv_columns_data else profile.csv_columns_data) or {},
                    'company_name': profile.step3_company_name,
                    'website': profile.step4_website_url or profile.csv_website,
                    'company_description': profile.step5_company_description,
                    'lead_status': profile.lead_status or 'raw_lead',
                    'generated_email': profile.generated_email,
                    'generated_linkedin_connection': profile.generated_linkedin_connection,
                    'generated_linkedin_followup': profile.generated_linkedin_followup,
                    'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
                    'messages_generated_at': profile.messages_generated_at.isoformat() if profile.messages_generated_at else None,
                    'custom_columns_data': (json.loads(profile.custom_columns_data) if isinstance(profile.custom_columns_data, str) and profile.custom_columns_data else profile.custom_columns_data) or {},
                    # LLM Analysis results
                    'llm_analysis_what_they_do': profile.llm_analysis_what_they_do,
                    'llm_analysis_can_we_pitch': profile.llm_analysis_can_we_pitch,
                    'llm_analysis_generated_at': profile.llm_analysis_generated_at.isoformat() if profile.llm_analysis_generated_at else None,
                    # Contacted date
                    'contacted_date': profile.contacted_date.isoformat() if profile.contacted_date else None
                })
            
            return jsonify({
                'profiles': profiles_data,
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages
            })
        finally:
            session.close()
    except Exception as e:
        print(f"Error getting enriched profiles: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get enriched profiles: {str(e)}'}), 500


@app.route('/generate-column-message/<int:profile_id>', methods=['POST'])
def generate_column_message(profile_id: int):
    """Generate message for a custom column."""
    try:
        data = request.get_json()
        column_name = data.get('column_name')
        column_type = data.get('column_type')
        max_length = data.get('max_length', 300)
        first_connect_message = data.get('first_connect_message', '')
        
        profile = db.get_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        if profile.status != 'completed':
            return jsonify({'error': 'Profile must be completed'}), 400
        
        if not profile.step3_name:
            return jsonify({'error': 'Profile name is required'}), 400
        
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        generator = MessageGenerator(api_key=api_key)
        
        if column_type == '1st_connect':
            # Generate 300 character connection request
            messages = generator.generate_messages(
                client_name=profile.step3_name,
                company_name=profile.step3_company_name,
                company_description=profile.step5_company_description,
                website=profile.step4_website_url
            )
            message = messages.get('linkedin_connection', '')
            # Ensure it's exactly 300 characters or less
            if len(message) > max_length:
                message = message[:max_length].rsplit(' ', 1)[0]  # Cut at word boundary
            
            return jsonify({'message': message})
            
        elif column_type == 'after_connect':
            # Generate follow-up using first connect message as context
            if not first_connect_message:
                return jsonify({'error': 'First connect message is required'}), 400
            
            # Use OpenAI to generate follow-up based on first message
            prompt = f"""You previously sent this LinkedIn connection request to {profile.step3_name} at {profile.step3_company_name or 'their company'}:

"{first_connect_message}"

They accepted your connection request. Now generate a professional follow-up message (2-3 sentences) that:
- Thanks them for connecting
- References something from your initial message or their company
- Provides value or suggests next steps
- Is warm and professional

Generate only the message text, no additional formatting."""
            
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional sales outreach specialist. Generate concise, professional follow-up messages."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                message = response.choices[0].message.content.strip()
                return jsonify({'message': message})
            except Exception as e:
                print(f"Error generating follow-up: {e}")
                return jsonify({'error': f'Failed to generate message: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Invalid column type'}), 400
            
    except Exception as e:
        print(f"Error generating column message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate message: {str(e)}'}), 500


@app.route('/update-lead-status/<int:profile_id>', methods=['POST'])
def update_lead_status(profile_id: int):
    """Update lead management status (raw_lead, qualified, contacted)."""
    try:
        data = request.get_json()
        lead_status = data.get('lead_status')
        
        if lead_status not in ['raw_lead', 'qualified', 'contacted']:
            return jsonify({'error': 'Invalid lead_status. Must be raw_lead, qualified, or contacted'}), 400
        
        # Set contacted_date when marking as contacted
        set_contacted_date = (lead_status == 'contacted')
        
        success = db.update_lead_status(profile_id, lead_status, set_contacted_date=set_contacted_date)
        
        if success:
            # Get updated profile to return contacted_date
            profile = db.get_profile(profile_id)
            return jsonify({
                'success': True, 
                'lead_status': lead_status,
                'contacted_date': profile.contacted_date.isoformat() if profile and profile.contacted_date else None
            })
        else:
            return jsonify({'error': 'Profile not found'}), 404
    except Exception as e:
        print(f"Error updating lead status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to update lead status: {str(e)}'}), 500


@app.route('/save-column-value/<int:profile_id>', methods=['POST'])
def save_column_value(profile_id: int):
    """Save a custom column value for a profile."""
    try:
        data = request.get_json()
        column_name = data.get('column_name')
        value = data.get('value', '')
        
        profile = db.get_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Update custom_columns_data
        import json
        custom_data = profile.custom_columns_data or {}
        if isinstance(custom_data, str):
            custom_data = json.loads(custom_data) if custom_data else {}
        custom_data[column_name] = value
        
        session = db.get_session()
        try:
            profile.custom_columns_data = custom_data
            session.commit()
            return jsonify({'success': True})
        finally:
            session.close()
            
    except Exception as e:
        print(f"Error saving column value: {e}")
        return jsonify({'error': f'Failed to save: {str(e)}'}), 500


@app.route('/llm-settings/<section>', methods=['GET'])
def get_llm_settings(section: str):
    """Get LLM settings for a section (pending or reached)."""
    try:
        if section not in ['pending', 'reached']:
            return jsonify({'error': 'Invalid section. Use "pending" or "reached"'}), 400
        
        settings = db.get_llm_settings(section)
        if not settings:
            # Return default empty settings if none exist
            return jsonify({
                'section': section,
                'provider': '',
                'api_key': '',
                'model': '',
                'system_prompt': '',
                'temperature': '0.7',
                'max_tokens': 1000,
                'variables': {}
            }), 200
        
        # Handle JSON variables if stored as string
        variables = settings.variables
        if isinstance(variables, str):
            try:
                import json
                variables = json.loads(variables) if variables else {}
            except:
                variables = {}
        
        return jsonify({
            'section': settings.section,
            'provider': settings.provider or '',
            'api_key': settings.api_key or '',
            'model': settings.model or '',
            'system_prompt': settings.system_prompt or '',
            'temperature': settings.temperature or '0.7',
            'max_tokens': settings.max_tokens or 1000,
            'variables': variables
        }), 200
    except Exception as e:
        print(f"Error getting LLM settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to get settings: {str(e)}'}), 500


@app.route('/llm-settings/<section>', methods=['POST'])
def save_llm_settings(section: str):
    """Save LLM settings for a section (pending or reached)."""
    try:
        if section not in ['pending', 'reached']:
            return jsonify({'error': 'Invalid section. Use "pending" or "reached"'}), 400
        
        data = request.get_json()
        provider = data.get('provider', '').lower()
        if provider not in ['openai', 'gemini']:
            return jsonify({'error': 'Invalid provider. Use "openai" or "gemini"'}), 400
        
        settings = db.save_llm_settings(
            section=section,
            provider=provider,
            api_key=data.get('api_key', ''),
            model=data.get('model', ''),
            system_prompt=data.get('system_prompt', ''),
            temperature=data.get('temperature', '0.7'),
            max_tokens=data.get('max_tokens', 1000),
            variables=data.get('variables', {})
        )
        
        return jsonify({
            'success': True,
            'message': f'LLM settings for {section} section saved successfully'
        })
    except Exception as e:
        print(f"Error saving LLM settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to save settings: {str(e)}'}), 500


@app.route('/generate-lead-response/<int:profile_id>', methods=['POST'])
def generate_lead_response(profile_id: int):
    """Generate LLM response for a lead based on their status (pending or reached)."""
    try:
        data = request.get_json()
        section = data.get('section', 'pending')  # 'pending' or 'reached'
        
        if section not in ['pending', 'reached']:
            return jsonify({'error': 'Invalid section. Use "pending" or "reached"'}), 400
        
        profile = db.get_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Get LLM settings for the section
        settings = db.get_llm_settings(section)
        if not settings or not settings.api_key:
            return jsonify({
                'error': f'LLM settings not configured for {section} section. Please configure in Settings.'
            }), 400
        
        # Initialize LLM service
        llm_service = LLMService(
            provider=settings.provider,
            api_key=settings.api_key,
            model=settings.model,
            temperature=float(settings.temperature or 0.7),
            max_tokens=settings.max_tokens or 1000
        )
        
        # Get profile data
        full_name = profile.step3_name or f"{profile.csv_firstname or ''} {profile.csv_lastname or ''}".strip()
        if not full_name:
            return jsonify({'error': 'Profile name not available'}), 400
        
        company_name = profile.step3_company_name
        company_description = profile.step5_company_description
        
        # For pending leads, use company description as about_section
        # This provides context about what the company does
        about_section = company_description  # Use company description as about section for analysis
        
        # Generate response based on section
        if section == 'pending':
            # Generate analysis/answers for pending leads
            response = llm_service.generate_for_pending(
                full_name=full_name,
                about_section=about_section,  # Now includes company description
                company_name=company_name,
                system_prompt=settings.system_prompt or '',
                variables=settings.variables or {}
            )
            
            # Try to parse and return as JSON if possible
            import json
            parsed_response = None
            try:
                # If response is already a dict/JSON, return as-is
                if isinstance(response, dict):
                    parsed_response = response
                else:
                    # Try to parse as JSON string
                    parsed_response = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, keep as text
                parsed_response = response
            
            # Extract and save analysis results to database
            what_they_do = ''
            can_we_pitch = ''
            
            if isinstance(parsed_response, dict):
                # Extract "What they do"
                what_they_do = parsed_response.get('What they do') or \
                               parsed_response.get('what_they_do') or \
                               parsed_response.get('What They Do') or \
                               parsed_response.get('whatTheyDo') or ''
                
                # Extract "Can we pitch Spheron?"
                pitch_data = parsed_response.get('Can we pitch Spheron?') or \
                            parsed_response.get('can_we_pitch_spheron') or \
                            parsed_response.get('Can We Pitch Spheron?') or \
                            parsed_response.get('canWePitchSpheron')
                
                if pitch_data:
                    if isinstance(pitch_data, dict):
                        verdict = pitch_data.get('Verdict') or pitch_data.get('verdict') or ''
                        reasoning = pitch_data.get('Reasoning') or pitch_data.get('reasoning') or ''
                        hook = pitch_data.get('The Hook') or pitch_data.get('the_hook') or ''
                        pitch_angle = pitch_data.get('The Pitch Angle') or pitch_data.get('the_pitch_angle') or ''
                        
                        parts = []
                        if verdict:
                            parts.append(f"Verdict: {verdict}")
                        if reasoning:
                            parts.append(f"Reasoning: {reasoning}")
                        if pitch_angle:
                            parts.append(f"The Pitch Angle: {pitch_angle}")
                        if hook:
                            parts.append(f"The Hook: {hook}")
                        
                        can_we_pitch = '\n\n'.join(parts) if parts else str(pitch_data)
                    else:
                        can_we_pitch = str(pitch_data)
            
            # Save to database
            db.update_profile_llm_analysis(
                profile_id=profile_id,
                what_they_do=what_they_do,
                can_we_pitch=can_we_pitch,
                raw_response=parsed_response if isinstance(parsed_response, dict) else None
            )
            
            return jsonify({
                'success': True,
                'section': 'pending',
                'response': parsed_response
            })
        
        else:  # reached
            # Generate email and LinkedIn messages for reached leads
            messages = llm_service.generate_for_reached(
                full_name=full_name,
                about_section=about_section,
                company_name=company_name,
                company_description=company_description,
                system_prompt=settings.system_prompt or '',
                variables=settings.variables or {}
            )
            
            # Save to profile
            db.update_profile_messages(
                profile_id=profile_id,
                email=messages.get('email'),
                linkedin_connection=messages.get('linkedin_message'),
                linkedin_followup=None  # Can be generated separately if needed
            )
            
            return jsonify({
                'success': True,
                'section': 'reached',
                'email': messages.get('email'),
                'linkedin_message': messages.get('linkedin_message')
            })
            
    except Exception as e:
        print(f"Error generating lead response: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate response: {str(e)}'}), 500


@app.route('/test-llm-settings/<section>', methods=['POST'])
def test_llm_settings(section: str):
    """Test LLM settings with dummy data to verify configuration."""
    try:
        if section not in ['pending', 'reached']:
            return jsonify({'error': 'Invalid section. Use "pending" or "reached"'}), 400
        
        data = request.get_json()
        provider = data.get('provider', '').lower()
        api_key = data.get('api_key', '')
        model = data.get('model', '')
        system_prompt = data.get('system_prompt', '')
        temperature = float(data.get('temperature', '0.7'))
        max_tokens = int(data.get('max_tokens', 1000))
        variables = data.get('variables', {})
        
        if not provider or provider not in ['openai', 'gemini']:
            return jsonify({'error': 'Invalid provider. Use "openai" or "gemini"'}), 400
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        # Initialize LLM service with provided settings
        llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            model=model or None,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Use dummy/test data based on section
        if section == 'pending':
            # Dummy data for pending leads test
            dummy_full_name = "John Smith"
            dummy_company_name = "Tech Innovations Inc."
            dummy_about_section = "Experienced software engineer with 10+ years in cloud infrastructure and DevOps. Passionate about building scalable solutions."
            
            # Generate test response
            response = llm_service.generate_for_pending(
                full_name=dummy_full_name,
                about_section=dummy_about_section,
                company_name=dummy_company_name,
                system_prompt=system_prompt or '',
                variables=variables
            )
            
            return jsonify({
                'success': True,
                'section': 'pending',
                'test_data': {
                    'full_name': dummy_full_name,
                    'company_name': dummy_company_name,
                    'about_section': dummy_about_section
                },
                'response': response
            })
        
        else:  # reached
            # Dummy data for reached leads test
            dummy_full_name = "Sarah Johnson"
            dummy_company_name = "Digital Solutions LLC"
            dummy_about_section = "Marketing director with expertise in B2B SaaS growth strategies. Led campaigns that increased revenue by 300%."
            dummy_company_description = "Digital Solutions LLC is a leading provider of cloud-based marketing automation tools. We help businesses streamline their marketing workflows, improve customer engagement, and drive revenue growth through AI-powered insights and automation."
            
            # Generate test messages
            messages = llm_service.generate_for_reached(
                full_name=dummy_full_name,
                about_section=dummy_about_section,
                company_name=dummy_company_name,
                company_description=dummy_company_description,
                system_prompt=system_prompt or '',
                variables=variables
            )
            
            return jsonify({
                'success': True,
                'section': 'reached',
                'test_data': {
                    'full_name': dummy_full_name,
                    'company_name': dummy_company_name,
                    'about_section': dummy_about_section,
                    'company_description': dummy_company_description
                },
                'email': messages.get('email'),
                'linkedin_message': messages.get('linkedin_message')
            })
            
    except ImportError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error testing LLM settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to test LLM settings: {str(e)}'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("LinkedIn Enricher - Admin Interface")
    print("=" * 60)
    print("\nStarting admin server...")
    print("Make sure Chrome is running with remote debugging:")
    print("  ./setup_chrome.sh")
    print("\nAccess the admin interface at: http://localhost:9001")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=9001)
