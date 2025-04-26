from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline, AutoModelForImageClassification, AutoImageProcessor
from ultralytics import YOLO
from PIL import Image
import shutil
import os
import torch
import uvicorn
import logging
from typing import Dict, Any

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Configuration ---
MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "brain_tumor": {
        "type": "huggingface",
        "model_name": "shimaGh/Brain-Tumor-Detection",
        "target_size": (224, 224),
        "label_map": {
            "glioma_tumor": "Tumor",
            "meningioma_tumor": "Tumor",
            "pituitary_tumor": "Tumor",
            "no_tumor": "Normal"
        }
    },
    "breast_cancer": {
        "type": "huggingface",
        "model_name": "Adam118/breast-cancer-classification",
        "target_size": (224, 224),
        "label_map": {
            "malignant": "Cancer",
            "benign": "Normal"
        }
    },
    "pneumonia": {
        "type": "huggingface",
        "model_name": "nickmuchi/vit-finetuned-chest-xray-pneumonia",
        "target_size": (224, 224),
        "label_map": {
            "PNEUMONIA": "Pneumonia",
            "NORMAL": "Normal"
        }
    },
    "skin_cancer": {
        "type": "huggingface",
        "model_name": "syaha/skin_cancer_detection_model",
        "processor": "google/vit-base-patch16-224-in21k",
        "target_size": (224, 224)
    },
    "malaria": {
        "type": "yolo",
        "model_name": "ultralyticsplus/yolov8s",
        "conf_threshold": 0.5,
        "target_size": (640, 640)
    }
}

# --- Clinical Pathways ---
CLINICAL_PATHWAYS = {
    "brain_tumor": {
        "Tumor": {
            "diagnosis": "Brain Tumor Detected",
            "care_pathway": [
                "Neurology consultation",
                "MRI with contrast",
                "Biopsy for histopathology",
                "Neurosurgery evaluation"
            ],
            "advice": "Urgent specialist referral required"
        },
        "Normal": {
            "care_pathway": ["Routine follow-up"],
            "advice": "No immediate intervention needed"
        }
    },
    "pneumonia": {
        "Pneumonia": {
            "care_pathway": [
                "Chest X-ray confirmation",
                "Antibiotic therapy",
                "Pulmonary function tests",
                "Follow-up in 72 hours"
            ],
            "advice": "Immediate antibiotic treatment recommended"
        },
        "Normal": {
            "care_pathway": ["Preventive vaccination"],
            "advice": "Maintain respiratory hygiene"
        }
    }
}

# --- Load Models ---
loaded_models: Dict[str, Any] = {}

logger.info("🔄 Initializing medical imaging models...")

for disease, config in MODEL_CONFIG.items():
    try:
        if config["type"] == "huggingface":
            if disease == "skin_cancer":
                loaded_models[disease] = {
                    "model": AutoModelForImageClassification.from_pretrained(
                        config["model_name"],
                    ),
                    "processor": AutoImageProcessor.from_pretrained(
                        config.get("processor", config["model_name"])
                    )
                }
            else:
                loaded_models[disease] = pipeline(
                    "image-classification", 
                    model=config["model_name"]
                )
            logger.info(f"✅ {disease.replace('_', ' ').title()} model loaded")
            
        elif config["type"] == "yolo":
            loaded_models[disease] = YOLO(config["model_name"])
            loaded_models[disease].set(parameters={'task': 'detect', 'mode': 'predict'})
            logger.info(f"✅ {disease.replace('_', ' ').title()} model loaded")
            
    except Exception as e:
        logger.error(f"❌ Model initialization failed for {disease}: {str(e)}")
        loaded_models[disease] = None

logger.info("🚀 Model initialization complete")

def save_temp_image(upload_file: UploadFile) -> str:
    """Securely save uploaded image to temporary storage"""
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, upload_file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return temp_path

def process_image(image_path: str, config: Dict[str, Any]) -> Image.Image:
    """Process and standardize medical images"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB for model compatibility
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Maintain aspect ratio while resizing
            target_size = config.get("target_size", (224, 224))
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            return img
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        raise ValueError("Invalid medical image format")

def format_diagnosis(disease_type: str, raw_label: str) -> str:
    """Convert model-specific labels to standardized diagnoses"""
    label_map = MODEL_CONFIG.get(disease_type, {}).get("label_map", {})
    for pattern, diagnosis in label_map.items():
        if pattern.lower() in raw_label.lower():
            return diagnosis
    return raw_label.title()

@app.post("/predict/")
async def predict(
    file: UploadFile = File(...),
    disease_type: str = Form(...)
) -> JSONResponse:
    """Main prediction endpoint for medical image analysis"""
    temp_path = None
    try:
        # Validate request parameters
        if disease_type not in MODEL_CONFIG:
            raise HTTPException(400, detail="Invalid medical condition specified")
            
        model_config = MODEL_CONFIG[disease_type]
        model = loaded_models.get(disease_type)
        if not model:
            raise HTTPException(503, detail="Diagnostic model currently unavailable")
        
        # Process medical image
        temp_path = save_temp_image(file)
        processed_image = process_image(temp_path, model_config)
        
        # Perform medical analysis
        if model_config["type"] == "huggingface":
            if disease_type == "skin_cancer":
                inputs = model["processor"](images=processed_image, return_tensors="pt")
                outputs = model["model"](**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidence = round(float(probs[0][1]) * 100, 2)
                diagnosis = "Cancer" if confidence > 50 else "Normal"
            else:
                result = model(processed_image)
                raw_label = result[0]['label']
                diagnosis = format_diagnosis(disease_type, raw_label)
                confidence = round(result[0]['score'] * 100, 2)
                
        elif disease_type == "malaria":
            results = model.predict(processed_image, conf=0.5)
            diagnosis = "Infected" if len(results[0].boxes) > 0 else "Normal"
            confidence = round(float(results[0].boxes[0].conf[0]) * 100, 2) if len(results[0].boxes) > 0 else 0.0
        
        # Get clinical guidance
        pathway = CLINICAL_PATHWAYS.get(disease_type, {}).get(diagnosis, {})
        
        return JSONResponse(content={
            "diagnosis": diagnosis,
            "confidence": f"{confidence:.2f}%",
            "clinical_pathway": pathway.get("care_pathway", ["Consult specialist"]),
            "medical_advice": pathway.get("advice", "Seek professional consultation")
        })
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Diagnostic error: {str(e)}")
        raise HTTPException(500, detail="Medical image analysis failed")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)