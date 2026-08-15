from backend.app.database import SessionLocal
from backend.app.services.collector import FeedCollectorService

def main():
    db = SessionLocal()
    try:
        print("Starting manual feed collector scan across all active sources...")
        collector = FeedCollectorService(db)
        summary = collector.scan_all_active_sources()
        print("\n================ SCAN SUMMARY ================")
        print(f"Total Sources Configured: {summary['total_sources']}")
        print(f"Successful Sources:       {summary['successful_sources']}")
        print(f"Failed Sources:           {summary['failed_sources']}")
        print(f"Total New Items Ingested: {summary['total_items_saved']}")
        print(f"Total Duplicate Items:    {summary['total_duplicates']}")
        print("==============================================\n")
        for det in summary['details']:
            status_symbol = "[OK]" if not det['errors'] else "[ERR]"
            name = det['source_name']
            found = det['items_found']
            saved = det['items_saved']
            dups = det['items_duplicate']
            print(f"{status_symbol} [{name}] Found: {found} | Saved: {saved} | Duplicates: {dups}")
            if det['errors']:
                for err in det['errors']:
                    print(f"    Notice/Error: {err}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
