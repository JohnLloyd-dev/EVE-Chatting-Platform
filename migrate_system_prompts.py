#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/dev/Work/eve/backend')

from sqlalchemy import create_engine, text
from database import Base, SystemPrompt
from config import settings

def run_migration():
    print('🔄 Updating system_prompts table structure...')
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Check if columns exist
        result = conn.execute(text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'system_prompts' 
            AND column_name IN ('head_prompt', 'rule_prompt', 'user_id')
        ''')).fetchall()
        
        existing_columns = [row[0] for row in result]
        print(f"Existing columns: {existing_columns}")
        
        # Add new columns if they don't exist
        if 'head_prompt' not in existing_columns:
            print('Adding head_prompt column...')
            conn.execute(text('ALTER TABLE system_prompts ADD COLUMN head_prompt TEXT'))
        
        if 'rule_prompt' not in existing_columns:
            print('Adding rule_prompt column...')
            conn.execute(text('ALTER TABLE system_prompts ADD COLUMN rule_prompt TEXT'))
            
        if 'user_id' not in existing_columns:
            print('Adding user_id column...')
            conn.execute(text('ALTER TABLE system_prompts ADD COLUMN user_id UUID REFERENCES users(id)'))
        
        # Migrate existing data if prompt_text exists
        try:
            existing_prompts = conn.execute(text('SELECT id, prompt_text FROM system_prompts WHERE prompt_text IS NOT NULL')).fetchall()
            print(f"Found {len(existing_prompts)} existing prompts to migrate")
            
            for prompt_id, prompt_text in existing_prompts:
                if prompt_text:
                    # Split the existing prompt into head and rule parts
                    # For now, put everything in rule_prompt and add default head
                    conn.execute(text('''
                        UPDATE system_prompts 
                        SET head_prompt = :head_prompt,
                            rule_prompt = :rule_prompt
                        WHERE id = :id
                    '''), {
                        'id': prompt_id,
                        'head_prompt': 'You are a sexual fantasy assistant.',
                        'rule_prompt': prompt_text
                    })
                    print(f"Migrated prompt {prompt_id}")
        except Exception as e:
            print(f"Migration of existing data failed (this is OK if prompt_text doesn't exist): {e}")
        
        # Drop old column if it exists
        try:
            conn.execute(text('ALTER TABLE system_prompts DROP COLUMN IF EXISTS prompt_text'))
            print('Dropped old prompt_text column')
        except Exception as e:
            print(f"Could not drop prompt_text column (this is OK): {e}")
        
        conn.commit()
        print('✅ System prompts table updated successfully!')

if __name__ == "__main__":
    run_migration()