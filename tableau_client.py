#!/usr/bin/env python3
"""
Shared Tableau Server Client Base Class

Provides common functionality for all Tableau governance scripts including:
- Multi-site authentication and scanning
- Standardized error handling  
- Consistent JSON output formatting
- Secure configuration management

This eliminates code duplication across all log_*.py scripts.
"""

import tableauserverclient as TSC
import datetime
import json
import os
import sys
import time
from typing import List, Dict, Any, Optional, Callable
from config import config
from logger import get_logger, timed_operation
from retry_utils import tableau_api_retry, tableau_auth_retry

class TableauGovernanceClient:
    """
    Base client for Tableau Server governance operations.
    
    Handles authentication, site iteration, and standardized logging.
    """
    
    def __init__(self):
        """Initialize client with secure configuration."""
        self.config = config
        self.server = None
        self.auth = None
        self.logger = get_logger("tableau_client")
        
        # Ensure log directory exists
        os.makedirs(self.config.log_dir, exist_ok=True)
        
        # Log initialization
        self.logger.info("Initializing Tableau Governance Client", 
                        server_url=self.config.server_url,
                        log_only_mode=self.config.log_only)
    
    @timed_operation("tableau_server_connection")
    @tableau_auth_retry
    def connect(self) -> TSC.Server:
        """
        Establish connection to Tableau Server.
        
        Returns:
            Authenticated TSC.Server instance
            
        Raises:
            ValueError: Configuration errors
            TSC.ServerResponseError: Authentication failures
        """
        self.logger.info("Connecting to Tableau Server", 
                        server_url=self.config.server_url)
        print(f"🔐 Connecting to Tableau Server: {self.config.server_url}")
        
        # Configure authentication (empty site_id for server-level operations)
        self.auth = TSC.PersonalAccessTokenAuth(
            self.config.token_name, 
            self.config.token_secret, 
            ""  # Empty for multi-site operations
        )
        
        self.server = TSC.Server(self.config.server_url, use_server_version=True)
        
        # Test connection
        try:
            with self.server.auth.sign_in(self.auth):
                self.logger.info("Authentication successful")
                print("✅ Authentication successful")
        except Exception as e:
            self.logger.error("Authentication failed", 
                            error_type=type(e).__name__,
                            error_message=str(e))
            raise
            
        return self.server
    
    @tableau_api_retry
    def get_all_sites(self) -> List[TSC.SiteItem]:
        """
        Get list of all sites on the server.
        
        Returns:
            List of site objects
        """
        if not self.server:
            raise RuntimeError("Must connect() before getting sites")
            
        with self.server.auth.sign_in(self.auth):
            all_sites, pagination = self.server.sites.get()
            self.logger.info(f"Retrieved site list", site_count=len(all_sites))
            print(f"📊 Found {len(all_sites)} sites to process")
            return all_sites
    
    def scan_all_sites(self, scan_function: Callable, resource_name: str) -> List[Dict[str, Any]]:
        """
        Apply a scanning function across all sites.
        
        Args:
            scan_function: Function that takes (server, site) and returns list of items
            resource_name: Human-readable name for logging (e.g., "users", "workbooks")
            
        Returns:
            Combined list of items from all sites
        """
        all_items = []
        sites = self.get_all_sites()
        
        with self.server.auth.sign_in(self.auth):
            for site in sites:
                try:
                    print(f"  📋 Scanning {resource_name} in site: {site.name} (ID: {site.id})")
                    
                    # Switch to site context
                    self.server.sites.switch_site(site)
                    
                    # Run the specific scanning function
                    site_items = scan_function(self.server, site)
                    all_items.extend(site_items)
                    
                    print(f"    ↳ Found {len(site_items)} {resource_name}")
                    
                except TSC.ServerResponseError as e:
                    print(f"    ❌ Error scanning site {site.name}: {e}")
                    continue
        
        return all_items
    
    def save_results(self, 
                    data: List[Dict[str, Any]], 
                    file_prefix: str,
                    summary_message: str,
                    extra_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save scan results to standardized JSON format.
        
        Args:
            data: List of items found
            file_prefix: Filename prefix (e.g., "inactive_users")
            summary_message: Human-readable summary
            extra_metadata: Additional metadata to include
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.datetime.now()
        log_file = os.path.join(
            self.config.log_dir, 
            f"{file_prefix}_{timestamp.date()}.json"
        )
        
        # Standard metadata
        output_data = {
            "summary": summary_message,
            "total_count": len(data),
            "scan_date": timestamp.isoformat(),
            "server_url": self.config.server_url,
            "log_only_mode": self.config.log_only,
            "script_version": "2.0_secure"
        }
        
        # Add any extra metadata
        if extra_metadata:
            output_data.update(extra_metadata)
        
        # Add the actual data
        output_data["items"] = data
        
        # Write to file
        with open(log_file, "w") as f:
            json.dump(output_data, f, indent=2)
        
        return log_file
    
    def print_results_summary(self, 
                            count: int, 
                            resource_type: str,
                            threshold_info: str,
                            log_file: str,
                            breakdown: Optional[Dict[str, int]] = None):
        """
        Print standardized results summary.
        
        Args:
            count: Total items found
            resource_type: Type of resource (e.g., "inactive users")
            threshold_info: Threshold description
            log_file: Path to log file
            breakdown: Optional site-by-site breakdown
        """
        print(f"\n✅ Scan completed successfully:")
        print(f"   📊 Total {resource_type}: {count}")
        print(f"   📅 Criteria: {threshold_info}")
        print(f"   💾 Results saved to: {log_file}")
        print(f"   🔒 Mode: {'LOG ONLY' if self.config.log_only else 'CLEANUP ENABLED'}")
        
        # Show breakdown if provided
        if breakdown:
            print(f"\n📋 Breakdown by site:")
            for site_name, site_count in breakdown.items():
                print(f"   • {site_name}: {site_count} {resource_type}")
        
        # Cleanup mode warning
        if not self.config.log_only and count > 0:
            print(f"\n⚠️  WARNING: Cleanup mode is enabled but not implemented yet")
            print(f"   - Would affect {count} {resource_type}")
            print(f"   - Set log_only=true in config to disable this warning")

def main_wrapper(scanner_function: Callable, 
                resource_name: str,
                description: str) -> int:
    """
    Standard main function wrapper for all governance scripts.
    
    Args:
        scanner_function: Function that takes TableauGovernanceClient and returns results
        resource_name: Resource type being scanned
        description: Script description for logging
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        print(f"🔍 {description}")
        print(f"Mode: {'LOG ONLY' if config.log_only else 'CLEANUP ENABLED'}")
        print("-" * 60)
        
        client = TableauGovernanceClient()
        client.connect()
        
        # Run the specific scanner
        results = scanner_function(client)
        
        return 0
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please check your environment variables or .env file")
        return 1
    except TSC.ServerResponseError as e:
        print(f"❌ Tableau Server Error: {e}")
        print("Check your server URL, credentials, and network connectivity")
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    print("This is a shared library module. Run individual log_*.py scripts instead.")
    sys.exit(1)