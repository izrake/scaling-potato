"""Step 6: Data Compiler Module
Compiles extracted data into structured JSON format."""
from typing import Dict, Optional
from .models import EnrichmentResult


class DataCompiler:
    """Compiles extracted data into structured format."""
    
    @staticmethod
    def compile_result(
        linkedin_url: str,
        name: Optional[str] = None,
        company_name: Optional[str] = None,
        company_linkedin_url: Optional[str] = None,
        website: Optional[str] = None,
        company_description: Optional[str] = None,
        valid_experience: bool = True,
        experience_reason: Optional[str] = None
    ) -> EnrichmentResult:
        """
        Compile all extracted data into structured result.
        
        Args:
            linkedin_url: Original LinkedIn profile URL
            name: User's name
            company_name: Name of the company
            company_linkedin_url: LinkedIn URL of the company
            website: Company website URL
            company_description: Scraped company description
            
        Returns:
            EnrichmentResult object with all data
        """
        return EnrichmentResult(
            name=name or "Unknown",
            website=website,
            company_description=company_description,
            linkedin_url=linkedin_url,
            company_name=company_name,
            company_linkedin_url=company_linkedin_url,
            valid_experience=valid_experience,
            experience_reason=experience_reason
        )
    
    @staticmethod
    def to_dict(result: EnrichmentResult) -> Dict:
        """
        Convert EnrichmentResult to dictionary.
        
        Args:
            result: EnrichmentResult object
            
        Returns:
            Dictionary representation
        """
        return result.model_dump()
    
    @staticmethod
    def to_json(result: EnrichmentResult) -> str:
        """
        Convert EnrichmentResult to JSON string.
        
        Args:
            result: EnrichmentResult object
            
        Returns:
            JSON string representation
        """
        return result.model_dump_json(indent=2)

