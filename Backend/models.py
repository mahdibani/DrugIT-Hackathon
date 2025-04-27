from ultralytics import YOLO
from transformers import pipeline
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Medical imaging models configuration
MODELS = {
    "brain_tumor": {
        "type": "huggingface",
        "model_name": "shimaGh/Brain-Tumor-Detection",
        "target_size": (224, 224)
    },
    "breast_tumor": {
        "type": "yolo_local",
        "model_path": "yolov8_medical_detection.pt", 
        "target_size": (640, 640), 
        "conf_threshold": 0.25
    },
    "pneumonia": {
        "type": "huggingface",
        "model_name": "nickmuchi/vit-finetuned-chest-xray-pneumonia",
        "target_size": (224, 224)
    },
    "malaria": {
        "type": "yolo",
        "model_name": "ultralytics/yolov8n.pt",
        "conf_threshold": 0.5,
        "target_size": (640, 640)
    }
}

# Dictionary to store loaded models
loaded_models = {}

def load_models():
    """Load and initialize all medical imaging models"""
    logger.info("🔄 Loading medical imaging models...")
    for disease, config in MODELS.items():
        try:
            if config["type"] == "huggingface":
                loaded_models[disease] = pipeline("image-classification", model=config["model_name"])
                logger.info(f"✅ Loaded Hugging Face model for {disease}")
            elif config["type"] == "yolo":
                loaded_models[disease] = YOLO(config["model_name"])
                logger.info(f"✅ Loaded YOLO model for {disease}")
            elif config["type"] == "yolo_local":
                # Load local YOLO model
                model_path = config["model_path"]
                if os.path.exists(model_path):
                    loaded_models[disease] = YOLO(model_path)
                    logger.info(f"✅ Loaded local YOLO model for {disease} from {model_path}")
                else:
                    logger.error(f"❌ Local YOLO model file not found: {model_path}")
                    loaded_models[disease] = None
        except Exception as e:
            logger.error(f"❌ Failed to load model for {disease}: {e}")
            loaded_models[disease] = None
    logger.info("🚀 All medical models loaded!")
    return loaded_models

# Initialize models when module is imported
loaded_models = load_models()