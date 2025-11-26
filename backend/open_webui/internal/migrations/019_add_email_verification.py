"""
019_add_email_verification.py

Adds email verification and password reset functionality
"""

def migrate(migrator, database, **kwargs):
    """Add email verification and password reset tables/columns"""
    
    # Use raw SQL to avoid circular imports
    migrator.sql('''
        ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
    ''')
    
    migrator.sql('''
        CREATE TABLE IF NOT EXISTS verification_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at BIGINT NOT NULL,
            created_at BIGINT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        );
    ''')
    
    migrator.sql('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at BIGINT NOT NULL,
            created_at BIGINT NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        );
    ''')
    
    # Set existing users as verified (grandfather clause)
    migrator.sql('''
        UPDATE user SET email_verified = TRUE WHERE email_verified IS NULL OR email_verified = FALSE;
    ''')


def rollback(migrator, database, **kwargs):
    """Rollback the migration"""
    
    migrator.sql('ALTER TABLE user DROP COLUMN email_verified;')
    migrator.sql('DROP TABLE IF EXISTS verification_tokens;')
    migrator.sql('DROP TABLE IF EXISTS password_reset_tokens;')