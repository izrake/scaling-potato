"""Message Generator Module
Generates sales emails and LinkedIn messages using OpenAI API."""
import os
from typing import Optional, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class MessageGenerator:
    """Generates personalized sales messages using OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize message generator.
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_messages(
        self,
        client_name: str,
        company_name: Optional[str] = None,
        company_description: Optional[str] = None,
        website: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate sales email and LinkedIn messages.
        
        Args:
            client_name: Name of the client/person
            company_name: Name of the company
            company_description: Scraped company description
            website: Company website URL
            
        Returns:
            Dictionary with 'email', 'linkedin_connection', and 'linkedin_followup' messages
        """
        # Build context for the prompt
        context_parts = []
        if company_name:
            context_parts.append(f"Company: {company_name}")
        if website:
            context_parts.append(f"Website: {website}")
        if company_description:
            # Truncate description if too long (OpenAI has token limits)
            desc = company_description[:2000] if len(company_description) > 2000 else company_description
            context_parts.append(f"Company Description: {desc}")
        
        context = "\n".join(context_parts) if context_parts else "No additional company information available."
        
        prompt = f"""You are a professional sales outreach specialist. Generate personalized outreach messages for {client_name}.

Context about the prospect:
{context}

Generate three types of messages:

1. **Sales Email**: A professional, personalized sales email (2-3 paragraphs) that:
   - Opens with a personalized connection to their company
   - Highlights value proposition
   - Includes a clear call-to-action
   - Is warm, professional, and not pushy

2. **LinkedIn Connection Request**: A brief, personalized connection request message (under 300 characters) that:
   - Mentions something specific about their company or role
   - Is friendly and professional
   - Invites them to connect

3. **LinkedIn Follow-up Message**: A follow-up message (2-3 sentences) to send after they accept the connection that:
   - Thanks them for connecting
   - Provides value or insight
   - Suggests next steps without being pushy

Format your response as JSON with these exact keys:
{{
    "email": "the email message here",
    "linkedin_connection": "the connection request message here",
    "linkedin_followup": "the follow-up message here"
}}

Make sure all messages are personalized, professional, and relevant to {client_name} and their company."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-effective model
                messages=[
                    {"role": "system", "content": "You are a professional sales outreach specialist. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            import json
            messages = json.loads(response.choices[0].message.content)
            
            # Validate and return messages
            return {
                'email': messages.get('email', ''),
                'linkedin_connection': messages.get('linkedin_connection', ''),
                'linkedin_followup': messages.get('linkedin_followup', '')
            }
            
        except Exception as e:
            print(f"Error generating messages: {e}")
            # Return fallback messages
            return {
                'email': f"Hi {client_name},\n\nI came across {company_name or 'your company'} and was impressed by your work. I'd love to discuss how we might be able to help.\n\nBest regards",
                'linkedin_connection': f"Hi {client_name}, I noticed your work at {company_name or 'your company'}. Would love to connect!",
                'linkedin_followup': f"Thanks for connecting, {client_name}! I'd love to learn more about {company_name or 'your company'} and see if there's a way we can help."
            }

