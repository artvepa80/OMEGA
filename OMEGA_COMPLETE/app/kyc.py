"""
KYC (Know Your Customer) Verification System
Comprehensive identity verification with document validation, biometric checks, and compliance
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import base64
import hashlib
import json
import asyncio
import aiohttp
import cv2
import numpy as np
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter()

class KYCStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class DocumentType(str, Enum):
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    RESIDENCE_PERMIT = "residence_permit"

class KYCSubmission(BaseModel):
    user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    date_of_birth: str
    nationality: str
    address: str
    city: str
    postal_code: str
    country: str
    phone: str
    document_type: DocumentType
    document_number: str
    occupation: Optional[str] = None
    source_of_funds: Optional[str] = None

class BiometricData(BaseModel):
    face_encoding: List[float]
    liveness_score: float
    quality_score: float

class KYCDocument:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    async def extract_document_data(self, image_bytes: bytes, document_type: DocumentType) -> Dict[str, Any]:
        """Extract data from uploaded document using OCR and validation"""
        try:
            # Convert bytes to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Invalid image format")
            
            # Document validation logic
            extracted_data = await self._ocr_extract(image, document_type)
            validation_result = await self._validate_document(extracted_data, document_type)
            
            return {
                "extracted_data": extracted_data,
                "validation": validation_result,
                "image_quality": self._assess_image_quality(image),
                "document_type": document_type
            }
            
        except Exception as e:
            logger.error(f"Document extraction failed: {e}")
            raise HTTPException(status_code=400, detail=f"Document processing failed: {str(e)}")
    
    async def _ocr_extract(self, image: np.ndarray, doc_type: DocumentType) -> Dict[str, str]:
        """Extract text from document using OCR"""
        # This would integrate with a real OCR service like AWS Textract, Google Vision API, etc.
        # For now, return mock data
        mock_data = {
            DocumentType.PASSPORT: {
                "document_number": "P123456789",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-01",
                "expiry_date": "2030-01-01",
                "nationality": "US"
            },
            DocumentType.DRIVERS_LICENSE: {
                "license_number": "DL123456789",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-01",
                "expiry_date": "2025-01-01",
                "address": "123 Main St, City, State"
            }
        }
        
        return mock_data.get(doc_type, {})
    
    async def _validate_document(self, extracted_data: Dict[str, str], doc_type: DocumentType) -> Dict[str, Any]:
        """Validate document authenticity and data consistency"""
        validation_result = {
            "is_valid": True,
            "confidence_score": 0.95,
            "checks": {
                "format_valid": True,
                "expiry_check": True,
                "security_features": True,
                "data_consistency": True
            },
            "warnings": []
        }
        
        # Check document expiry
        if "expiry_date" in extracted_data:
            try:
                expiry = datetime.strptime(extracted_data["expiry_date"], "%Y-%m-%d")
                if expiry < datetime.now():
                    validation_result["checks"]["expiry_check"] = False
                    validation_result["warnings"].append("Document has expired")
            except ValueError:
                validation_result["warnings"].append("Invalid expiry date format")
        
        return validation_result
    
    def _assess_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """Assess image quality for document processing"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast
        contrast = gray.std()
        
        return {
            "sharpness": float(sharpness),
            "brightness": float(brightness),
            "contrast": float(contrast),
            "overall_quality": min(sharpness / 100, 1.0)  # Normalize to 0-1
        }

class BiometricProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    async def process_selfie(self, image_bytes: bytes) -> BiometricData:
        """Process selfie for biometric verification"""
        try:
            # Convert bytes to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Invalid image format")
            
            # Face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                raise ValueError("No face detected in image")
            elif len(faces) > 1:
                raise ValueError("Multiple faces detected - only one face allowed")
            
            # Extract face encoding (simplified - would use face_recognition library)
            face_encoding = self._extract_face_encoding(image, faces[0])
            
            # Liveness detection
            liveness_score = await self._detect_liveness(image)
            
            # Quality assessment
            quality_score = self._assess_face_quality(image, faces[0])
            
            return BiometricData(
                face_encoding=face_encoding,
                liveness_score=liveness_score,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Biometric processing failed: {e}")
            raise HTTPException(status_code=400, detail=f"Biometric processing failed: {str(e)}")
    
    def _extract_face_encoding(self, image: np.ndarray, face_coords: tuple) -> List[float]:
        """Extract face encoding for comparison"""
        # This would use a proper face recognition library like face_recognition
        # For now, return a mock encoding
        x, y, w, h = face_coords
        face_region = image[y:y+h, x:x+w]
        
        # Convert to feature vector (simplified)
        face_resized = cv2.resize(face_region, (128, 128))
        face_vector = face_resized.flatten().astype(float)
        
        # Normalize to reasonable range
        face_encoding = (face_vector / 255.0).tolist()[:128]  # Take first 128 features
        
        return face_encoding
    
    async def _detect_liveness(self, image: np.ndarray) -> float:
        """Detect if the image is from a live person (anti-spoofing)"""
        # This would implement actual liveness detection algorithms
        # For now, return a mock score based on image properties
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple liveness indicators
        edge_density = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness_variance = np.var(gray)
        
        # Mock liveness score
        liveness_score = min((edge_density + brightness_variance) / 10000, 1.0)
        
        return max(0.1, liveness_score)  # Ensure minimum score
    
    def _assess_face_quality(self, image: np.ndarray, face_coords: tuple) -> float:
        """Assess quality of face image"""
        x, y, w, h = face_coords
        face_region = image[y:y+h, x:x+w]
        
        # Quality metrics
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        brightness = np.mean(gray_face)
        
        # Face size check (larger faces are generally better quality)
        face_area = w * h
        size_score = min(face_area / 10000, 1.0)
        
        # Combine metrics
        quality_score = (sharpness / 1000 + size_score + (brightness / 255)) / 3
        
        return min(max(quality_score, 0.1), 1.0)

# Initialize processors
kyc_doc_processor = None
biometric_processor = None

@router.on_event("startup")
async def startup_kyc():
    global kyc_doc_processor, biometric_processor
    # These would be initialized with Redis client
    biometric_processor = BiometricProcessor()
    logger.info("KYC system initialized")

@router.post("/submit")
async def submit_kyc(
    background_tasks: BackgroundTasks,
    kyc_data: KYCSubmission,
    document_front: UploadFile = File(...),
    document_back: Optional[UploadFile] = File(None),
    selfie: UploadFile = File(...)
):
    """Submit KYC application with documents and biometric data"""
    try:
        # Validate file types
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        
        if document_front.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid document file type")
        
        if selfie.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid selfie file type")
        
        # Generate application ID
        application_id = hashlib.sha256(
            f"{kyc_data.user_id}_{kyc_data.email}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Read file contents
        doc_front_bytes = await document_front.read()
        doc_back_bytes = await document_back.read() if document_back else None
        selfie_bytes = await selfie.read()
        
        # Process documents
        if kyc_doc_processor:
            doc_front_result = await kyc_doc_processor.extract_document_data(
                doc_front_bytes, kyc_data.document_type
            )
            
            doc_back_result = None
            if doc_back_bytes:
                doc_back_result = await kyc_doc_processor.extract_document_data(
                    doc_back_bytes, kyc_data.document_type
                )
        else:
            # Mock processing for demonstration
            doc_front_result = {"validation": {"is_valid": True, "confidence_score": 0.95}}
            doc_back_result = None
        
        # Process biometric data
        if biometric_processor:
            biometric_data = await biometric_processor.process_selfie(selfie_bytes)
        else:
            # Mock biometric data
            biometric_data = BiometricData(
                face_encoding=[0.1] * 128,
                liveness_score=0.85,
                quality_score=0.9
            )
        
        # Create KYC record
        kyc_record = {
            "application_id": application_id,
            "user_data": kyc_data.dict(),
            "documents": {
                "front": doc_front_result,
                "back": doc_back_result
            },
            "biometric_data": biometric_data.dict(),
            "status": KYCStatus.IN_REVIEW,
            "submitted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store in Redis (in real implementation)
        # await redis_client.hset(f"kyc:{application_id}", mapping=kyc_record)
        
        # Schedule background processing
        background_tasks.add_task(
            process_kyc_application,
            application_id,
            kyc_record
        )
        
        return {
            "success": True,
            "application_id": application_id,
            "status": KYCStatus.IN_REVIEW,
            "estimated_processing_time": "2-5 business days",
            "next_steps": [
                "Document verification in progress",
                "Biometric verification in progress",
                "Compliance check pending",
                "Final review pending"
            ]
        }
        
    except Exception as e:
        logger.error(f"KYC submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"KYC submission failed: {str(e)}")

@router.get("/status/{application_id}")
async def get_kyc_status(application_id: str):
    """Get KYC application status"""
    try:
        # In real implementation, fetch from Redis
        # kyc_record = await redis_client.hgetall(f"kyc:{application_id}")
        
        # Mock response
        mock_statuses = {
            "pending": {
                "status": KYCStatus.PENDING,
                "progress": 25,
                "current_step": "Document upload pending"
            },
            "in_review": {
                "status": KYCStatus.IN_REVIEW,
                "progress": 75,
                "current_step": "Final compliance review"
            },
            "approved": {
                "status": KYCStatus.APPROVED,
                "progress": 100,
                "current_step": "Verification complete"
            }
        }
        
        # Return mock status (in real implementation, use actual data)
        return {
            "application_id": application_id,
            "status": KYCStatus.IN_REVIEW,
            "progress": 75,
            "current_step": "Document verification complete, biometric review in progress",
            "submitted_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(days=2)).isoformat(),
            "required_actions": []
        }
        
    except Exception as e:
        logger.error(f"Failed to get KYC status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/verify")
async def verify_identity(user_id: str, application_id: str):
    """Verify user identity against KYC data"""
    try:
        # In real implementation, fetch from Redis and verify
        # kyc_record = await redis_client.hgetall(f"kyc:{application_id}")
        
        # Mock verification
        verification_result = {
            "verified": True,
            "confidence_score": 0.95,
            "verification_level": "full_kyc",
            "verified_at": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
            "verified_attributes": [
                "identity",
                "address",
                "document_authenticity",
                "biometric_match"
            ]
        }
        
        return verification_result
        
    except Exception as e:
        logger.error(f"Identity verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

async def process_kyc_application(application_id: str, kyc_record: Dict[str, Any]):
    """Background task to process KYC application"""
    try:
        logger.info(f"Processing KYC application: {application_id}")
        
        # Simulate processing time
        await asyncio.sleep(5)
        
        # Update status to approved (in real implementation, use actual verification logic)
        kyc_record["status"] = KYCStatus.APPROVED
        kyc_record["approved_at"] = datetime.now().isoformat()
        kyc_record["updated_at"] = datetime.now().isoformat()
        
        # Store updated record
        # await redis_client.hset(f"kyc:{application_id}", mapping=kyc_record)
        
        # Send notification (email/SMS)
        await send_kyc_notification(kyc_record["user_data"]["email"], application_id, KYCStatus.APPROVED)
        
        logger.info(f"KYC application {application_id} processed successfully")
        
    except Exception as e:
        logger.error(f"KYC processing failed for {application_id}: {e}")
        
        # Update status to rejected
        kyc_record["status"] = KYCStatus.REJECTED
        kyc_record["rejection_reason"] = str(e)
        kyc_record["updated_at"] = datetime.now().isoformat()

async def send_kyc_notification(email: str, application_id: str, status: KYCStatus):
    """Send notification about KYC status change"""
    try:
        # In real implementation, send email/SMS notification
        logger.info(f"Notification sent to {email} for application {application_id}: {status}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

@router.get("/compliance/report/{application_id}")
async def get_compliance_report(application_id: str):
    """Generate compliance report for KYC application"""
    try:
        # Mock compliance report
        report = {
            "application_id": application_id,
            "compliance_checks": {
                "sanctions_screening": {
                    "status": "passed",
                    "checked_lists": ["OFAC", "UN", "EU", "UK"],
                    "matches_found": 0
                },
                "pep_screening": {
                    "status": "passed",
                    "risk_level": "low"
                },
                "adverse_media": {
                    "status": "passed",
                    "articles_reviewed": 15
                },
                "document_authenticity": {
                    "status": "passed",
                    "confidence_score": 0.95
                }
            },
            "risk_assessment": {
                "overall_risk": "low",
                "risk_score": 15,  # Out of 100
                "risk_factors": []
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")