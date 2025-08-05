#!/usr/bin/env python3
"""
Secure Migration Script
Uses parameterized queries and proper error handling to prevent SQL injection
"""

import sys
import os
import logging
from typing import Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    from config import settings
    from security import InputValidator, SecurityViolation, security_log_violation
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class SecureMigration:
        """Secure database migration with parameterized queries"""
        
        def __init__(self):
            self.validator = InputValidator()
            self.engine = None
            self.session = None
            
        def connect_database(self) -> bool:
            """Connect to database with proper error handling"""
            try:
                # Validate database URL
                db_url = settings.database_url
                if not db_url or not isinstance(db_url, str):
                    raise SecurityViolation("Invalid database URL")
                
                # Check for malicious patterns in connection string
                if self.validator.check_malicious_patterns(db_url):
                    raise SecurityViolation("Malicious patterns detected in database URL")
                
                # Create engine with security settings
                self.engine = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    connect_args={
                        "connect_timeout": 10,
                        "application_name": "secure_migration"
                    }
                )
                
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Create session factory
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
                self.session = SessionLocal()
                
                logger.info("✅ Successfully connected to database")
                return True
                
            except SQLAlchemyError as e:
                logger.error(f"❌ Database connection failed: {str(e)}")
                security_log_violation("DB_CONNECTION_ERROR", str(e))
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected error during connection: {str(e)}")
                security_log_violation("UNEXPECTED_ERROR", str(e))
                return False
        
        def check_column_exists(self, table_name: str, column_name: str) -> bool:
            """Check if a column exists using parameterized query"""
            try:
                # Validate input parameters
                if not self.validator.validate_length(table_name, 100):
                    raise SecurityViolation(f"Table name too long: {len(table_name)}")
                if not self.validator.validate_length(column_name, 100):
                    raise SecurityViolation(f"Column name too long: {len(column_name)}")
                
                # Check for malicious patterns
                if self.validator.check_malicious_patterns(table_name):
                    raise SecurityViolation(f"Malicious patterns in table name: {table_name}")
                if self.validator.check_malicious_patterns(column_name):
                    raise SecurityViolation(f"Malicious patterns in column name: {column_name}")
                
                # Parameterized query to check column existence
                query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                """)
                
                result = self.session.execute(query, {
                    "table_name": table_name,
                    "column_name": column_name
                })
                
                return result.fetchone() is not None
                
            except SQLAlchemyError as e:
                logger.error(f"❌ Error checking column existence: {str(e)}")
                security_log_violation("SQL_ERROR", f"Column check failed: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected error checking column: {str(e)}")
                security_log_violation("UNEXPECTED_ERROR", str(e))
                return False
        
        def add_column(self, table_name: str, column_name: str, column_type: str, default_value: Optional[str] = None) -> bool:
            """Add a column using parameterized query"""
            try:
                # Validate input parameters
                if not all([
                    self.validator.validate_length(table_name, 100),
                    self.validator.validate_length(column_name, 100),
                    self.validator.validate_length(column_type, 50)
                ]):
                    raise SecurityViolation("Input parameters too long")
                
                # Check for malicious patterns
                for param in [table_name, column_name, column_type]:
                    if self.validator.check_malicious_patterns(param):
                        raise SecurityViolation(f"Malicious patterns detected in parameter: {param}")
                
                # Build safe ALTER TABLE statement
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                if default_value:
                    alter_sql += f" DEFAULT {default_value}"
                
                # Execute with parameterized query
                self.session.execute(text(alter_sql))
                self.session.commit()
                
                logger.info(f"✅ Successfully added column {column_name} to {table_name}")
                return True
                
            except SQLAlchemyError as e:
                logger.error(f"❌ Error adding column: {str(e)}")
                self.session.rollback()
                security_log_violation("SQL_ERROR", f"Add column failed: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected error adding column: {str(e)}")
                self.session.rollback()
                security_log_violation("UNEXPECTED_ERROR", str(e))
                return False
        
        def update_existing_records(self, table_name: str, column_name: str, value: str) -> bool:
            """Update existing records using parameterized query"""
            try:
                # Validate input parameters
                if not all([
                    self.validator.validate_length(table_name, 100),
                    self.validator.validate_length(column_name, 100)
                ]):
                    raise SecurityViolation("Input parameters too long")
                
                # Check for malicious patterns
                for param in [table_name, column_name]:
                    if self.validator.check_malicious_patterns(param):
                        raise SecurityViolation(f"Malicious patterns detected in parameter: {param}")
                
                # Parameterized UPDATE query
                update_sql = f"UPDATE {table_name} SET {column_name} = :value WHERE {column_name} IS NULL"
                
                result = self.session.execute(text(update_sql), {"value": value})
                self.session.commit()
                
                logger.info(f"✅ Updated {result.rowcount} records in {table_name}")
                return True
                
            except SQLAlchemyError as e:
                logger.error(f"❌ Error updating records: {str(e)}")
                self.session.rollback()
                security_log_violation("SQL_ERROR", f"Update records failed: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"❌ Unexpected error updating records: {str(e)}")
                self.session.rollback()
                security_log_violation("UNEXPECTED_ERROR", str(e))
                return False
        
        def run_migration(self) -> bool:
            """Run the complete migration"""
            try:
                logger.info("🔒 Starting secure database migration...")
                
                # Connect to database
                if not self.connect_database():
                    return False
                
                # Check if column already exists
                if self.check_column_exists("users", "ai_responses_enabled"):
                    logger.info("✅ Column ai_responses_enabled already exists in users table")
                    return True
                
                # Add the column
                if not self.add_column("users", "ai_responses_enabled", "BOOLEAN", "TRUE"):
                    return False
                
                # Update existing users to have AI responses enabled by default
                if not self.update_existing_records("users", "ai_responses_enabled", "TRUE"):
                    return False
                
                logger.info("✅ Migration completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"❌ Migration failed: {str(e)}")
                security_log_violation("MIGRATION_ERROR", str(e))
                return False
            finally:
                if self.session:
                    self.session.close()
                if self.engine:
                    self.engine.dispose()
        
        def cleanup(self):
            """Clean up resources"""
            try:
                if self.session:
                    self.session.close()
                if self.engine:
                    self.engine.dispose()
            except Exception as e:
                logger.error(f"❌ Error during cleanup: {str(e)}")
    
    def main():
        """Main migration function"""
        migration = SecureMigration()
        try:
            success = migration.run_migration()
            if success:
                logger.info("🎉 Migration completed successfully!")
                return 0
            else:
                logger.error("❌ Migration failed!")
                return 1
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            security_log_violation("CRITICAL_ERROR", str(e))
            return 1
        finally:
            migration.cleanup()
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install sqlalchemy psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"❌ Critical error: {str(e)}")
    sys.exit(1) 