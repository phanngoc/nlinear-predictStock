"""
Base renderer for TrendRadar.

Provides base class and common functionality for all renderers.
"""

from typing import Dict


class BaseRenderer:
    """
    Base renderer class for all platform renderers.
    
    All platform-specific renderers should inherit from this class.
    """

    def render(self, report_data: Dict, **kwargs) -> str:
        """
        Render report data to platform-specific format.
        
        Args:
            report_data: Report data dictionary
            **kwargs: Additional rendering options
            
        Returns:
            str: Rendered content
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement render()")

    def format_title(self, title_data: Dict, show_source: bool = True) -> str:
        """
        Format title for platform.
        
        Args:
            title_data: Title data dictionary
            show_source: Whether to show source name
            
        Returns:
            str: Formatted title
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement format_title()")
