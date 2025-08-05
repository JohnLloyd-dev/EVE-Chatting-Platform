#!/bin/bash

echo "🔄 Updating System Prompts table structure..."

# Run the migration inside the backend container
docker-compose exec backend python -c "
import sys
sys.path.append('/app')

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
        existing_prompts = conn.execute(text('SELECT id, prompt_text FROM system_prompts WHERE prompt_text IS NOT NULL')).fetchall()
        
        for prompt_id, prompt_text in existing_prompts:
            if prompt_text:
                # Split the existing prompt into head and rule parts
                # For now, put everything in head_prompt
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
        
        # Drop old column if it exists
        try:
            conn.execute(text('ALTER TABLE system_prompts DROP COLUMN IF EXISTS prompt_text'))
            print('Dropped old prompt_text column')
        except:
            pass
        
        conn.commit()
        print('✅ System prompts table updated successfully!')

run_migration()
"

echo "✅ Migration completed!"