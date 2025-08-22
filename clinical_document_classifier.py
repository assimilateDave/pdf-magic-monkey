"""
Clinical Document Classifier using medSpaCy for Document Classification and Entity Extraction

This module provides clinical document classification and entity extraction capabilities
specifically designed for medical documents after OCR processing.

Document types supported:
- referral: Referral letters and requests
- order: Medical orders, prescriptions, lab orders
- progress_note: Progress notes, clinical notes
- correspondence: Letters, communications
- other: Other document types

The classifier uses medSpaCy's clinical NLP pipeline combined with scikit-learn
for document classification, and provides clinical entity extraction.
"""

import os
import pickle
import json
from typing import List, Dict, Tuple, Optional
import spacy
import medspacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np


class ClinicalDocumentClassifier:
    """
    Clinical document classifier using medSpaCy and scikit-learn.
    
    Features:
    - Document type classification (referral, order, progress_note, correspondence, other)
    - Clinical entity extraction using medSpaCy
    - Trainable model with user-provided examples
    - Persistent model storage
    """
    
    def __init__(self, model_path: str = "clinical_classifier_model.pkl"):
        """
        Initialize the clinical document classifier.
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        self.nlp = None
        self.classifier = None
        self.document_types = ["referral", "order", "progress_note", "correspondence", "other"]
        
        # Initialize medSpaCy pipeline
        self._init_medspacy_pipeline()
        
        # Try to load existing model
        self._load_model()
    
    def _init_medspacy_pipeline(self):
        """Initialize the medSpaCy clinical NLP pipeline."""
        try:
            # Load base spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: en_core_web_sm not found. Installing...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Add basic medSpaCy components (avoiding problematic ones)
        try:
            # Add context detection (helps with negation, etc.)
            self.nlp.add_pipe("medspacy_context")
            
            # Add target matcher for clinical concepts
            self.nlp.add_pipe("medspacy_target_matcher")
                
        except Exception as e:
            print(f"Warning: Some medSpaCy components not available: {e}")
            print("Basic clinical processing will still work.")
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract clinical entities from text using medSpaCy.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary containing extracted entities by category
        """
        if not self.nlp:
            return {"clinical_entities": []}
        
        try:
            doc = self.nlp(text)
            
            entities = {
                "clinical_entities": [],
                "medications": [],
                "conditions": [],
                "procedures": [],
                "anatomy": [],
                "general_entities": []
            }
            
            for ent in doc.ents:
                entity_info = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": getattr(ent, 'confidence', None)
                }
                
                # Categorize entities
                if ent.label_ in ["MEDICATION", "DRUG"]:
                    entities["medications"].append(entity_info)
                elif ent.label_ in ["CONDITION", "DISEASE", "SYMPTOM"]:
                    entities["conditions"].append(entity_info)
                elif ent.label_ in ["PROCEDURE", "TREATMENT"]:
                    entities["procedures"].append(entity_info)
                elif ent.label_ in ["ANATOMY", "BODY_PART"]:
                    entities["anatomy"].append(entity_info)
                else:
                    entities["general_entities"].append(entity_info)
                
                # Also add to clinical entities list
                entities["clinical_entities"].append(entity_info)
            
            return entities
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {"clinical_entities": [], "medications": [], "conditions": [], "procedures": [], "anatomy": [], "general_entities": []}
    
    def train(self, training_data: List[Tuple[str, str]]) -> Dict:
        """
        Train the document classifier with provided training data.
        
        Args:
            training_data: List of tuples (text, document_type)
            
        Returns:
            Training metrics and information
        """
        if len(training_data) < 2:
            raise ValueError("Need at least 2 training examples")
        
        # Separate texts and labels
        texts, labels = zip(*training_data)
        
        # Create classification pipeline
        self.classifier = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Split data for evaluation if we have enough samples
        if len(training_data) >= 10:
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    texts, labels, test_size=0.2, random_state=42, stratify=labels
                )
            except ValueError:
                # Fallback if stratify fails (not enough samples per class)
                X_train, X_test, y_train, y_test = train_test_split(
                    texts, labels, test_size=0.2, random_state=42
                )
        else:
            # Use all data for training if we have limited samples
            X_train, y_train = texts, labels
            X_test, y_test = texts, labels
        
        # Train the model
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test)
        
        # Calculate metrics
        metrics = {
            "accuracy": np.mean(y_pred == y_test),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "training_samples": len(training_data),
            "document_types": list(set(labels))
        }
        
        # Save the model
        self._save_model()
        
        return metrics
    
    def predict(self, text: str) -> Dict:
        """
        Predict document type and extract entities from text.
        
        Args:
            text: Input text to classify and analyze
            
        Returns:
            Dictionary with document_type, confidence, and extracted_entities
        """
        result = {
            "document_type": "other",
            "confidence": 0.0,
            "extracted_entities": {}
        }
        
        # Extract entities
        result["extracted_entities"] = self.extract_entities(text)
        
        # Classify document type
        if self.classifier:
            try:
                prediction = self.classifier.predict([text])[0]
                probabilities = self.classifier.predict_proba([text])[0]
                confidence = max(probabilities)
                
                result["document_type"] = prediction
                result["confidence"] = float(confidence)
                
            except Exception as e:
                print(f"Error during prediction: {e}")
                result["document_type"] = self._fallback_classify(text)
        else:
            # Fallback to rule-based classification
            result["document_type"] = self._fallback_classify(text)
        
        return result
    
    def _fallback_classify(self, text: str) -> str:
        """
        Fallback classification using keyword matching when ML model is not available.
        
        Args:
            text: Input text to classify
            
        Returns:
            Predicted document type
        """
        text_lower = text.lower()
        
        # Clinical document type keywords
        if any(word in text_lower for word in ["referral", "refer", "consultation request", "please see"]):
            return "referral"
        elif any(word in text_lower for word in ["order", "prescription", "rx", "lab order", "imaging order", "prescribe"]):
            return "order"
        elif any(word in text_lower for word in ["progress note", "clinical note", "assessment", "plan", "soap", "subjective", "objective"]):
            return "progress_note"
        elif any(word in text_lower for word in ["letter", "correspondence", "dear", "sincerely", "regards"]):
            return "correspondence"
        else:
            return "other"
    
    def _save_model(self):
        """Save the trained model to disk."""
        if self.classifier:
            try:
                with open(self.model_path, 'wb') as f:
                    pickle.dump(self.classifier, f)
                print(f"Model saved to {self.model_path}")
            except Exception as e:
                print(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load existing model from disk."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.classifier = pickle.load(f)
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
    
    def get_training_data_template(self) -> List[Tuple[str, str]]:
        """
        Get template training data for clinical documents.
        
        Returns:
            List of example training data tuples
        """
        return [
            # Referral examples
            ("Patient John Doe is referred to cardiology for evaluation of chest pain and abnormal EKG findings. Please evaluate and provide recommendations for further management.", "referral"),
            ("Referral to orthopedic surgery for evaluation of left knee pain. Patient reports chronic pain following previous injury. Please assess for surgical intervention.", "referral"),
            
            # Order examples  
            ("Order: CBC with differential, comprehensive metabolic panel, lipid panel. Patient fasting required. Schedule for tomorrow morning.", "order"),
            ("Prescription: Metformin 500mg twice daily with meals. Dispense 60 tablets with 5 refills. Patient counseled on side effects.", "order"),
            
            # Progress note examples
            ("Progress Note - Patient continues to improve post-operatively. Vital signs stable. Pain well controlled. Plan to discharge tomorrow if continues to progress.", "progress_note"),
            ("SOAP Note: S: Patient reports decreased pain since last visit. O: Wound healing well, no signs of infection. A: Post-surgical recovery on track. P: Continue current medications.", "progress_note"),
            
            # Correspondence examples
            ("Dear Dr. Smith, Thank you for the referral of Mrs. Johnson. I have completed my evaluation and my recommendations are attached. Please let me know if you have any questions. Sincerely, Dr. Brown", "correspondence"),
            ("Letter to patient: Your recent lab results are within normal limits. Please continue your current medications and schedule follow-up in 3 months.", "correspondence"),
            
            # Other examples
            ("Insurance verification form - Patient demographics and coverage information for processing claims.", "other"),
            ("Appointment reminder: Your appointment with Dr. Jones is scheduled for next Tuesday at 2 PM. Please arrive 15 minutes early.", "other")
        ]


def install_spacy_model():
    """Install required spaCy model if not present."""
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        print("Installing required spaCy model...")
        os.system("python -m spacy download en_core_web_sm")


if __name__ == "__main__":
    # Example usage
    install_spacy_model()
    
    classifier = ClinicalDocumentClassifier()
    
    # Get template training data
    training_data = classifier.get_training_data_template()
    
    # Train the model
    print("Training classifier with template data...")
    metrics = classifier.train(training_data)
    print(f"Training completed. Accuracy: {metrics['accuracy']:.2f}")
    
    # Test prediction
    test_text = "Patient referred to cardiology for evaluation of chest pain and shortness of breath."
    result = classifier.predict(test_text)
    print(f"\nTest prediction:")
    print(f"Document type: {result['document_type']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Entities found: {len(result['extracted_entities']['clinical_entities'])}")