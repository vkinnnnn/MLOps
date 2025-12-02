#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Sample Loan Documents
Processes all documents in sample-loan-docs directory through the API
"""
import os
import sys
import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
API_BASE_URL = "http://localhost:8000"
SAMPLE_DOCS_DIR = Path("sample-loan-docs")
OUTPUT_DIR = Path("output/sample-results")
API_KEY = "test-api-key"  # Use default or generate one

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_sample_documents() -> List[Path]:
    """Get all PDF documents from sample directory"""
    if not SAMPLE_DOCS_DIR.exists():
        print(f"❌ Sample documents directory not found: {SAMPLE_DOCS_DIR}")
        return []
    
    pdf_files = list(SAMPLE_DOCS_DIR.glob("*.pdf"))
    print(f"📁 Found {len(pdf_files)} PDF documents")
    return pdf_files

def check_api_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"⚠️ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def process_single_document(file_path: Path) -> Dict[str, Any]:
    """Process a single document through the API"""
    print(f"\n📄 Processing: {file_path.name}")
    
    try:
        # Prepare file
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            headers = {}
            
            # Add API key if configured
            if API_KEY and API_KEY != "test-api-key":
                headers['X-API-Key'] = API_KEY
            
            # Send request
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/api/v1/extract",
                files=files,
                headers=headers,
                timeout=120
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Success! Processed in {processing_time:.2f}s")
                
                # Extract key metrics
                if 'accuracy_metrics' in result:
                    metrics = result['accuracy_metrics']
                    print(f"  📊 Overall Accuracy: {metrics.get('overall_accuracy', 0)*100:.1f}%")
                    print(f"  📊 Form Field Confidence: {metrics.get('form_field_confidence', 0)*100:.1f}%")
                
                return {
                    'status': 'success',
                    'file_name': file_path.name,
                    'processing_time': processing_time,
                    'result': result
                }
            elif response.status_code == 401:
                print(f"  ❌ Authentication failed - Invalid API key")
                return {
                    'status': 'auth_error',
                    'file_name': file_path.name,
                    'error': 'Invalid API key'
                }
            elif response.status_code == 429:
                print(f"  ⚠️ Rate limit exceeded - Waiting...")
                time.sleep(5)
                return process_single_document(file_path)  # Retry
            else:
                error_msg = response.text
                print(f"  ❌ Failed with status {response.status_code}")
                print(f"  Error: {error_msg[:200]}")
                return {
                    'status': 'error',
                    'file_name': file_path.name,
                    'error': error_msg
                }
                
    except requests.exceptions.Timeout:
        print(f"  ⏱️ Request timeout (>120s)")
        return {
            'status': 'timeout',
            'file_name': file_path.name,
            'error': 'Request timeout'
        }
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {
            'status': 'error',
            'file_name': file_path.name,
            'error': str(e)
        }

def process_batch(file_paths: List[Path], max_docs: int = 10) -> Dict[str, Any]:
    """Process multiple documents"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_documents': len(file_paths),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_processing_time': 0,
        'documents': []
    }
    
    # Limit number of documents if specified
    file_paths = file_paths[:max_docs]
    print(f"\n🚀 Starting batch processing of {len(file_paths)} documents...")
    
    for i, file_path in enumerate(file_paths, 1):
        print(f"\n[{i}/{len(file_paths)}]", end=" ")
        result = process_single_document(file_path)
        
        results['documents'].append(result)
        results['processed'] += 1
        
        if result['status'] == 'success':
            results['successful'] += 1
            results['total_processing_time'] += result.get('processing_time', 0)
        else:
            results['failed'] += 1
        
        # Small delay between requests
        if i < len(file_paths):
            time.sleep(1)
    
    return results

def generate_report(results: Dict[str, Any]) -> str:
    """Generate a summary report"""
    report = []
    report.append("=" * 80)
    report.append("DOCUMENT PROCESSING REPORT")
    report.append("=" * 80)
    report.append(f"Timestamp: {results['timestamp']}")
    report.append(f"Total Documents: {results['total_documents']}")
    report.append(f"Processed: {results['processed']}")
    report.append(f"Successful: {results['successful']}")
    report.append(f"Failed: {results['failed']}")
    
    if results['successful'] > 0:
        avg_time = results['total_processing_time'] / results['successful']
        report.append(f"Average Processing Time: {avg_time:.2f}s")
    
    report.append("\n" + "=" * 80)
    report.append("DOCUMENT DETAILS")
    report.append("=" * 80)
    
    for doc in results['documents']:
        report.append(f"\n📄 {doc['file_name']}")
        report.append(f"   Status: {doc['status']}")
        
        if doc['status'] == 'success':
            report.append(f"   Processing Time: {doc.get('processing_time', 0):.2f}s")
            
            # Extract accuracy if available
            result = doc.get('result', {})
            if 'accuracy_metrics' in result:
                metrics = result['accuracy_metrics']
                report.append(f"   Overall Accuracy: {metrics.get('overall_accuracy', 0)*100:.1f}%")
                report.append(f"   Form Field Confidence: {metrics.get('form_field_confidence', 0)*100:.1f}%")
        else:
            report.append(f"   Error: {doc.get('error', 'Unknown error')}")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)

def save_results(results: Dict[str, Any], report: str):
    """Save results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON results
    json_file = OUTPUT_DIR / f"processing_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {json_file}")
    
    # Save text report
    report_file = OUTPUT_DIR / f"processing_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📊 Report saved to: {report_file}")
    
    # Save individual successful extractions
    for doc in results['documents']:
        if doc['status'] == 'success' and 'result' in doc:
            doc_file = OUTPUT_DIR / f"{Path(doc['file_name']).stem}_extraction.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(doc['result'], f, indent=2, default=str)

def main():
    """Main execution"""
    print("=" * 80)
    print("Student Loan Document Extractor - Sample Processing")
    print("=" * 80)
    
    # Check API health
    if not check_api_health():
        print("\n❌ API is not accessible. Please ensure Docker services are running:")
        print("   docker-compose ps")
        print("   docker-compose up -d")
        return
    
    # Get sample documents
    sample_docs = get_sample_documents()
    if not sample_docs:
        return
    
    # Ask user how many to process
    print(f"\n📋 Available documents: {len(sample_docs)}")
    try:
        max_docs = input("How many documents to process? (default: 10, 'all' for all): ").strip()
        if max_docs.lower() == 'all':
            max_docs = len(sample_docs)
        elif max_docs == '':
            max_docs = 10
        else:
            max_docs = int(max_docs)
    except (ValueError, EOFError):
        max_docs = 10
    
    # Process documents
    results = process_batch(sample_docs, max_docs)
    
    # Generate and display report
    report = generate_report(results)
    print("\n" + report)
    
    # Save results
    save_results(results, report)
    
    print("\n✅ Processing complete!")

if __name__ == "__main__":
    main()
