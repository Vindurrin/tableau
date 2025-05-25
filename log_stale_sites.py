#!/usr/bin/env python3
"""
Tableau Server Stale Sites Detection

Identifies sites that haven't been updated within the configured threshold period.
Note: This scans at the server level, not individual sites.

Security: Uses environment variables for credentials (see .env.example)
"""

import datetime
import sys
from tableau_client import TableauGovernanceClient, main_wrapper
from config import config

def run_sites_scanner(client: TableauGovernanceClient):
    """
    Scanner for stale sites - operates at server level.
    
    Args:
        client: Initialized TableauGovernanceClient instance
        
    Returns:
        None (results are handled by client)
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=config.stale_site_days)
    
    # Get all sites (this is server-level, not per-site scanning)
    all_sites = client.get_all_sites()
    
    stale_sites = []
    active_sites = []
    
    for site in all_sites:
        # Use the most recent date available
        last_updated = site.updated_at or site.created_at
        
        if last_updated and last_updated < cutoff_date:
            days_stale = (datetime.datetime.now() - last_updated).days
            stale_sites.append({
                "site_name": site.name,
                "site_id": site.id,
                "content_url": site.content_url or "default",
                "state": site.state,
                "admin_mode": site.admin_mode,
                "user_quota": site.user_quota or "unlimited",
                "storage_quota": site.storage_quota or "unlimited", 
                "created_at": site.created_at.isoformat() if site.created_at else "N/A",
                "updated_at": site.updated_at.isoformat() if site.updated_at else "N/A",
                "last_activity": last_updated.isoformat(),
                "days_stale": days_stale
            })
        else:
            active_sites.append(site.name)
    
    # Create status summary
    status_summary = {
        "total_sites": len(all_sites),
        "stale_sites": len(stale_sites),
        "active_sites": len(active_sites),
        "stale_percentage": round((len(stale_sites) / len(all_sites)) * 100, 1) if all_sites else 0
    }
    
    # Save results using standardized format
    log_file = client.save_results(
        data=stale_sites,
        file_prefix="stale_sites",
        summary_message=f"{len(stale_sites)} stale sites found out of {len(all_sites)} total",
        extra_metadata={
            "threshold_days": config.stale_site_days,
            "status_summary": status_summary,
            "active_sites": active_sites[:10]  # First 10 active sites for reference
        }
    )
    
    # Print detailed summary
    print(f"\n✅ Site analysis completed:")
    print(f"   📊 Total sites: {len(all_sites)}")
    print(f"   ⚠️  Stale sites: {len(stale_sites)} ({status_summary['stale_percentage']}%)")
    print(f"   ✅ Active sites: {len(active_sites)}")
    print(f"   📅 Threshold: {config.stale_site_days} days")
    print(f"   💾 Results saved to: {log_file}")
    print(f"   🔒 Mode: {'LOG ONLY' if config.log_only else 'CLEANUP ENABLED'}")
    
    # Show stale sites if any
    if stale_sites:
        print(f"\n⚠️  Stale sites found:")
        for site in stale_sites[:5]:  # Show first 5
            print(f"   • {site['site_name']}: {site['days_stale']} days stale")
        if len(stale_sites) > 5:
            print(f"   • ... and {len(stale_sites) - 5} more")
    
    # Cleanup mode warning
    if not config.log_only and stale_sites:
        print(f"\n⚠️  WARNING: Cleanup mode is enabled but not implemented yet")
        print(f"   - Would affect {len(stale_sites)} sites")
        print(f"   - Set log_only=true in config to disable this warning")

if __name__ == "__main__":
    sys.exit(main_wrapper(
        scanner_function=run_sites_scanner,
        resource_name="sites",
        description="Server-Level Stale Sites Scanner"
    ))
