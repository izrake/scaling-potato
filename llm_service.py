"""Unified LLM Service
Supports both OpenAI and Google Gemini for generating responses."""
import os
from typing import Optional, Dict, Any
from openai import OpenAI

# Optional import for Gemini (using new google-genai package)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class LLMService:
    """Unified service for LLM calls supporting OpenAI and Gemini."""
    
    def __init__(
        self,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: 'openai' or 'gemini'
            api_key: API key for the provider
            model: Model name (optional, will use defaults)
            temperature: Temperature setting (0.0-1.0)
            max_tokens: Maximum tokens for response
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if self.provider == 'openai':
            self.client = OpenAI(api_key=api_key)
            self.model = model or 'gpt-4o-mini'
        elif self.provider == 'gemini':
            if not GEMINI_AVAILABLE:
                raise ImportError(
                    "Google GenAI package not installed. "
                    "Install it with: pip install google-genai"
                )
            # The new API uses Client() which gets API key from GEMINI_API_KEY env var
            # Temporarily set it in environment
            original_key = os.environ.get('GEMINI_API_KEY')
            os.environ['GEMINI_API_KEY'] = api_key
            self.gemini_client = genai.Client()
            # Restore original if it existed, otherwise clean up
            if original_key is not None:
                os.environ['GEMINI_API_KEY'] = original_key
            self.model = model or 'gemini-2.5-flash'  # Updated to new default model
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'gemini'")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using the configured LLM.
        
        Args:
            system_prompt: System prompt/instructions
            user_prompt: User prompt/question
            variables: Optional variables to inject into prompts
            
        Returns:
            Generated response text
        """
        # Replace variables in prompts if provided
        if variables:
            for key, value in variables.items():
                system_prompt = system_prompt.replace(f"{{{key}}}", str(value))
                user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
        
        if self.provider == 'openai':
            return self._generate_openai(system_prompt, user_prompt)
        elif self.provider == 'gemini':
            return self._generate_gemini(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _generate_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Google Gemini (new API)."""
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Google GenAI package not installed. "
                "Install it with: pip install google-genai"
            )
        try:
            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Use new API: client.models.generate_content()
            # According to docs: https://ai.google.dev/gemini-api/docs/quickstart
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def generate_for_pending(
        self,
        full_name: str,
        about_section: Optional[str] = None,
        company_name: Optional[str] = None,
        system_prompt: str = "",
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response for pending leads section.
        
        Args:
            full_name: Full name of the lead
            about_section: About/bio section from LinkedIn
            company_name: Company name (optional)
            system_prompt: System prompt from settings
            variables: Additional variables (e.g., questions)
            
        Returns:
            Generated response
        """
        # Build user prompt for pending section
        prompt_parts = [f"Lead Name: {full_name}"]
        if company_name:
            prompt_parts.append(f"Company: {company_name}")
        if about_section:
            # Truncate if too long to avoid token limits
            about_text = about_section[:2000] if len(about_section) > 2000 else about_section
            prompt_parts.append(f"About/Company Description: {about_text}")
        
        # Add questions from variables if provided
        if variables and 'questions' in variables:
            questions = variables['questions']
            if isinstance(questions, list):
                prompt_parts.append("\nQuestions to answer:")
                for q in questions:
                    prompt_parts.append(f"- {q}")
            elif isinstance(questions, str):
                prompt_parts.append(f"\nQuestions: {questions}")
        
        user_prompt = "\n".join(prompt_parts)
        
        # Use default system prompt if none provided
        if not system_prompt:
            system_prompt = """You are a sales research assistant. Analyze the lead information and answer the provided questions.

IMPORTANT: You must respond with valid JSON only. The JSON should have the following structure:
{
  "What they do": "A brief description of what the company does based on the provided information",
  "Can we pitch Spheron?": {
    "Verdict": "YES" or "NO",
    "Reasoning": "Detailed explanation for the verdict"
  }
}

Return ONLY the JSON object, no additional text or markdown formatting."""
        
        return self.generate(system_prompt, user_prompt, variables)
    
    def generate_for_reached(
        self,
        full_name: str,
        about_section: Optional[str] = None,
        company_name: Optional[str] = None,
        company_description: Optional[str] = None,
        system_prompt: str = "",
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate email and LinkedIn messages for reached leads section.
        
        Args:
            full_name: Full name of the lead
            about_section: About/bio section from LinkedIn
            company_name: Company name
            company_description: Company description
            system_prompt: System prompt from settings
            variables: Additional variables
            
        Returns:
            Dictionary with 'email' and 'linkedin_message' keys
        """
        # Build context for the prompt
        context_parts = [f"Lead Name: {full_name}"]
        if company_name:
            context_parts.append(f"Company: {company_name}")
        if about_section:
            context_parts.append(f"About: {about_section}")
        if company_description:
            # Truncate if too long
            desc = company_description[:2000] if len(company_description) > 2000 else company_description
            context_parts.append(f"Company Description: {desc}")
        
        context = "\n".join(context_parts)
        
        # Use default system prompt if none provided
        if not system_prompt:
            system_prompt = """You are a professional sales outreach specialist. Generate personalized outreach messages.
Generate both:
1. A professional sales email (2-3 paragraphs)
2. A LinkedIn message (under 300 characters)

Format your response as JSON with keys: "email" and "linkedin_message"."""
        
        user_prompt = f"""Generate personalized outreach messages for this lead:

{context}

Provide both an email and LinkedIn message that are:
- Personalized and relevant
- Professional and warm
- Not pushy
- Include clear value proposition"""
        
        try:
            response = self.generate(system_prompt, user_prompt, variables)
            
            # Try to parse as JSON if possible
            import json
            try:
                parsed = json.loads(response)
                return {
                    'email': parsed.get('email', response),
                    'linkedin_message': parsed.get('linkedin_message', response)
                }
            except:
                # If not JSON, split response or return as-is
                # Try to detect email vs LinkedIn message
                lines = response.split('\n')
                email_lines = []
                linkedin_lines = []
                in_email = False
                in_linkedin = False
                
                for line in lines:
                    if 'email' in line.lower() or 'subject' in line.lower():
                        in_email = True
                        in_linkedin = False
                    elif 'linkedin' in line.lower():
                        in_email = False
                        in_linkedin = True
                    elif in_email:
                        email_lines.append(line)
                    elif in_linkedin:
                        linkedin_lines.append(line)
                
                return {
                    'email': '\n'.join(email_lines) if email_lines else response,
                    'linkedin_message': '\n'.join(linkedin_lines) if linkedin_lines else response[:300]
                }
        except Exception as e:
            # Fallback response
            return {
                'email': f"Hi {full_name},\n\nI came across {company_name or 'your company'} and was impressed. I'd love to discuss how we might be able to help.\n\nBest regards",
                'linkedin_message': f"Hi {full_name}, I noticed your work at {company_name or 'your company'}. Would love to connect!"
            }

