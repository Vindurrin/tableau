#!/usr/bin/env python3
"""
Tableau Server Stale Content Detection (Multi-Site)

Identifies workbooks and datasources that haven't been updated within the 
configured threshold period across ALL sites on the deployment.

Security: Uses environment variables for credentials (see .env.example)
"""

import datetime
import sys
from tableau_client import TableauGovernanceClient, main_wrapper
from config import config

def scan_site_content(server, site):
    """
    Scan a specific site for stale content (workbooks and datasources).
    
    Args:
        server: TSC.Server instance
        site: TSC.SiteItem instance  
        
    Returns:
        List of stale content dictionaries
    """
    stale_content = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=config.stale_content_days)
    
    # Scan workbooks
    try:
        all_workbooks, pagination = server.workbooks.get()
        for wb in all_workbooks:
            if wb.updated_at and wb.updated_at < cutoff_date:
                days_stale = (datetime.datetime.now() - wb.updated_at).days
                stale_content.append({
                    "name": wb.name,
                    "type": "workbook",
                    "project": wb.project_name or "Unknown",
                    "owner_id": wb.owner_id,
                    "content_url": wb.content_url or "N/A",
                    "updated_at": wb.updated_at.isoformat(),
                    "days_stale": days_stale,
                    "site_name": site.name,
                    "site_id": site.id,
                    "site_content_url": site.content_url or "default",
                    "size_mb": round(wb.size / (1024*1024), 2) if wb.size else 0,
                    "views_count": getattr(wb, 'views', 'N/A')
                })
    except Exception as e:
        print(f"    ⚠️  Error scanning workbooks: {e}")
    
    # Scan datasources  
    try:
        all_datasources, pagination = server.datasources.get()
        for ds in all_datasources:
            if ds.updated_at and ds.updated_at < cutoff_date:
                days_stale = (datetime.datetime.now() - ds.updated_at).days
                stale_content.append({
                    "name": ds.name,
                    "type": "datasource", 
                    "project": ds.project_name or "Unknown",
                    "owner_id": ds.owner_id,
                    "content_url": ds.content_url or "N/A",
                    "updated_at": ds.updated_at.isoformat(),
                    "days_stale": days_stale,
                    "site_name": site.name,
                    "site_id": site.id,
                    "site_content_url": site.content_url or "default",
                    "size_mb": round(ds.size / (1024*1024), 2) if ds.size else 0,
                    "views_count": "N/A"  # Datasources don't have view counts
                })
    except Exception as e:
        print(f"    ⚠️  Error scanning datasources: {e}")
    
    return stale_content

def run_content_scanner(client: TableauGovernanceClient):
    """
    Main scanner function using the shared client.
    
    Args:
        client: Initialized TableauGovernanceClient instance
        
    Returns:
        None (results are handled by client)
    """
    # Use the shared scanning infrastructure
    all_stale_content = client.scan_all_sites(scan_site_content, "content")
    
    # Group content by site and type for summary
    sites_summary = {}
    type_summary = {"workbook": 0, "datasource": 0}
    
    for item in all_stale_content:
        site_name = item['site_name']
        content_type = item['type']
        
        if site_name not in sites_summary:
            sites_summary[site_name] = 0
        sites_summary[site_name] += 1
        type_summary[content_type] += 1
    
    # Save results using standardized format
    log_file = client.save_results(
        data=all_stale_content,
        file_prefix="stale_content",
        summary_message=f"{len(all_stale_content)} stale content items found",
        extra_metadata={
            "threshold_days": config.stale_content_days,
            "sites_summary": sites_summary,
            "type_summary": type_summary
        }
    )
    
    # Print standardized summary
    client.print_results_summary(
        count=len(all_stale_content),
        resource_type="stale content items",
        threshold_info=f"{config.stale_content_days} days without updates",
        log_file=log_file,
        breakdown=sites_summary
    )
    
    # Additional type breakdown
    if type_summary:
        print(f"\n📊 Content type breakdown:")
        for content_type, count in type_summary.items():
            print(f"   • {content_type.title()}s: {count}")

if __name__ == "__main__":
    sys.exit(main_wrapper(
        scanner_function=run_content_scanner,
        resource_name="content",
        description="Multi-Site Stale Content Scanner"
    ))
