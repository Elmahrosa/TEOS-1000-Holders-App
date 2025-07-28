from flask import Blueprint, jsonify, request
from src.models.contribution import db, Contribution, PoolStats, Holder
from src.models.user import User
from datetime import datetime
import logging
import os

admin_bp = Blueprint('admin', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple admin authentication (in production, use proper JWT or session management)
def verify_admin_token(token):
    """Verify admin authentication token"""
    # In production, implement proper token verification
    return token == "admin_secret_token_2025"

def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Admin authentication required'
            }), 401
        
        token = auth_header.split(' ')[1]
        if not verify_admin_token(token):
            return jsonify({
                'success': False,
                'error': 'Invalid admin token'
            }), 401
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/system/status', methods=['GET'])
@admin_required
def get_system_status():
    """Get comprehensive system status"""
    try:
        # Database status
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        # Get counts
        total_contributions = Contribution.query.count()
        verified_contributions = Contribution.query.filter_by(verified=True).count()
        total_holders = Holder.query.count()
        verified_holders = Holder.query.filter_by(verified=True).count()
        total_users = User.query.count()
        
        # Pool stats
        pool_stats = PoolStats.query.first()
        
        # System info
        system_info = {
            'database_status': db_status,
            'total_contributions': total_contributions,
            'verified_contributions': verified_contributions,
            'total_holders': total_holders,
            'verified_holders': verified_holders,
            'total_users': total_users,
            'pool_stats': pool_stats.to_dict() if pool_stats else None,
            'server_time': datetime.utcnow().isoformat(),
            'database_file_exists': os.path.exists(
                os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
            )
        }
        
        return jsonify({
            'success': True,
            'data': system_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system status'
        }), 500

@admin_bp.route('/pool/reset-stats', methods=['POST'])
@admin_required
def reset_pool_stats():
    """Reset pool statistics (dangerous operation)"""
    try:
        data = request.get_json()
        confirm = data.get('confirm', False) if data else False
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Confirmation required. Send {"confirm": true} to proceed.'
            }), 400
        
        # Delete existing stats
        PoolStats.query.delete()
        
        # Create fresh stats
        new_stats = PoolStats(
            total_contributors=0,
            verified_contributors=0,
            total_sol_contributed=0.0,
            total_sol_locked=0.0,
            total_teos_distributed=0.0,
            trading_unlocked=False,
            sol_unlocked=False
        )
        
        db.session.add(new_stats)
        db.session.commit()
        
        logger.info("Pool statistics reset by admin")
        
        return jsonify({
            'success': True,
            'message': 'Pool statistics have been reset',
            'data': new_stats.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting pool stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset pool statistics'
        }), 500

@admin_bp.route('/contributions/bulk-verify', methods=['POST'])
@admin_required
def bulk_verify_contributions():
    """Bulk verify contributions"""
    try:
        data = request.get_json()
        
        if not data:
            # Verify all unverified contributions
            unverified = Contribution.query.filter_by(verified=False).all()
        else:
            contribution_ids = data.get('contribution_ids', [])
            if contribution_ids:
                unverified = Contribution.query.filter(
                    Contribution.id.in_(contribution_ids)
                ).all()
            else:
                unverified = Contribution.query.filter_by(verified=False).all()
        
        verified_count = 0
        for contribution in unverified:
            if not contribution.verified:
                contribution.verified = True
                contribution.updated_at = datetime.utcnow()
                verified_count += 1
        
        # Update pool stats
        pool_stats = PoolStats.query.first()
        if pool_stats:
            pool_stats.verified_contributors += verified_count
            
            # Check unlock conditions
            if pool_stats.verified_contributors >= 500 and not pool_stats.trading_unlocked:
                pool_stats.trading_unlocked = True
            
            if pool_stats.verified_contributors >= 10000 and not pool_stats.sol_unlocked:
                pool_stats.sol_unlocked = True
                pool_stats.total_sol_locked = 0.0
        
        db.session.commit()
        
        logger.info(f"Admin bulk verified {verified_count} contributions")
        
        return jsonify({
            'success': True,
            'message': f'Successfully verified {verified_count} contributions',
            'verified_count': verified_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk verification: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to bulk verify contributions'
        }), 500

@admin_bp.route('/contributions/<int:contribution_id>/delete', methods=['DELETE'])
@admin_required
def delete_contribution(contribution_id):
    """Delete a specific contribution (admin only)"""
    try:
        contribution = Contribution.query.get_or_404(contribution_id)
        
        # Update pool stats before deletion
        pool_stats = PoolStats.query.first()
        if pool_stats:
            pool_stats.total_contributors -= 1
            if contribution.verified:
                pool_stats.verified_contributors -= 1
            pool_stats.total_sol_contributed -= contribution.sol_amount
            pool_stats.total_sol_locked -= contribution.sol_amount / 2
            pool_stats.total_teos_distributed -= contribution.teos_amount
        
        wallet_address = contribution.wallet_address
        db.session.delete(contribution)
        db.session.commit()
        
        logger.info(f"Admin deleted contribution for wallet {wallet_address}")
        
        return jsonify({
            'success': True,
            'message': f'Contribution for wallet {wallet_address} has been deleted'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting contribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete contribution'
        }), 500

@admin_bp.route('/pool/update-stats', methods=['POST'])
@admin_required
def update_pool_stats():
    """Manually update pool statistics"""
    try:
        data = request.get_json()
        
        pool_stats = PoolStats.query.first()
        if not pool_stats:
            pool_stats = PoolStats()
            db.session.add(pool_stats)
        
        # Update provided fields
        if 'total_contributors' in data:
            pool_stats.total_contributors = int(data['total_contributors'])
        
        if 'verified_contributors' in data:
            pool_stats.verified_contributors = int(data['verified_contributors'])
        
        if 'total_sol_contributed' in data:
            pool_stats.total_sol_contributed = float(data['total_sol_contributed'])
        
        if 'total_sol_locked' in data:
            pool_stats.total_sol_locked = float(data['total_sol_locked'])
        
        if 'total_teos_distributed' in data:
            pool_stats.total_teos_distributed = float(data['total_teos_distributed'])
        
        if 'trading_unlocked' in data:
            pool_stats.trading_unlocked = bool(data['trading_unlocked'])
        
        if 'sol_unlocked' in data:
            pool_stats.sol_unlocked = bool(data['sol_unlocked'])
        
        pool_stats.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info("Pool statistics manually updated by admin")
        
        return jsonify({
            'success': True,
            'message': 'Pool statistics updated successfully',
            'data': pool_stats.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating pool stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update pool statistics'
        }), 500

@admin_bp.route('/database/backup', methods=['POST'])
@admin_required
def backup_database():
    """Create a backup of the database"""
    try:
        import shutil
        from datetime import datetime
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backup created: {backup_filename}")
        
        return jsonify({
            'success': True,
            'message': 'Database backup created successfully',
            'backup_filename': backup_filename,
            'backup_path': backup_path
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create database backup'
        }), 500

@admin_bp.route('/logs/recent', methods=['GET'])
@admin_required
def get_recent_logs():
    """Get recent system logs (mock implementation)"""
    try:
        # In a real implementation, you would read from actual log files
        mock_logs = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'message': 'System status check completed',
                'module': 'admin'
            },
            {
                'timestamp': (datetime.utcnow()).isoformat(),
                'level': 'INFO',
                'message': 'New contribution processed',
                'module': 'contribution'
            },
            {
                'timestamp': (datetime.utcnow()).isoformat(),
                'level': 'WARNING',
                'message': 'High contribution volume detected',
                'module': 'analytics'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': mock_logs,
                'total_logs': len(mock_logs)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recent logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recent logs'
        }), 500

