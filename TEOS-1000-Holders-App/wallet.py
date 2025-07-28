from flask import Blueprint, jsonify, request
from src.models.contribution import db, Contribution, Holder
from datetime import datetime
import logging
import re

wallet_bp = Blueprint('wallet', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_solana_address(address):
    """Validate Solana wallet address format"""
    if not address or len(address) < 32 or len(address) > 44:
        return False
    
    # Basic pattern check for base58 characters
    pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
    return bool(re.match(pattern, address))

@wallet_bp.route('/verify', methods=['POST'])
def verify_wallet():
    """Verify wallet address and check eligibility"""
    try:
        data = request.get_json()
        
        if not data or 'wallet_address' not in data:
            return jsonify({
                'success': False,
                'error': 'Wallet address is required'
            }), 400
        
        wallet_address = data['wallet_address'].strip()
        
        # Validate wallet address format
        if not is_valid_solana_address(wallet_address):
            return jsonify({
                'success': False,
                'error': 'Invalid Solana wallet address format'
            }), 400
        
        # Check if wallet already contributed
        existing_contribution = Contribution.query.filter_by(
            wallet_address=wallet_address
        ).first()
        
        if existing_contribution:
            return jsonify({
                'success': False,
                'error': 'This wallet has already contributed to the pool',
                'contribution_details': existing_contribution.to_dict()
            }), 400
        
        # Check if wallet is already a holder
        existing_holder = Holder.query.filter_by(
            wallet_address=wallet_address
        ).first()
        
        # Mock verification logic (in production, this would check on-chain data)
        verification_score = 85  # Mock score
        is_eligible = verification_score >= 70
        
        verification_details = {
            'wallet_address': wallet_address,
            'is_eligible': is_eligible,
            'verification_score': verification_score,
            'checks': {
                'valid_format': True,
                'not_duplicate': True,
                'sufficient_activity': verification_score >= 70,
                'not_blacklisted': True
            },
            'existing_holder': existing_holder.to_dict() if existing_holder else None
        }
        
        return jsonify({
            'success': True,
            'data': verification_details
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying wallet: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify wallet address'
        }), 500

@wallet_bp.route('/balance/<wallet_address>', methods=['GET'])
def get_wallet_balance(wallet_address):
    """Get TEOS balance for a specific wallet"""
    try:
        if not is_valid_solana_address(wallet_address):
            return jsonify({
                'success': False,
                'error': 'Invalid Solana wallet address format'
            }), 400
        
        # Check contribution record
        contribution = Contribution.query.filter_by(
            wallet_address=wallet_address
        ).first()
        
        # Check holder record
        holder = Holder.query.filter_by(
            wallet_address=wallet_address
        ).first()
        
        balance_info = {
            'wallet_address': wallet_address,
            'teos_balance': 0.0,
            'contribution_amount': 0.0,
            'verified': False,
            'last_updated': None
        }
        
        if contribution:
            balance_info['contribution_amount'] = contribution.teos_amount
            balance_info['verified'] = contribution.verified
            balance_info['last_updated'] = contribution.updated_at.isoformat() if contribution.updated_at else None
        
        if holder:
            balance_info['teos_balance'] = holder.teos_balance
            balance_info['verified'] = holder.verified
            balance_info['last_updated'] = holder.updated_at.isoformat() if holder.updated_at else None
        
        # If both exist, use the higher balance
        if contribution and holder:
            balance_info['teos_balance'] = max(contribution.teos_amount, holder.teos_balance)
        elif contribution and not holder:
            balance_info['teos_balance'] = contribution.teos_amount
        
        return jsonify({
            'success': True,
            'data': balance_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting wallet balance: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve wallet balance'
        }), 500

@wallet_bp.route('/register-holder', methods=['POST'])
def register_holder():
    """Register a new TEOS holder"""
    try:
        data = request.get_json()
        
        required_fields = ['wallet_address', 'teos_balance']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        wallet_address = data['wallet_address'].strip()
        teos_balance = float(data['teos_balance'])
        verification_method = data.get('verification_method', 'manual')
        
        # Validate wallet address
        if not is_valid_solana_address(wallet_address):
            return jsonify({
                'success': False,
                'error': 'Invalid Solana wallet address format'
            }), 400
        
        # Check if holder already exists
        existing_holder = Holder.query.filter_by(
            wallet_address=wallet_address
        ).first()
        
        if existing_holder:
            # Update existing holder
            existing_holder.teos_balance = teos_balance
            existing_holder.verification_method = verification_method
            existing_holder.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': existing_holder.to_dict(),
                'message': 'Holder information updated'
            }), 200
        
        else:
            # Create new holder
            new_holder = Holder(
                wallet_address=wallet_address,
                teos_balance=teos_balance,
                verified=True,
                verification_method=verification_method
            )
            
            db.session.add(new_holder)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': new_holder.to_dict(),
                'message': 'New holder registered successfully'
            }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid numeric value for TEOS balance'
        }), 400
    except Exception as e:
        logger.error(f"Error registering holder: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to register holder'
        }), 500

@wallet_bp.route('/search', methods=['GET'])
def search_wallets():
    """Search for wallets by address or partial match"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # 'contributors', 'holders', 'all'
        limit = request.args.get('limit', 20, type=int)
        
        if not query or len(query) < 3:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 3 characters'
            }), 400
        
        results = {
            'contributors': [],
            'holders': [],
            'total_found': 0
        }
        
        # Search contributors
        if search_type in ['contributors', 'all']:
            contributors = Contribution.query.filter(
                Contribution.wallet_address.like(f'%{query}%')
            ).limit(limit).all()
            
            results['contributors'] = [
                {
                    **contrib.to_dict(),
                    'type': 'contributor'
                }
                for contrib in contributors
            ]
        
        # Search holders
        if search_type in ['holders', 'all']:
            holders = Holder.query.filter(
                Holder.wallet_address.like(f'%{query}%')
            ).limit(limit).all()
            
            results['holders'] = [
                {
                    **holder.to_dict(),
                    'type': 'holder'
                }
                for holder in holders
            ]
        
        results['total_found'] = len(results['contributors']) + len(results['holders'])
        
        return jsonify({
            'success': True,
            'data': results,
            'search_query': query,
            'search_type': search_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching wallets: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to search wallets'
        }), 500

@wallet_bp.route('/bulk-verify', methods=['POST'])
def bulk_verify_wallets():
    """Bulk verify multiple wallet addresses (admin endpoint)"""
    try:
        data = request.get_json()
        
        if not data or 'wallet_addresses' not in data:
            return jsonify({
                'success': False,
                'error': 'List of wallet addresses is required'
            }), 400
        
        wallet_addresses = data['wallet_addresses']
        
        if not isinstance(wallet_addresses, list) or len(wallet_addresses) == 0:
            return jsonify({
                'success': False,
                'error': 'wallet_addresses must be a non-empty list'
            }), 400
        
        if len(wallet_addresses) > 100:
            return jsonify({
                'success': False,
                'error': 'Maximum 100 wallet addresses allowed per request'
            }), 400
        
        results = {
            'verified': [],
            'failed': [],
            'already_verified': [],
            'not_found': []
        }
        
        for wallet_address in wallet_addresses:
            if not is_valid_solana_address(wallet_address):
                results['failed'].append({
                    'wallet_address': wallet_address,
                    'reason': 'Invalid address format'
                })
                continue
            
            # Check contribution
            contribution = Contribution.query.filter_by(
                wallet_address=wallet_address
            ).first()
            
            if contribution:
                if contribution.verified:
                    results['already_verified'].append(wallet_address)
                else:
                    contribution.verified = True
                    contribution.updated_at = datetime.utcnow()
                    results['verified'].append(wallet_address)
            else:
                results['not_found'].append(wallet_address)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': results,
            'summary': {
                'total_processed': len(wallet_addresses),
                'verified_count': len(results['verified']),
                'failed_count': len(results['failed']),
                'already_verified_count': len(results['already_verified']),
                'not_found_count': len(results['not_found'])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk verification: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process bulk verification'
        }), 500

