from flask import Blueprint, request, jsonify
from src.models.contribution import db, Contribution, PoolStats, Holder
from datetime import datetime
import logging

contribution_bp = Blueprint('contribution', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contribution_bp.route('/pool/stats', methods=['GET'])
def get_pool_stats():
    """Get current pool statistics"""
    try:
        stats = PoolStats.query.first()
        if not stats:
            # Initialize default stats if none exist
            stats = PoolStats(
                total_contributors=347,  # Mock data matching frontend
                verified_contributors=347,
                total_sol_contributed=17350.0,  # 347 * 50
                total_sol_locked=8675.0,  # 50% locked
                total_teos_distributed=3470000.0,  # 347 * 10000
                trading_unlocked=False,
                sol_unlocked=False
            )
            db.session.add(stats)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': stats.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting pool stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve pool statistics'
        }), 500

@contribution_bp.route('/contribute', methods=['POST'])
def contribute():
    """Handle SOL contribution and TEOS distribution"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['wallet_address', 'sol_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        wallet_address = data['wallet_address']
        sol_amount = float(data['sol_amount'])
        
        # Validate SOL amount (should be $50 equivalent)
        if sol_amount != 50.0:
            return jsonify({
                'success': False,
                'error': 'Contribution must be exactly $50 worth of SOL'
            }), 400
        
        # Check if wallet already contributed
        existing_contribution = Contribution.query.filter_by(wallet_address=wallet_address).first()
        if existing_contribution:
            return jsonify({
                'success': False,
                'error': 'Wallet has already contributed to the pool'
            }), 400
        
        # Create new contribution
        teos_amount = 10000.0  # Fixed amount of TEOS tokens
        contribution = Contribution(
            wallet_address=wallet_address,
            sol_amount=sol_amount,
            teos_amount=teos_amount,
            transaction_hash=data.get('transaction_hash'),
            verified=True  # Auto-verify for demo purposes
        )
        
        db.session.add(contribution)
        
        # Update pool stats
        stats = PoolStats.query.first()
        if not stats:
            stats = PoolStats()
            db.session.add(stats)
        
        stats.total_contributors += 1
        stats.verified_contributors += 1
        stats.total_sol_contributed += sol_amount
        stats.total_sol_locked += sol_amount / 2  # 50% locked
        stats.total_teos_distributed += teos_amount
        
        # Check if trading should be unlocked (500 contributors)
        if stats.verified_contributors >= 500 and not stats.trading_unlocked:
            stats.trading_unlocked = True
        
        # Check if SOL should be unlocked (10,000 holders)
        if stats.verified_contributors >= 10000 and not stats.sol_unlocked:
            stats.sol_unlocked = True
            stats.total_sol_locked = 0.0  # Unlock all SOL
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'contribution': contribution.to_dict(),
                'pool_stats': stats.to_dict()
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid numeric value provided'
        }), 400
    except Exception as e:
        logger.error(f"Error processing contribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process contribution'
        }), 500

@contribution_bp.route('/contributions', methods=['GET'])
def get_contributions():
    """Get all contributions with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        verified_only = request.args.get('verified', 'false').lower() == 'true'
        
        query = Contribution.query
        if verified_only:
            query = query.filter_by(verified=True)
        
        contributions = query.order_by(Contribution.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'contributions': [c.to_dict() for c in contributions.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': contributions.total,
                    'pages': contributions.pages,
                    'has_next': contributions.has_next,
                    'has_prev': contributions.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contributions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve contributions'
        }), 500

@contribution_bp.route('/verify/<wallet_address>', methods=['POST'])
def verify_contribution(wallet_address):
    """Verify a contribution (admin endpoint)"""
    try:
        contribution = Contribution.query.filter_by(wallet_address=wallet_address).first()
        if not contribution:
            return jsonify({
                'success': False,
                'error': 'Contribution not found'
            }), 404
        
        if contribution.verified:
            return jsonify({
                'success': False,
                'error': 'Contribution already verified'
            }), 400
        
        contribution.verified = True
        contribution.updated_at = datetime.utcnow()
        
        # Update pool stats
        stats = PoolStats.query.first()
        if stats:
            stats.verified_contributors += 1
            
            # Check unlock conditions
            if stats.verified_contributors >= 500 and not stats.trading_unlocked:
                stats.trading_unlocked = True
            
            if stats.verified_contributors >= 10000 and not stats.sol_unlocked:
                stats.sol_unlocked = True
                stats.total_sol_locked = 0.0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': contribution.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying contribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify contribution'
        }), 500

@contribution_bp.route('/holders', methods=['GET'])
def get_holders():
    """Get all verified holders"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        holders = Holder.query.filter_by(verified=True).order_by(
            Holder.teos_balance.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'holders': [h.to_dict() for h in holders.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': holders.total,
                    'pages': holders.pages,
                    'has_next': holders.has_next,
                    'has_prev': holders.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting holders: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve holders'
        }), 500

@contribution_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'TEOS Contribution Pool API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

