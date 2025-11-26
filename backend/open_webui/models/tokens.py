"""
Token models for email verification and password reset
"""

import logging
import time
import uuid
import secrets
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, BigInteger
from open_webui.internal.db import Base, get_db

log = logging.getLogger(__name__)

####################
# DB MODELS
####################


class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    token = Column(String, unique=True)
    expires_at = Column(BigInteger)
    created_at = Column(BigInteger)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    token = Column(String, unique=True)
    expires_at = Column(BigInteger)
    created_at = Column(BigInteger)
    used = Column(Boolean, default=False)


class VerificationTokenModel(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: int
    created_at: int


class PasswordResetTokenModel(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: int
    created_at: int
    used: bool


####################
# TOKEN OPERATIONS
####################


class VerificationTokensTable:
    
    def create_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """Create a new verification token for user"""
        with get_db() as db:
            token = secrets.token_urlsafe(32)
            expires_at = int(time.time()) + (expires_in_hours * 3600)
            
            # Delete any existing tokens for this user
            db.query(VerificationToken).filter_by(user_id=user_id).delete()
            
            # Create new token
            verification = VerificationToken(
                id=str(uuid.uuid4()),
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                created_at=int(time.time())
            )
            db.add(verification)
            db.commit()
            
            log.info(f"Created verification token for user {user_id}")
            return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify a token and return user_id if valid
        Deletes token after successful verification
        """
        with get_db() as db:
            verification = db.query(VerificationToken).filter_by(token=token).first()
            
            if not verification:
                log.warning(f"Verification token not found: {token[:10]}...")
                return None
            
            # Check if expired
            if int(time.time()) > verification.expires_at:
                log.warning(f"Verification token expired for user {verification.user_id}")
                db.query(VerificationToken).filter_by(token=token).delete()
                db.commit()
                return None
            
            user_id = verification.user_id
            
            # Delete token after use
            db.query(VerificationToken).filter_by(token=token).delete()
            db.commit()
            
            log.info(f"Verification token verified for user {user_id}")
            return user_id
    
    def delete_tokens_by_user_id(self, user_id: str) -> bool:
        """Delete all verification tokens for a user"""
        try:
            with get_db() as db:
                db.query(VerificationToken).filter_by(user_id=user_id).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Error deleting verification tokens: {e}")
            return False


class PasswordResetTokensTable:
    
    def create_token(self, user_id: str, expires_in_hours: int = 1) -> str:
        """Create a new password reset token for user"""
        with get_db() as db:
            token = secrets.token_urlsafe(32)
            expires_at = int(time.time()) + (expires_in_hours * 3600)
            
            # Delete any existing unused tokens for this user
            db.query(PasswordResetToken).filter_by(user_id=user_id, used=False).delete()
            
            # Create new token
            reset = PasswordResetToken(
                id=str(uuid.uuid4()),
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                created_at=int(time.time()),
                used=False
            )
            db.add(reset)
            db.commit()
            
            log.info(f"Created password reset token for user {user_id}")
            return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify a token and return user_id if valid
        Marks token as used but doesn't delete (for audit trail)
        """
        with get_db() as db:
            reset = db.query(PasswordResetToken).filter_by(token=token).first()
            
            if not reset:
                log.warning(f"Reset token not found: {token[:10]}...")
                return None
            
            # Check if already used
            if reset.used:
                log.warning(f"Reset token already used for user {reset.user_id}")
                return None
            
            # Check if expired
            if int(time.time()) > reset.expires_at:
                log.warning(f"Reset token expired for user {reset.user_id}")
                return None
            
            user_id = reset.user_id
            
            # Mark as used
            db.query(PasswordResetToken).filter_by(token=token).update({"used": True})
            db.commit()
            
            log.info(f"Password reset token verified for user {user_id}")
            return user_id
    
    def delete_tokens_by_user_id(self, user_id: str) -> bool:
        """Delete all password reset tokens for a user"""
        try:
            with get_db() as db:
                db.query(PasswordResetToken).filter_by(user_id=user_id).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Error deleting reset tokens: {e}")
            return False


# Initialize tables
VerificationTokens = VerificationTokensTable()
PasswordResetTokens = PasswordResetTokensTable()