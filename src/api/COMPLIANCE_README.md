# Compliance and Privacy Features

This module implements GDPR, COPPA, and privacy compliance features for the Student Loan Document Extractor Platform.

## Overview

The compliance module provides comprehensive data protection and privacy controls to ensure the platform meets regulatory requirements for handling sensitive financial and personal information.

## Features

### 1. GDPR Compliance (Requirement 9.4)

#### Data Deletion (Right to Erasure - Article 17)
- Delete user documents, extracted loan data, and access logs
- Configurable deletion scope
- Audit trail of deletion operations

**Endpoint**: `POST /api/v1/compliance/gdpr/delete`

**Example Request**:
```json
{
 "user_id": "user123",
 "reason": "User requested account deletion",
 "delete_documents": true,
 "delete_extracted_data": true,
 "delete_access_logs": false
}
```

#### Data Export (Right to Data Portability - Article 20)
- Export user data in JSON, CSV, or PDF format
- Include documents, extracted data, and access logs
- Machine-readable structured format

**Endpoint**: `POST /api/v1/compliance/gdpr/export`

**Example Request**:
```json
{
 "user_id": "user123",
 "format": "json",
 "include_documents": true,
 "include_extracted_data": true,
 "include_access_logs": true
}
```

### 2. COPPA Compliance (Requirement 9.5)

#### Parental Consent Mechanisms
- Request and record parental consent for users under 13
- Verify parent identity through multiple methods
- Track consent status (pending, granted, denied, revoked)

**Endpoint**: `POST /api/v1/compliance/coppa/parental-consent`

**Example Request**:
```json
{
 "child_user_id": "child123",
 "parent_name": "John Doe",
 "parent_email": "john.doe@example.com",
 "parent_phone": "+1234567890",
 "consent_granted": true,
 "verification_method": "email_verification"
}
```

#### Data Minimization Controls
- Collect only essential information
- Configurable data retention periods
- Automatic deletion after retention period
- Anonymization of personal information

**Endpoint**: `POST /api/v1/compliance/coppa/data-minimization/{user_id}`

**Example Request**:
```json
{
 "collect_only_essential": true,
 "retention_days": 90,
 "auto_delete_after_retention": true,
 "anonymize_personal_info": true
}
```

#### Age Verification
- Determine if user is under 13
- Check if parental consent is required
- Apply appropriate COPPA measures

**Endpoint**: `GET /api/v1/compliance/coppa/age-verification/{user_id}?birth_date=2015-01-01`

#### Data Retention Management
- Check retention status for users
- Automatic deletion of expired data
- Retention period tracking

**Endpoint**: `GET /api/v1/compliance/coppa/retention-status/{user_id}`

#### Personal Information Anonymization
- Anonymize names (convert to initials)
- Anonymize email addresses
- Anonymize phone numbers
- Anonymize loan data while preserving analytical value

**Endpoint**: `POST /api/v1/compliance/coppa/anonymize-data/{user_id}`

### 3. Privacy Controls (Requirement 9.6)

#### Document Confidentiality Settings
- Four confidentiality levels: public, internal, confidential, restricted
- User-specific access control lists
- Time-based access expiry

**Endpoint**: `POST /api/v1/compliance/privacy/document-confidentiality`

**Example Request**:
```json
{
 "document_id": "doc123",
 "confidentiality_level": "confidential",
 "allowed_users": ["user1", "user2", "user3"],
 "expiry_date": "2024-12-31T23:59:59Z"
}
```

#### Access Logging
- Log all document access (view, download, edit, delete)
- Record user ID, timestamp, IP address, and user agent
- Comprehensive audit trail

**Endpoint**: `POST /api/v1/compliance/privacy/log-access/{document_id}`

**Query Parameters**:
- `user_id`: User accessing the document
- `action`: Action performed (view, download, edit, delete)

#### Access Permission Management
- Check user access permissions
- Grant access to specific users
- Revoke access from users
- Time-limited access grants

**Endpoints**:
- `GET /api/v1/compliance/privacy/check-access/{document_id}?user_id=user123`
- `POST /api/v1/compliance/privacy/grant-access/{document_id}?user_id=user123&granted_by=owner123`
- `POST /api/v1/compliance/privacy/revoke-access/{document_id}?user_id=user123&revoked_by=owner123`

#### Audit Trail
- User activity summaries
- Document access summaries
- Export audit trails in JSON or CSV
- Time-range filtering

**Endpoints**:
- `GET /api/v1/compliance/privacy/audit/user/{user_id}?start_date=2024-01-01&end_date=2024-12-31`
- `GET /api/v1/compliance/privacy/audit/document/{document_id}?start_date=2024-01-01&end_date=2024-12-31`
- `POST /api/v1/compliance/privacy/audit/export?entity_type=user&entity_id=user123&format=json`

#### Privacy Policy Management
- Record policy acceptance
- Check policy acceptance status
- Version tracking
- Require acceptance of updated policies

**Endpoints**:
- `POST /api/v1/compliance/privacy/policy/accept?user_id=user123&policy_version=1.0&accepted=true`
- `GET /api/v1/compliance/privacy/policy/check/{user_id}?required_version=1.0`

## Database Schema

### Parental Consents Table
```sql
CREATE TABLE parental_consents (
 consent_id UUID PRIMARY KEY,
 child_user_id VARCHAR(255) NOT NULL,
 parent_name VARCHAR(255) NOT NULL,
 parent_email VARCHAR(255) NOT NULL,
 parent_phone VARCHAR(50),
 consent_status VARCHAR(50) NOT NULL,
 verification_method VARCHAR(100) NOT NULL,
 consent_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 revoked_at TIMESTAMP
);
```

### Document Privacy Settings Table
```sql
CREATE TABLE document_privacy_settings (
 setting_id UUID PRIMARY KEY,
 document_id UUID NOT NULL,
 confidentiality_level VARCHAR(50) NOT NULL,
 allowed_users JSONB,
 expiry_date TIMESTAMP,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP
);
```

### Access Logs Table
```sql
CREATE TABLE access_logs (
 log_id UUID PRIMARY KEY,
 user_id VARCHAR(255) NOT NULL,
 document_id UUID NOT NULL,
 action VARCHAR(50) NOT NULL,
 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 ip_address VARCHAR(45),
 user_agent TEXT
);
```

### Data Minimization Settings Table
```sql
CREATE TABLE data_minimization_settings (
 setting_id UUID PRIMARY KEY,
 user_id VARCHAR(255) NOT NULL,
 collect_only_essential VARCHAR(10) DEFAULT 'true',
 retention_days INTEGER DEFAULT 90,
 auto_delete_after_retention VARCHAR(10) DEFAULT 'true',
 anonymize_personal_info VARCHAR(10) DEFAULT 'true',
 applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP
);
```

## Services

### GDPRComplianceService
Handles GDPR-related operations including data deletion and export.

### COPPAComplianceService
Manages COPPA compliance including parental consent and data minimization.

### PrivacyControlsService
Implements document confidentiality settings and access logging.

### DocumentAccessControl
Manages document access permissions and user access lists.

### EncryptionService
Provides encryption/decryption for sensitive document content.

### AuditTrailService
Manages comprehensive audit trails for compliance reporting.

### DataRetentionService
Handles data retention policies and automatic deletion.

### PersonalInfoAnonymizer
Anonymizes personal information while preserving data utility.

### AgeVerificationService
Determines if COPPA compliance measures are required.

### PrivacyPolicyService
Manages privacy policy acceptance and version tracking.

## Usage Examples

### Example 1: Handle GDPR Data Deletion Request

```python
from api.compliance import GDPRComplianceService, DataDeletionRequest

# Create deletion request
request = DataDeletionRequest(
 user_id="user123",
 reason="User requested account deletion",
 delete_documents=True,
 delete_extracted_data=True,
 delete_access_logs=False
)

# Execute deletion
service = GDPRComplianceService(db_session, storage_service)
response = await service.delete_user_data(request)

print(f"Deleted {response.deleted_documents} documents")
print(f"Deleted {response.deleted_loans} loan records")
```

### Example 2: Request Parental Consent

```python
from api.compliance import COPPAComplianceService, ParentalConsentRequest

# Create consent request
request = ParentalConsentRequest(
 child_user_id="child123",
 parent_name="Jane Smith",
 parent_email="jane.smith@example.com",
 consent_granted=True,
 verification_method="email_verification"
)

# Process consent
service = COPPAComplianceService(db_session)
response = await service.request_parental_consent(request)

print(f"Consent status: {response.consent_status}")
```

### Example 3: Set Document Confidentiality

```python
from api.compliance import PrivacyControlsService, PrivacyControlsRequest, ConfidentialityLevel

# Create privacy request
request = PrivacyControlsRequest(
 document_id="doc123",
 confidentiality_level=ConfidentialityLevel.CONFIDENTIAL,
 allowed_users=["user1", "user2"],
 expiry_date=datetime(2024, 12, 31)
)

# Apply privacy controls
service = PrivacyControlsService(db_session)
response = await service.set_document_confidentiality(request)

print(f"Privacy controls applied: {response.confidentiality_level}")
```

### Example 4: Log Document Access

```python
from api.compliance import PrivacyControlsService

service = PrivacyControlsService(db_session)

# Log access
await service.log_document_access(
 user_id="user123",
 document_id="doc123",
 action="view",
 ip_address="192.168.1.1",
 user_agent="Mozilla/5.0..."
)
```

## Security Considerations

1. **Encryption**: All sensitive data should be encrypted at rest and in transit
2. **Authentication**: All endpoints require proper authentication
3. **Authorization**: Users can only access/delete their own data
4. **Audit Logging**: All compliance operations are logged
5. **Data Retention**: Automatic cleanup of expired data
6. **Access Control**: Role-based access control for sensitive operations

## Compliance Checklist

### GDPR Compliance
- [x] Right to erasure (data deletion)
- [x] Right to data portability (data export)
- [x] Audit trail for data access
- [x] Encryption at rest and in transit
- [x] Access control mechanisms

### COPPA Compliance
- [x] Parental consent mechanisms
- [x] Age verification
- [x] Data minimization controls
- [x] Automatic data deletion
- [x] Personal information anonymization

### Privacy Controls
- [x] Document confidentiality settings
- [x] Access logging
- [x] User access control lists
- [x] Time-based access expiry
- [x] Comprehensive audit trails

## Testing

Run compliance tests:
```bash
pytest tests/test_compliance.py -v
```

## Monitoring

Monitor compliance operations:
- Track deletion requests and completion rates
- Monitor parental consent requests
- Audit access log volumes
- Track data retention cleanup operations

## Support

For questions or issues related to compliance features, contact the development team or refer to the main project documentation.
