# TEOS-1000-Holders-App API Documentation

## Overview

This document provides comprehensive documentation for the TEOS Contribution Pool API. The API provides endpoints for managing contributions, wallet verification, analytics, and administrative functions.

**Base URL:** `http://localhost:5000/api`

## Authentication

Most endpoints are public, but admin endpoints require authentication:

```
Authorization: Bearer admin_secret_token_2025
```

## API Endpoints

### Contribution Management

#### Get Pool Statistics
```
GET /pool/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "total_contributors": 347,
    "verified_contributors": 347,
    "total_sol_contributed": 17350.0,
    "total_sol_locked": 8675.0,
    "total_teos_distributed": 3470000.0,
    "trading_unlocked": false,
    "sol_unlocked": false,
    "updated_at": "2025-01-25T12:00:00"
  }
}
```

#### Submit Contribution
```
POST /contribute
```

**Request Body:**
```json
{
  "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "sol_amount": 50.0,
  "transaction_hash": "optional_tx_hash"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "contribution": {
      "id": 1,
      "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
      "sol_amount": 50.0,
      "teos_amount": 10000.0,
      "verified": true,
      "created_at": "2025-01-25T12:00:00"
    },
    "pool_stats": { /* updated pool stats */ }
  }
}
```

#### Get All Contributions
```
GET /contributions?page=1&per_page=20&verified=true
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `verified` (optional): Filter by verification status

#### Verify Contribution (Admin)
```
POST /verify/{wallet_address}
```

#### Get Holders
```
GET /holders?page=1&per_page=50
```

#### Health Check
```
GET /health
```

### Wallet Management

#### Verify Wallet
```
POST /wallet/verify
```

**Request Body:**
```json
{
  "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "is_eligible": true,
    "verification_score": 85,
    "checks": {
      "valid_format": true,
      "not_duplicate": true,
      "sufficient_activity": true,
      "not_blacklisted": true
    }
  }
}
```

#### Get Wallet Balance
```
GET /wallet/balance/{wallet_address}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "teos_balance": 10000.0,
    "contribution_amount": 10000.0,
    "verified": true,
    "last_updated": "2025-01-25T12:00:00"
  }
}
```

#### Register Holder
```
POST /wallet/register-holder
```

**Request Body:**
```json
{
  "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "teos_balance": 10000.0,
  "verification_method": "manual"
}
```

#### Search Wallets
```
GET /wallet/search?q=9WzDX&type=all&limit=20
```

**Query Parameters:**
- `q`: Search query (minimum 3 characters)
- `type`: Search type (`contributors`, `holders`, `all`)
- `limit`: Maximum results (default: 20)

#### Bulk Verify Wallets (Admin)
```
POST /wallet/bulk-verify
```

**Request Body:**
```json
{
  "wallet_addresses": [
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "8VzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWN"
  ]
}
```

### Analytics

#### Dashboard Statistics
```
GET /analytics/dashboard
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pool_stats": { /* pool statistics */ },
    "recent_contributions": 25,
    "daily_stats": [
      {
        "date": "2025-01-25",
        "contributions": 5
      }
    ],
    "progress": {
      "trading_unlock": 69.4,
      "sol_unlock": 3.47
    },
    "milestones": {
      "trading_unlock_target": 500,
      "sol_unlock_target": 10000,
      "current_verified": 347
    },
    "top_holders": [ /* top 10 holders */ ]
  }
}
```

#### Contribution Trends
```
GET /analytics/contribution-trends?days=30
```

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

#### Holder Distribution
```
GET /analytics/holder-distribution
```

**Response:**
```json
{
  "success": true,
  "data": {
    "balance_distribution": [
      {
        "range": "0 - 1,000",
        "count": 50,
        "min_balance": 0,
        "max_balance": 1000
      }
    ],
    "verification_methods": [
      {
        "method": "manual",
        "count": 300
      }
    ],
    "total_verified_holders": 347
  }
}
```

#### Pool Health
```
GET /analytics/pool-health
```

#### Export Contributions
```
GET /analytics/export/contributions?format=json&verified=true
```

**Query Parameters:**
- `format`: Export format (`json`, `csv`)
- `verified`: Include only verified contributions

### Administrative Functions

All admin endpoints require authentication header:
```
Authorization: Bearer admin_secret_token_2025
```

#### System Status
```
GET /admin/system/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "database_status": "healthy",
    "total_contributions": 347,
    "verified_contributions": 347,
    "total_holders": 347,
    "verified_holders": 347,
    "total_users": 0,
    "pool_stats": { /* current pool stats */ },
    "server_time": "2025-01-25T12:00:00",
    "database_file_exists": true
  }
}
```

#### Reset Pool Statistics
```
POST /admin/pool/reset-stats
```

**Request Body:**
```json
{
  "confirm": true
}
```

#### Bulk Verify Contributions
```
POST /admin/contributions/bulk-verify
```

**Request Body (optional):**
```json
{
  "contribution_ids": [1, 2, 3]
}
```

#### Delete Contribution
```
DELETE /admin/contributions/{contribution_id}/delete
```

#### Update Pool Statistics
```
POST /admin/pool/update-stats
```

**Request Body:**
```json
{
  "total_contributors": 350,
  "verified_contributors": 350,
  "total_sol_contributed": 17500.0,
  "trading_unlocked": false,
  "sol_unlocked": false
}
```

#### Backup Database
```
POST /admin/database/backup
```

#### Get Recent Logs
```
GET /admin/logs/recent
```

### User Management (Legacy)

#### Get All Users
```
GET /users
```

#### Create User
```
POST /users
```

#### Get User by ID
```
GET /users/{user_id}
```

#### Update User
```
PUT /users/{user_id}
```

#### Delete User
```
DELETE /users/{user_id}
```

## Error Responses

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting for:
- Contribution submissions
- Wallet verification requests
- Admin operations

## Security Considerations

1. **Admin Authentication**: Currently uses a simple token. Implement proper JWT or OAuth in production.
2. **Input Validation**: All inputs are validated for format and content.
3. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection attacks.
4. **CORS**: Currently allows all origins. Restrict in production.

## Database Schema

### Contributions Table
- `id`: Primary key
- `wallet_address`: Solana wallet address (unique)
- `sol_amount`: Amount of SOL contributed
- `teos_amount`: Amount of TEOS tokens received
- `transaction_hash`: Blockchain transaction hash
- `verified`: Verification status
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Holders Table
- `id`: Primary key
- `wallet_address`: Solana wallet address (unique)
- `teos_balance`: Current TEOS balance
- `verified`: Verification status
- `verification_method`: Method used for verification
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Pool Stats Table
- `id`: Primary key
- `total_contributors`: Total number of contributors
- `verified_contributors`: Number of verified contributors
- `total_sol_contributed`: Total SOL contributed
- `total_sol_locked`: Total SOL locked (50% of contributed)
- `total_teos_distributed`: Total TEOS tokens distributed
- `trading_unlocked`: Private trading status
- `sol_unlocked`: SOL unlock status
- `updated_at`: Last update timestamp

### Users Table (Legacy)
- `id`: Primary key
- `username`: User name
- `email`: User email
- `created_at`: Creation timestamp

## Development Setup

1. **Install Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Run Development Server:**
```bash
python src/main.py
```

3. **Database Initialization:**
The database is automatically created when the application starts.

## Production Deployment

1. **Environment Variables:**
   - Set `FLASK_ENV=production`
   - Configure proper secret key
   - Set up production database

2. **Security:**
   - Implement proper authentication
   - Configure CORS for specific domains
   - Set up HTTPS
   - Implement rate limiting

3. **Monitoring:**
   - Set up logging
   - Configure health checks
   - Monitor database performance

## API Testing

Use tools like Postman, curl, or any HTTP client to test the API endpoints. Example curl commands:

```bash
# Get pool stats
curl -X GET http://localhost:5000/api/pool/stats

# Submit contribution
curl -X POST http://localhost:5000/api/contribute \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "sol_amount": 50.0}'

# Admin system status
curl -X GET http://localhost:5000/api/admin/system/status \
  -H "Authorization: Bearer admin_secret_token_2025"
```

