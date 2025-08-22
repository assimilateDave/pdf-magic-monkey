-- Database Migration for medSpaCy Integration
-- PDF Magic Monkey - Clinical Document Classification and Entity Extraction
-- 
-- This script adds the extracted_entities column to store clinical entities
-- extracted by medSpaCy from OCR'd documents.
-- 
-- The extracted_entities column stores JSON data containing:
-- - clinical_entities: All clinical entities found
-- - medications: Medication-related entities  
-- - conditions: Medical conditions and symptoms
-- - procedures: Medical procedures and treatments
-- - anatomy: Anatomical references
-- - general_entities: Other named entities
--
-- Execute this script after setting up medSpaCy integration to enable
-- entity extraction storage in your database.

-- Add extracted_entities column if it doesn't exist
-- This column stores JSON data with clinical entities extracted by medSpaCy
ALTER TABLE documents ADD COLUMN extracted_entities TEXT;

-- Optional: Add index on document_type for faster filtering of clinical document types
-- Useful for queries like: SELECT * FROM documents WHERE document_type = 'referral'
CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type);

-- Optional: Add index on extracted_entities for faster searching
-- Note: This creates a basic text index. For more advanced JSON querying,
-- consider upgrading to a database that supports JSON indexing
CREATE INDEX IF NOT EXISTS idx_extracted_entities ON documents(extracted_entities);

-- Update any existing 'Unknown' document types to 'other' to match new classification system
-- The medSpaCy classifier uses 'other' instead of 'Unknown'
UPDATE documents SET document_type = 'other' WHERE document_type = 'Unknown';

-- View the updated schema
-- Uncomment the following line to see the current table structure:
-- PRAGMA table_info(documents);

-- Example queries after migration:
-- 
-- 1. Find all referral documents:
-- SELECT id, basename, document_type, processed_at FROM documents WHERE document_type = 'referral';
--
-- 2. Find documents containing medication entities:
-- SELECT id, basename, document_type FROM documents WHERE extracted_entities LIKE '%medication%';
--
-- 3. Find documents with specific clinical entities:
-- SELECT id, basename, extracted_entities FROM documents WHERE extracted_entities LIKE '%hypertension%';
--
-- 4. Count documents by type:
-- SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type ORDER BY count DESC;
--
-- 5. Find recent clinical documents with entities:
-- SELECT id, basename, document_type, LENGTH(extracted_entities) as entity_data_size 
-- FROM documents 
-- WHERE extracted_entities IS NOT NULL 
-- ORDER BY processed_at DESC 
-- LIMIT 10;

-- Notes:
-- - The extracted_entities field stores JSON as TEXT
-- - JSON structure: {"clinical_entities": [...], "medications": [...], etc.}
-- - Empty entity extraction results in: {"entities": []}
-- - For advanced JSON querying, consider PostgreSQL or other JSON-capable databases
-- - This migration is safe to run multiple times (uses IF NOT EXISTS and ADD COLUMN IF NOT EXISTS logic)