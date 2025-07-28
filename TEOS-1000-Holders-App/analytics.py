from flask import Blueprint, jsonify, request
from src.models.contribution import db, Contribution, PoolStats, Holder
from src.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

analytics_bp = Blueprint('analytics', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        # Get pool stats
        pool_stats = PoolStats.query.first()
        if not pool_stats:
            pool_stats = PoolStats()
        
        # Get contribution trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_contributions = Contribution.query.filter(
            Contribution.created_at >= thirty_days_ago
        ).count()
        
        # Get daily contribution counts for the last 7 days
        daily_stats = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            daily_count = Contribution.query.filter(
                Contribution.created_at >= start_of_day,
                Contribution.created_at < end_of_day
            ).count()
            
            daily_stats.append({
                'date': start_of_day.strftime('%Y-%m-%d'),
                'contributions': daily_count
            })
        
        # Calculate progress percentages
        trading_unlock_progress = min((pool_stats.verified_contributors / 500) * 100, 100)
        sol_unlock_progress = min((pool_stats.verified_contributors / 10000) * 100, 100)
        
        # Get top holders
        top_holders = Holder.query.filter_by(verified=True).order_by(
            Holder.teos_balance.desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'pool_stats': pool_stats.to_dict(),
                'recent_contributions': recent_contributions,
                'daily_stats': daily_stats,
                'progress': {
                    'trading_unlock': trading_unlock_progress,
                    'sol_unlock': sol_unlock_progress
                },
                'milestones': {
                    'trading_unlock_target': 500,
                    'sol_unlock_target': 10000,
                    'current_verified': pool_stats.verified_contributors
                },
                'top_holders': [holder.to_dict() for holder in top_holders]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard statistics'
        }), 500

@analytics_bp.route('/contribution-trends', methods=['GET'])
def get_contribution_trends():
    """Get detailed contribution trends and analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get contributions grouped by day
        daily_contributions = db.session.query(
            func.date(Contribution.created_at).label('date'),
            func.count(Contribution.id).label('count'),
            func.sum(Contribution.sol_amount).label('total_sol'),
            func.sum(Contribution.teos_amount).label('total_teos')
        ).filter(
            Contribution.created_at >= start_date
        ).group_by(
            func.date(Contribution.created_at)
        ).order_by('date').all()
        
        # Format the data
        trends = []
        for row in daily_contributions:
            trends.append({
                'date': row.date.strftime('%Y-%m-%d'),
                'contributions': row.count,
                'sol_amount': float(row.total_sol or 0),
                'teos_amount': float(row.total_teos or 0)
            })
        
        # Calculate cumulative stats
        cumulative_contributions = 0
        cumulative_sol = 0
        cumulative_teos = 0
        
        for trend in trends:
            cumulative_contributions += trend['contributions']
            cumulative_sol += trend['sol_amount']
            cumulative_teos += trend['teos_amount']
            
            trend['cumulative_contributions'] = cumulative_contributions
            trend['cumulative_sol'] = cumulative_sol
            trend['cumulative_teos'] = cumulative_teos
        
        return jsonify({
            'success': True,
            'data': {
                'trends': trends,
                'period_days': days,
                'total_period_contributions': cumulative_contributions,
                'total_period_sol': cumulative_sol,
                'total_period_teos': cumulative_teos
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting contribution trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve contribution trends'
        }), 500

@analytics_bp.route('/holder-distribution', methods=['GET'])
def get_holder_distribution():
    """Get holder distribution analytics"""
    try:
        # Get holder balance distribution
        balance_ranges = [
            (0, 1000),
            (1000, 5000),
            (5000, 10000),
            (10000, 50000),
            (50000, 100000),
            (100000, float('inf'))
        ]
        
        distribution = []
        for min_balance, max_balance in balance_ranges:
            if max_balance == float('inf'):
                count = Holder.query.filter(
                    Holder.teos_balance >= min_balance,
                    Holder.verified == True
                ).count()
                range_label = f"{min_balance:,}+"
            else:
                count = Holder.query.filter(
                    Holder.teos_balance >= min_balance,
                    Holder.teos_balance < max_balance,
                    Holder.verified == True
                ).count()
                range_label = f"{min_balance:,} - {max_balance:,}"
            
            distribution.append({
                'range': range_label,
                'count': count,
                'min_balance': min_balance,
                'max_balance': max_balance if max_balance != float('inf') else None
            })
        
        # Get verification method distribution
        verification_methods = db.session.query(
            Holder.verification_method,
            func.count(Holder.id).label('count')
        ).filter(
            Holder.verified == True
        ).group_by(
            Holder.verification_method
        ).all()
        
        verification_stats = [
            {
                'method': method or 'Unknown',
                'count': count
            }
            for method, count in verification_methods
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'balance_distribution': distribution,
                'verification_methods': verification_stats,
                'total_verified_holders': sum(item['count'] for item in distribution)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting holder distribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve holder distribution'
        }), 500

@analytics_bp.route('/pool-health', methods=['GET'])
def get_pool_health():
    """Get pool health metrics and status"""
    try:
        pool_stats = PoolStats.query.first()
        if not pool_stats:
            pool_stats = PoolStats()
        
        # Calculate health metrics
        contribution_rate = pool_stats.verified_contributors / max(pool_stats.total_contributors, 1)
        sol_lock_ratio = pool_stats.total_sol_locked / max(pool_stats.total_sol_contributed, 1)
        
        # Determine pool phase
        if pool_stats.verified_contributors < 500:
            phase = "Initial Contribution Phase"
            next_milestone = 500
            next_milestone_description = "Private Trading Unlock"
        elif pool_stats.verified_contributors < 10000:
            phase = "Private Trading Phase"
            next_milestone = 10000
            next_milestone_description = "Full SOL Unlock & Exchange Listings"
        else:
            phase = "Full Launch Phase"
            next_milestone = None
            next_milestone_description = "All milestones achieved"
        
        # Calculate time estimates (mock data for demonstration)
        current_rate = 10  # contributions per day (mock)
        if next_milestone:
            remaining_contributions = next_milestone - pool_stats.verified_contributors
            estimated_days = max(remaining_contributions / current_rate, 0) if current_rate > 0 else None
        else:
            estimated_days = None
        
        health_score = min(
            (pool_stats.verified_contributors / 10000) * 100,
            100
        )
        
        return jsonify({
            'success': True,
            'data': {
                'pool_stats': pool_stats.to_dict(),
                'health_metrics': {
                    'contribution_rate': round(contribution_rate * 100, 2),
                    'sol_lock_ratio': round(sol_lock_ratio * 100, 2),
                    'health_score': round(health_score, 2)
                },
                'phase_info': {
                    'current_phase': phase,
                    'next_milestone': next_milestone,
                    'next_milestone_description': next_milestone_description,
                    'estimated_days_to_milestone': estimated_days
                },
                'features_unlocked': {
                    'private_trading': pool_stats.trading_unlocked,
                    'sol_unlock': pool_stats.sol_unlocked,
                    'exchange_ready': pool_stats.verified_contributors >= 10000
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pool health: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve pool health metrics'
        }), 500

@analytics_bp.route('/export/contributions', methods=['GET'])
def export_contributions():
    """Export contributions data (admin endpoint)"""
    try:
        format_type = request.args.get('format', 'json')
        verified_only = request.args.get('verified', 'false').lower() == 'true'
        
        query = Contribution.query
        if verified_only:
            query = query.filter_by(verified=True)
        
        contributions = query.order_by(Contribution.created_at.desc()).all()
        
        if format_type == 'csv':
            # For CSV export, you would typically use pandas or csv module
            # For now, returning JSON with CSV-like structure
            csv_data = []
            csv_data.append(['Wallet Address', 'SOL Amount', 'TEOS Amount', 'Verified', 'Created At'])
            
            for contrib in contributions:
                csv_data.append([
                    contrib.wallet_address,
                    contrib.sol_amount,
                    contrib.teos_amount,
                    contrib.verified,
                    contrib.created_at.isoformat() if contrib.created_at else ''
                ])
            
            return jsonify({
                'success': True,
                'data': csv_data,
                'format': 'csv_array'
            }), 200
        
        else:  # JSON format
            return jsonify({
                'success': True,
                'data': [contrib.to_dict() for contrib in contributions],
                'format': 'json',
                'total_records': len(contributions)
            }), 200
        
    except Exception as e:
        logger.error(f"Error exporting contributions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export contributions data'
        }), 500

