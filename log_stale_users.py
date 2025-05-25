#!/usr/bin/env python3
"""
Tableau Server Inactive Users Detection (Multi-Site)

Identifies users who haven't logged in within the configured threshold period
across ALL sites on the Tableau Server deployment.

Security: Uses environment variables for credentials (see .env.example)
"""

import datetime
import sys
from tableau_client import TableauGovernanceClient, main_wrapper
from config import config

def scan_site_users(server, site):
    """
    Scan a specific site for inactive users.
    
    Args:
        server: TSC.Server instance
        site: TSC.SiteItem instance  
        
    Returns:
        List of inactive user dictionaries
    """
    inactive_users = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=config.stale_user_days)
    
    # Get all users for this site
    all_users, pagination = server.users.get()
    
    for user in all_users:
        # Check if user has logged in and if it's before cutoff
        if user.last_login and user.last_login < cutoff_date:
            days_inactive = (datetime.datetime.now() - user.last_login).days
            inactive_users.append({
                "username": user.name,
                "full_name": user.fullname or "N/A",
                "email": user.email or "N/A", 
                "last_login": user.last_login.isoformat(),
                "days_inactive": days_inactive,
                "site_name": site.name,
                "site_id": site.id,
                "site_content_url": site.content_url or "default",
                "domain_name": user.domain_name or "local"
            })
    
    return inactive_users

def run_user_scanner(client: TableauGovernanceClient):
    """
    Main scanner function using the shared client.
    
    Args:
        client: Initialized TableauGovernanceClient instance
        
    Returns:
        None (results are handled by client)
    """
    # Use the shared scanning infrastructure
    all_inactive_users = client.scan_all_sites(scan_site_users, "users")
    
    # Group users by site for summary
    sites_summary = {}
    for user in all_inactive_users:
        site_name = user['site_name']
        if site_name not in sites_summary:
            sites_summary[site_name] = 0
        sites_summary[site_name] += 1
    
    # Save results using standardized format
    log_file = client.save_results(
        data=all_inactive_users,
        file_prefix="inactive_users",
        summary_message=f"{len(all_inactive_users)} inactive users found",
        extra_metadata={
            "threshold_days": config.stale_user_days,
            "sites_summary": sites_summary
        }
    )
    
    # Print standardized summary
    client.print_results_summary(
        count=len(all_inactive_users),
        resource_type="inactive users",
        threshold_info=f"{config.stale_user_days} days without login",
        log_file=log_file,
        breakdown=sites_summary
    )

if __name__ == "__main__":
    sys.exit(main_wrapper(
        scanner_function=run_user_scanner,
        resource_name="users",
        description="Multi-Site Inactive User Scanner"
    ))
