# $TEOS Contribution Pool API Documentation

## Overview

The $TEOS Contribution Pool API provides endpoints for managing contributions, tracking pool statistics, and handling holder verification. The API is built using Flask and follows RESTful design principles.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, the API does not require authentication for read operations. Write operations may require authentication in future versions.

## Endpoints

### Health Check

#### GET /health

Returns the health status of the API.

**Response:**
```json
{
  "success": true,
  "message": "TEOS Contribution Pool API is running",
  "timestamp": "2025-07-24T18:15:06.618374"
}
```

### Pool Statistics

#### GET /pool/stats

Returns current pool statistics including contributor counts, SOL amounts, and unlock status.

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
    "updated_at": "2025-07-24T18:16:09.104104"
  }
}
```

### Contributions

#### POST /contribute

Submit a new contribution to the pool.

**Request Body:**
```json
{
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "sol_amount": 50.0,
  "transaction_hash": "optional_transaction_hash"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "contribution": {
      "id": 1,
      "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
      "sol_amount": 50.0,
      "teos_amount": 10000.0,
      "transaction_hash": "optional_transaction_hash",
      "verified": true,
      "created_at": "2025-07-24T18:16:09.104104",
      "updated_at": "2025-07-24T18:16:09.104104"
    },
    "pool_stats": {
      // Updated pool statistics
    }
  }
}
```

**Error Responses:**
- `400`: Invalid request data or contribution amount
- `400`: Wallet has already contributed
- `500`: Internal server error

#### GET /contributions

Retrieve all contributions with optional filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `verified` (optional): Filter by verification status (true/false)

**Response:**
```json
{
  "success": true,
  "data": {
    "contributions": [
      {
        "id": 1,
        "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        "sol_amount": 50.0,
        "teos_amount": 10000.0,
        "transaction_hash": "optional_transaction_hash",
        "verified": true,
        "created_at": "2025-07-24T18:16:09.104104",
        "updated_at": "2025-07-24T18:16:09.104104"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### Verification

#### POST /verify/{wallet_address}

Verify a contribution (admin endpoint).

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "sol_amount": 50.0,
    "teos_amount": 10000.0,
    "transaction_hash": "optional_transaction_hash",
    "verified": true,
    "created_at": "2025-07-24T18:16:09.104104",
    "updated_at": "2025-07-24T18:16:09.104104"
  }
}
```

**Error Responses:**
- `404`: Contribution not found
- `400`: Contribution already verified
- `500`: Internal server error

### Holders

#### GET /holders

Retrieve all verified holders with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "holders": [
      {
        "id": 1,
        "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        "teos_balance": 10000.0,
        "verified": true,
        "verification_method": "contribution_pool",
        "created_at": "2025-07-24T18:16:09.104104",
        "updated_at": "2025-07-24T18:16:09.104104"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions to prevent abuse.

## CORS

The API supports Cross-Origin Resource Sharing (CORS) and accepts requests from any origin during development. In production, this should be restricted to specific domains.

## Development

To run the API in development mode:

```bash
cd backend
source venv/bin/activate
python src/main.py
```

The API will be available at `http://localhost:5000` with debug mode enabled.

## Testing

API endpoints can be tested using tools like curl, Postman, or any HTTP client:

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Get pool statistics
curl http://localhost:5000/api/pool/stats

# Submit a contribution
curl -X POST http://localhost:5000/api/contribute \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", "sol_amount": 50.0}'
```

