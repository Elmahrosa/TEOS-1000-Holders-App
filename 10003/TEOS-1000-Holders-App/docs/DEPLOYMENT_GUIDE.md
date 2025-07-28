# Deployment Guide for $TEOS Contribution Pool

## Overview

This guide covers the deployment process for the $TEOS Private Contribution Pool system, including smart contracts, backend services, and frontend applications.

## Prerequisites

Before deploying, ensure you have:

- Solana CLI tools installed and configured
- Node.js (version 18+) and npm/pnpm
- Python 3.8+ and pip
- Git for version control
- Access to deployment environments (mainnet, devnet, etc.)

## Environment Setup

### Development Environment

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd teos_contribution_pool
   ```

2. **Install Dependencies**
   ```bash
   # Frontend
   cd frontend
   npm install
   
   # Backend
   cd ../backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Smart Contract
   cd ../smart_contract
   anchor build
   ```

### Production Environment

1. **Server Requirements**
   - Ubuntu 20.04+ or similar Linux distribution
   - 2+ CPU cores
   - 4GB+ RAM
   - 50GB+ storage
   - SSL certificate for HTTPS

2. **Domain Configuration**
   - Configure DNS records for your domain
   - Set up SSL certificates (Let's Encrypt recommended)
   - Configure reverse proxy (Nginx recommended)

## Smart Contract Deployment

### Solana Devnet Deployment

1. **Configure Solana CLI**
   ```bash
   solana config set --url devnet
   solana-keygen new --outfile ~/.config/solana/id.json
   solana airdrop 2
   ```

2. **Build and Deploy Contract**
   ```bash
   cd smart_contract
   anchor build
   anchor deploy --provider.cluster devnet
   ```

3. **Update Program ID**
   - Copy the deployed program ID
   - Update `declare_id!()` in `lib.rs`
   - Update frontend configuration with new program ID

### Solana Mainnet Deployment

1. **Configure Mainnet**
   ```bash
   solana config set --url mainnet-beta
   ```

2. **Fund Deployment Account**
   - Transfer sufficient SOL for deployment costs
   - Verify account balance: `solana balance`

3. **Deploy to Mainnet**
   ```bash
   anchor deploy --provider.cluster mainnet-beta
   ```

4. **Verify Deployment**
   - Test contract functions on mainnet
   - Verify program ID matches expectations

## Backend Deployment

### Local Development

```bash
cd backend
source venv/bin/activate
python src/main.py
```

### Production Deployment with Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY src/ ./src/
   
   EXPOSE 5000
   CMD ["python", "src/main.py"]
   ```

2. **Build and Run Container**
   ```bash
   docker build -t teos-backend .
   docker run -p 5000:5000 teos-backend
   ```

### Production Deployment with Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create Gunicorn Configuration**
   ```python
   # gunicorn.conf.py
   bind = "0.0.0.0:5000"
   workers = 4
   worker_class = "sync"
   timeout = 30
   keepalive = 2
   max_requests = 1000
   max_requests_jitter = 100
   ```

3. **Start with Gunicorn**
   ```bash
   gunicorn --config gunicorn.conf.py src.main:app
   ```

### Database Configuration

1. **SQLite (Development)**
   - Default configuration uses SQLite
   - Database file created automatically

2. **PostgreSQL (Production)**
   ```bash
   # Install PostgreSQL
   sudo apt-get install postgresql postgresql-contrib
   
   # Create database and user
   sudo -u postgres createdb teos_pool
   sudo -u postgres createuser teos_user
   sudo -u postgres psql -c "ALTER USER teos_user PASSWORD 'secure_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE teos_pool TO teos_user;"
   ```

3. **Update Configuration**
   ```python
   # In src/main.py
   app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://teos_user:secure_password@localhost/teos_pool'
   ```

## Frontend Deployment

### Build for Production

```bash
cd frontend
npm run build
```

### Static Hosting (Netlify/Vercel)

1. **Netlify Deployment**
   ```bash
   # Install Netlify CLI
   npm install -g netlify-cli
   
   # Deploy
   netlify deploy --prod --dir=dist
   ```

2. **Vercel Deployment**
   ```bash
   # Install Vercel CLI
   npm install -g vercel
   
   # Deploy
   vercel --prod
   ```

### Self-Hosted with Nginx

1. **Install Nginx**
   ```bash
   sudo apt-get install nginx
   ```

2. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           root /var/www/teos-frontend;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Copy Build Files**
   ```bash
   sudo cp -r frontend/dist/* /var/www/teos-frontend/
   sudo chown -R www-data:www-data /var/www/teos-frontend
   ```

## Full-Stack Deployment

### Using Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     backend:
       build: ./backend
       ports:
         - "5000:5000"
       environment:
         - DATABASE_URL=postgresql://teos_user:password@db:5432/teos_pool
       depends_on:
         - db
   
     frontend:
       build: ./frontend
       ports:
         - "80:80"
       depends_on:
         - backend
   
     db:
       image: postgres:13
       environment:
         POSTGRES_DB: teos_pool
         POSTGRES_USER: teos_user
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
   volumes:
     postgres_data:
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Environment Variables

### Backend Environment Variables

```bash
# .env file
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
PROGRAM_ID=your-deployed-program-id
DEBUG=False
```

### Frontend Environment Variables

```bash
# .env file
VITE_API_BASE_URL=https://api.your-domain.com
VITE_SOLANA_NETWORK=mainnet-beta
VITE_PROGRAM_ID=your-deployed-program-id
```

## SSL Configuration

### Using Certbot (Let's Encrypt)

1. **Install Certbot**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. **Obtain Certificate**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Auto-renewal**
   ```bash
   sudo crontab -e
   # Add: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

## Monitoring and Logging

### Application Monitoring

1. **Install Monitoring Tools**
   ```bash
   pip install prometheus-flask-exporter
   ```

2. **Configure Logging**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s %(levelname)s %(name)s %(message)s',
       handlers=[
           logging.FileHandler('/var/log/teos-backend.log'),
           logging.StreamHandler()
       ]
   )
   ```

### System Monitoring

1. **Install System Monitoring**
   ```bash
   sudo apt-get install htop iotop nethogs
   ```

2. **Set up Log Rotation**
   ```bash
   sudo nano /etc/logrotate.d/teos-backend
   ```
   
   ```
   /var/log/teos-backend.log {
       daily
       missingok
       rotate 52
       compress
       delaycompress
       notifempty
       create 644 www-data www-data
   }
   ```

## Security Considerations

### Backend Security

1. **Firewall Configuration**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Secure Headers**
   ```python
   from flask_talisman import Talisman
   
   Talisman(app, force_https=True)
   ```

### Database Security

1. **Secure PostgreSQL**
   ```bash
   sudo nano /etc/postgresql/13/main/postgresql.conf
   # Set: listen_addresses = 'localhost'
   
   sudo nano /etc/postgresql/13/main/pg_hba.conf
   # Configure authentication methods
   ```

2. **Regular Backups**
   ```bash
   # Create backup script
   #!/bin/bash
   pg_dump -U teos_user teos_pool > /backups/teos_pool_$(date +%Y%m%d_%H%M%S).sql
   ```

## Troubleshooting

### Common Issues

1. **Smart Contract Deployment Fails**
   - Check Solana CLI configuration
   - Verify sufficient SOL balance
   - Ensure Anchor version compatibility

2. **Backend API Errors**
   - Check database connection
   - Verify environment variables
   - Review application logs

3. **Frontend Build Issues**
   - Clear node_modules and reinstall
   - Check environment variables
   - Verify API endpoint configuration

### Debugging Commands

```bash
# Check Solana configuration
solana config get

# Test API endpoints
curl -X GET http://localhost:5000/api/health

# Check application logs
tail -f /var/log/teos-backend.log

# Monitor system resources
htop
```

## Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   # Backend
   pip list --outdated
   pip install -U package_name
   
   # Frontend
   npm outdated
   npm update
   ```

2. **Database Maintenance**
   ```bash
   # PostgreSQL maintenance
   sudo -u postgres psql -c "VACUUM ANALYZE;"
   ```

3. **Log Cleanup**
   ```bash
   # Clean old logs
   sudo logrotate -f /etc/logrotate.d/teos-backend
   ```

### Backup Strategy

1. **Database Backups**
   - Daily automated backups
   - Weekly full backups
   - Monthly archive backups

2. **Application Backups**
   - Code repository backups
   - Configuration file backups
   - SSL certificate backups

## Performance Optimization

### Backend Optimization

1. **Database Indexing**
   ```sql
   CREATE INDEX idx_contributions_wallet ON contributions(wallet_address);
   CREATE INDEX idx_contributions_created ON contributions(created_at);
   ```

2. **Caching**
   ```python
   from flask_caching import Cache
   
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   ```

### Frontend Optimization

1. **Bundle Analysis**
   ```bash
   npm run build -- --analyze
   ```

2. **CDN Configuration**
   - Use CDN for static assets
   - Enable gzip compression
   - Implement caching headers

This deployment guide provides comprehensive instructions for deploying the $TEOS Contribution Pool system in various environments, from development to production.

