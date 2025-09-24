import json
import os
from app.db.sqlite_conn import SessionLocal, CompanyProfile

def populate_db()->None:
    """Populate the database with mock company data from JSON files."""
    
    # Get the directory containing the mock company JSON files
    mock_companies_dir = os.path.join(os.path.dirname(__file__), "mock_companies")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Get all JSON files in the mock_companies directory
        json_files = [f for f in os.listdir(mock_companies_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            file_path = os.path.join(mock_companies_dir, json_file)
            
            # Read and parse the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                company_data = json.load(f)
            company_data['company_name'] = (company_data.get('company_name')).lower()
            # Check if company already exists
            existing_company = db.query(CompanyProfile).filter(
                CompanyProfile.company_name == company_data.get('company_name')
            ).first()

            if existing_company:
                print(f"Company '{company_data.get('company_name')}' already exists, skipping...")
                continue
            # Create a CompanyProfile instance
            company_profile = CompanyProfile(
                company_name=(company_data.get('company_name')),
                brand_voice=(company_data.get('brand_voice')),
                target_audience=company_data.get('target_audience'),
                product_category=company_data.get('product_category'),
                style_guide=company_data.get('style_guide'),
                recent_campaign_metrics=company_data.get('recent_campaign_metrics')
            )
            
            # Add to session
            db.add(company_profile)
            print(f"Added company: {company_data.get('company_name', json_file)}")
        
        # Commit all changes
        db.commit()
        print(f"Successfully populated database with {len(json_files)} companies.")
        
    except Exception as e:
        # Rollback in case of error
        db.rollback()
        print(f"Error populating database: {e}")
        raise
    
    finally:
        # Close the session
        db.close()