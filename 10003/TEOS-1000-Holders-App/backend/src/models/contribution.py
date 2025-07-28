from src.models.user import db
from datetime import datetime

class Contribution(db.Model):
    __tablename__ = 'contributions'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(44), nullable=False, unique=True)
    sol_amount = db.Column(db.Float, nullable=False)
    teos_amount = db.Column(db.Float, nullable=False)
    transaction_hash = db.Column(db.String(88), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'sol_amount': self.sol_amount,
            'teos_amount': self.teos_amount,
            'transaction_hash': self.transaction_hash,
            'verified': self.verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PoolStats(db.Model):
    __tablename__ = 'pool_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    total_contributors = db.Column(db.Integer, default=0)
    verified_contributors = db.Column(db.Integer, default=0)
    total_sol_contributed = db.Column(db.Float, default=0.0)
    total_sol_locked = db.Column(db.Float, default=0.0)
    total_teos_distributed = db.Column(db.Float, default=0.0)
    trading_unlocked = db.Column(db.Boolean, default=False)
    sol_unlocked = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'total_contributors': self.total_contributors,
            'verified_contributors': self.verified_contributors,
            'total_sol_contributed': self.total_sol_contributed,
            'total_sol_locked': self.total_sol_locked,
            'total_teos_distributed': self.total_teos_distributed,
            'trading_unlocked': self.trading_unlocked,
            'sol_unlocked': self.sol_unlocked,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Holder(db.Model):
    __tablename__ = 'holders'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(44), nullable=False, unique=True)
    teos_balance = db.Column(db.Float, nullable=False, default=0.0)
    verified = db.Column(db.Boolean, default=False)
    verification_method = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'teos_balance': self.teos_balance,
            'verified': self.verified,
            'verification_method': self.verification_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

