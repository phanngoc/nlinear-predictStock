"""
Base notifier for TrendRadar.

Provides base class and common functionality for all notifiers.
"""

from typing import Dict, List


class BaseNotifier:
    """
    Base notifier class for all platform notifiers.
    
    All platform-specific notifiers should inherit from this class.
    """

    def send(self, report_data: Dict, **kwargs) -> bool:
        """
        Send notification to platform.
        
        Args:
            report_data: Report data dictionary
            **kwargs: Additional sending options
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement send()")

    def split_batches(self, content: str, max_bytes: int) -> List[str]:
        """
        Split content into batches based on byte size.
        
        Args:
            content: Content to split
            max_bytes: Maximum bytes per batch
            
        Returns:
            List[str]: List of content batches
        """
        batches = []
        current_batch = ""
        
        for line in content.split("\n"):
            test_batch = current_batch + line + "\n"
            if len(test_batch.encode('utf-8')) > max_bytes and current_batch:
                batches.append(current_batch)
                current_batch = line + "\n"
            else:
                current_batch = test_batch
        
        if current_batch:
            batches.append(current_batch)
        
        return batches if batches else [content]
