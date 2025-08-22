"""
medSpaCy Integration Example for PDF Magic Monkey

This script demonstrates how to integrate medSpaCy-powered clinical document
classification and entity extraction with the PDF Magic Monkey OCR pipeline.

INTEGRATION INSTRUCTIONS:
========================

1. INSTALLATION:
   - Run: pip install -r requirements.txt
   - This will install medspacy and scikit-learn
   - The system will automatically install the spaCy English model if needed

2. ADDING/UPDATING TRAINING EXAMPLES:
   - Edit the 'train_data' list below to add your clinical document examples
   - Each example should be a tuple: (text_content, document_type)
   - Document types: "referral", "order", "progress_note", "correspondence", "other"
   - Add diverse examples for better classification accuracy
   - Minimum 2 examples per document type recommended

3. TRAINING OR UPDATING THE MODEL:
   - Run this script: python example_medspacy_integration.py
   - The model will be trained on your data and saved as 'clinical_classifier_model.pkl'
   - Training metrics will be displayed
   - Re-run anytime you add new training examples

4. USING THE MODEL IN THE PIPELINE:
   - The model integrates automatically with processor.py after OCR
   - It replaces the basic keyword-based classification
   - Provides both document classification and entity extraction
   - Results are stored in the database

5. DATABASE RESULTS:
   - document_type: Predicted document type (referral, order, progress_note, correspondence, other)
   - extracted_entities: JSON string containing clinical entities found in the document
   - Use the database migration SQL to add the extracted_entities column if needed

WORKFLOW INTEGRATION:
====================
OCR Text Extraction → medSpaCy Classification & Entity Extraction → Database Storage

The integration occurs in processor.py after OCR text extraction and before database storage.
"""

from clinical_document_classifier import ClinicalDocumentClassifier, install_spacy_model
import json

# TRAINING DATA - CUSTOMIZE THIS SECTION
# =====================================
# Add your own clinical document examples here.
# Each tuple contains (document_text, document_type)
# Document types: "referral", "order", "progress_note", "correspondence", "other"

train_data = [
    # REFERRAL EXAMPLES - Add more examples of referral documents
    (
        "Patient John Doe, DOB 01/15/1975, is referred to cardiology for evaluation of chest pain and abnormal EKG findings showing ST depression in leads II, III, aVF. Patient reports substernal chest pressure with exertion lasting 10-15 minutes, relieved by rest. No radiation to arms or jaw. Please evaluate for coronary artery disease and provide recommendations for further management including stress testing if appropriate.",
        "referral"
    ),
    (
        "Referral to orthopedic surgery for evaluation of left knee pain. Patient Susan Smith reports chronic pain and stiffness following motor vehicle accident 6 months ago. MRI shows torn meniscus and possible ligament damage. Conservative treatment with physical therapy has not provided adequate relief. Please assess for surgical intervention and provide treatment recommendations.",
        "referral"
    ),
    (
        "Please see this 45-year-old male for evaluation of chronic back pain. Patient has failed conservative management including physical therapy and NSAIDs. MRI shows disc herniation at L4-L5 with nerve root compression. Requesting consultation for possible surgical intervention.",
        "referral"
    ),
    
    # ORDER EXAMPLES - Add more examples of medical orders, prescriptions, lab orders
    (
        "Laboratory Order: CBC with differential, comprehensive metabolic panel, lipid panel, HbA1c, thyroid function tests. Patient fasting required for 12 hours. Schedule for tomorrow morning at 0800. Results needed before next appointment on Friday.",
        "order"
    ),
    (
        "Prescription Order: Metformin 500mg tablet, take twice daily with meals. Dispense 60 tablets with 5 refills. Patient counseled on potential gastrointestinal side effects and need for regular monitoring. Check kidney function in 3 months.",
        "order"
    ),
    (
        "Imaging Order: MRI of lumbar spine without contrast. Clinical indication: chronic low back pain with radiculopathy. Rule out disc herniation or spinal stenosis. Schedule within 2 weeks. Prior authorization may be required.",
        "order"
    ),
    (
        "Physical Therapy Order: Evaluate and treat for right shoulder impingement syndrome. Focus on range of motion, strengthening, and functional activities. 2-3 times per week for 6 weeks. Patient may weight bear as tolerated.",
        "order"
    ),
    
    # PROGRESS NOTE EXAMPLES - Add more clinical notes, SOAP notes, assessments
    (
        "Progress Note - Post-operative day 2 following laparoscopic cholecystectomy. Patient continues to improve. Vital signs stable: BP 120/80, HR 72, T 98.6°F. Pain well controlled with oral medications, rating 3/10. Incision sites clean and dry with no signs of infection. Tolerating regular diet. Plan to discharge tomorrow if continues to progress well. Follow-up in clinic in 1 week.",
        "progress_note"
    ),
    (
        "SOAP Note: S: Patient reports decreased pain since last visit, now 4/10 from previous 8/10. Sleep improved. O: Wound healing well, no erythema or drainage. Range of motion improved. A: Post-surgical recovery progressing as expected. P: Continue current pain medications, start physical therapy next week, follow-up in 2 weeks.",
        "progress_note"
    ),
    (
        "Clinical Assessment: 55-year-old diabetic patient for routine follow-up. Blood glucose logs show good control with average readings 110-140 mg/dL. No symptoms of hypoglycemia or hyperglycemia. Physical exam normal. HbA1c 7.2%, slight improvement from last visit. Plan: continue current metformin dose, recheck labs in 3 months.",
        "progress_note"
    ),
    (
        "Hospital Progress Note: Day 3 of admission for pneumonia. Patient showing clinical improvement with decreased fever and improved oxygen saturation. Chest X-ray shows resolving infiltrate. White count trending down. Tolerating oral antibiotics well. Plan for discharge tomorrow with oral antibiotic course.",
        "progress_note"
    ),
    
    # CORRESPONDENCE EXAMPLES - Add more letters, communications between providers
    (
        "Dear Dr. Smith, Thank you for the referral of Mrs. Johnson for evaluation of her cardiac symptoms. I have completed my cardiovascular assessment and my recommendations are as follows: 1) Continue current cardiac medications, 2) Schedule stress test within 2 weeks, 3) Consider cardiac catheterization if stress test abnormal. I will see her again in 4 weeks to review results. Please let me know if you have any questions. Sincerely, Dr. Brown, Cardiology",
        "correspondence"
    ),
    (
        "Letter to patient: Dear Mr. Davis, Your recent laboratory results are within normal limits. Your cholesterol has improved significantly since starting the statin medication. Please continue your current medications as prescribed and schedule a follow-up appointment in 3 months. If you have any questions or concerns before then, please don't hesitate to call our office.",
        "correspondence"
    ),
    (
        "Consultation Report: Thank you for referring this pleasant 62-year-old gentleman for evaluation of chronic kidney disease. Based on my examination and review of laboratory studies, I recommend the following management plan. I have discussed these recommendations with the patient and he agrees with the proposed treatment approach.",
        "correspondence"
    ),
    
    # OTHER EXAMPLES - Add more administrative documents, forms, etc.
    (
        "Insurance Pre-Authorization Form - Patient demographics and coverage information for processing prior authorization request for MRI imaging. Member ID: 123456789. Procedure code: 72148. Clinical indication: chronic low back pain with radiculopathy.",
        "other"
    ),
    (
        "Appointment Reminder: Your appointment with Dr. Jones is scheduled for next Tuesday, March 15th at 2:00 PM in the Cardiology Clinic. Please arrive 15 minutes early for check-in. Bring your insurance card and a list of current medications. Call if you need to reschedule.",
        "other"
    ),
    (
        "Medical Records Release Form: Authorization to release medical records for patient Jane Doe, DOB 05/20/1980. Records to be sent to Dr. Wilson at ABC Medical Center. Patient signature and date required for processing.",
        "other"
    )
]

def train_clinical_classifier():
    """
    Train the clinical document classifier with the provided training data.
    """
    print("=" * 60)
    print("MEDSPACY CLINICAL DOCUMENT CLASSIFIER TRAINING")
    print("=" * 60)
    
    # Install required spaCy model
    print("Checking spaCy model installation...")
    install_spacy_model()
    
    # Initialize classifier
    print("Initializing clinical document classifier...")
    classifier = ClinicalDocumentClassifier()
    
    # Display training data summary
    print(f"\nTraining Data Summary:")
    print(f"Total examples: {len(train_data)}")
    
    # Count examples by type
    type_counts = {}
    for text, doc_type in train_data:
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    for doc_type, count in type_counts.items():
        print(f"  {doc_type}: {count} examples")
    
    # Train the model
    print(f"\nTraining classifier...")
    try:
        metrics = classifier.train(train_data)
        
        print(f"\n" + "=" * 40)
        print("TRAINING RESULTS")
        print("=" * 40)
        print(f"Accuracy: {metrics['accuracy']:.3f}")
        print(f"Training samples: {metrics['training_samples']}")
        print(f"Document types: {', '.join(metrics['document_types'])}")
        
        # Display detailed classification report
        if 'classification_report' in metrics:
            print(f"\nDetailed Classification Report:")
            report = metrics['classification_report']
            for doc_type in report:
                if isinstance(report[doc_type], dict) and 'precision' in report[doc_type]:
                    print(f"  {doc_type}:")
                    print(f"    Precision: {report[doc_type]['precision']:.3f}")
                    print(f"    Recall: {report[doc_type]['recall']:.3f}")
                    print(f"    F1-score: {report[doc_type]['f1-score']:.3f}")
        
        print(f"\nModel saved successfully!")
        return True
        
    except Exception as e:
        print(f"Error during training: {e}")
        return False

def test_classification_examples():
    """
    Test the trained classifier with example documents.
    """
    print(f"\n" + "=" * 40)
    print("TESTING CLASSIFICATION")
    print("=" * 40)
    
    classifier = ClinicalDocumentClassifier()
    
    test_examples = [
        "Patient referred to neurology for evaluation of chronic headaches and possible migraine. Please assess and provide treatment recommendations.",
        "Order CBC, CMP, lipid panel. Patient NPO after midnight for morning draw.",
        "Progress note: Patient tolerating chemotherapy well. Nausea controlled with ondansetron. Next cycle scheduled in 3 weeks.",
        "Dear colleague, thank you for the consultation on this complex case. I agree with your assessment and recommendations.",
        "Appointment confirmation for John Smith on Friday at 10 AM in clinic room 3."
    ]
    
    for i, text in enumerate(test_examples, 1):
        print(f"\nTest {i}: {text[:80]}...")
        result = classifier.predict(text)
        print(f"  Predicted type: {result['document_type']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Clinical entities found: {len(result['extracted_entities']['clinical_entities'])}")
        
        # Show some entities if found
        entities = result['extracted_entities']['clinical_entities']
        if entities:
            print(f"  Sample entities: {[ent['text'] for ent in entities[:3]]}")

def integration_status():
    """
    Check integration status with the main pipeline.
    """
    print(f"\n" + "=" * 40)
    print("INTEGRATION STATUS")
    print("=" * 40)
    
    # Check if model file exists
    import os
    model_exists = os.path.exists("clinical_classifier_model.pkl")
    print(f"Trained model available: {'✓ Yes' if model_exists else '✗ No - run training first'}")
    
    # Check database schema
    try:
        import database
        conn = database.init_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        has_extracted_entities = 'extracted_entities' in columns
        print(f"Database schema updated: {'✓ Yes' if has_extracted_entities else '✗ No - run database migration'}")
        
        if not has_extracted_entities:
            print("  Run: ALTER TABLE documents ADD COLUMN extracted_entities TEXT;")
    
    except Exception as e:
        print(f"Database check failed: {e}")
    
    print(f"\nTo integrate with your pipeline:")
    print(f"1. Ensure the model is trained (run this script)")
    print(f"2. Update your processor.py to use ClinicalDocumentClassifier")
    print(f"3. Update database schema with extracted_entities column")

if __name__ == "__main__":
    print("PDF Magic Monkey - medSpaCy Integration")
    print("Run this script to train your clinical document classifier\n")
    
    # Train the classifier
    success = train_clinical_classifier()
    
    if success:
        # Test the classifier
        test_classification_examples()
        
        # Show integration status
        integration_status()
        
        print(f"\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Review the training results above")
        print("2. Add more training examples if needed (edit train_data in this file)")
        print("3. Run the database migration SQL (see database_migration.sql)")
        print("4. The classifier is now ready for integration with your OCR pipeline")
        print("5. Document classification and entity extraction will occur automatically")
        
        # Show how to use results
        print(f"\nHOW TO USE RESULTS IN YOUR DATABASE:")
        print("- document_type field will contain: referral, order, progress_note, correspondence, or other")
        print("- extracted_entities field will contain JSON with clinical entities")
        print("- Query examples:")
        print("  SELECT * FROM documents WHERE document_type = 'referral';")
        print("  SELECT * FROM documents WHERE extracted_entities LIKE '%medication%';")
        
    else:
        print("Training failed. Please check the error messages above.")
        print("Make sure you have:")
        print("1. Installed all requirements: pip install -r requirements.txt")
        print("2. Added proper training examples in the train_data list")
        print("3. At least 2 examples per document type")