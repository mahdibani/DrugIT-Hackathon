# DrugIT-Hackathon
# AI-Powered Healthcare Diagnostic Platform

## Overview

This platform is an end-to-end AI-powered healthcare diagnostic system built on a multi-agent architecture. Each specialized agent contributes to different aspects of the medical decision-making pipeline, creating a comprehensive system that simulates how a real clinical team collaborates.

The system processes medical images and documents, provides clinical reasoning, and offers treatment recommendations through a coordinated series of AI agents. The architecture supports sequential, parallel, and feedback-loop agent interactions to deliver medical-grade assessments.

## Key Features

- **Multi-Agent Architecture**: Specialized AI agents working together in a coordinated system
- **Medical Imaging Analysis**: Deep learning models for disease classification and detection
- **Document Processing**: Extraction and structuring of clinical data from medical records
- **Clinical Reasoning**: AI-powered differential diagnosis and assessment generation
- **Treatment Recommendations**: Evidence-based treatment suggestions
- **Secure API Orchestration**: FastAPI-based system managing requests, states, and workflows

## System Architecture
![image](https://github.com/user-attachments/assets/36304865-f81e-4345-a035-4e023f28e25e)


The platform consists of the following components:

### 1. Medical Imaging Agent
- Utilizes HuggingFace vision transformers for disease classification
  - Brain tumor detection
  - Pneumonia diagnosis
- Implements YOLOv8 object detection for malaria parasite identification
- Models dynamically loaded and managed through a structured Model Registry

### 2. Document Processing Agent
- Extracts and structures clinical data from medical records
- Bridges image analysis with patient history information
- Utilizes NLP techniques for medical text understanding

### 3. Clinical Reasoning Agent
- Powered by Large Language Models through OpenRouter
- Synthesizes multi-modal insights from imaging and documents
- Generates differential diagnoses and structured clinical assessments

### 4. Treatment Recommendation Agent
- Aligns diagnoses with evidence-based treatments
- Utilizes internal treatment database
- Considers patient-specific factors in recommendations

### 5. Orchestration Agent
- FastAPI-based system coordination
- Routes requests to appropriate agents
- Maintains conversation states
- Manages asynchronous API workflows
- Secures communication between components

## Technical Details

### Image Processing
- Standardizes medical images using PIL preprocessing
- Applies disease-specific logic based on image type
- Normalizes heterogeneous model outputs

### Model Management
- Structured Model Registry for versioning
- Dynamic model loading based on diagnostic needs
- Support for multiple deep learning frameworks (PyTorch, TensorFlow, JAX)

### API Infrastructure
- FastAPI for high-performance async API endpoints
- Authentication and authorization mechanisms
- Input validation using Pydantic models
- Comprehensive logging and monitoring

## Installation

### Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended for inference)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/healthcare-diagnostic-platform.git
cd healthcare-diagnostic-platform
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

### Starting the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API documentation can be accessed at `http://localhost:8000/docs`.

### API Endpoints

- `/api/v1/diagnose/image`: Upload medical images for diagnosis
- `/api/v1/diagnose/document`: Upload medical documents for processing
- `/api/v1/assessment`: Generate comprehensive clinical assessment
- `/api/v1/recommend`: Get treatment recommendations

### Sample Request

```python
import requests

# Upload an image for diagnosis
url = "http://localhost:8000/api/v1/diagnose/image"
files = {"file": open("chest_xray.jpg", "rb")}
data = {"case_id": "12345", "image_type": "chest_xray"}

response = requests.post(url, files=files, data=data)
result = response.json()
print(result)
```

## Project Structure


## Development

### Adding New Models

1. Place model implementation in the appropriate directory under `ml_models/`
2. Register the model in `ml_models/registry.py`
3. Implement agent integration in the relevant agent class

### Running Tests

```bash
pytest
```

## Future Enhancements

- Federated learning capabilities for distributed model training
- Support for additional medical imaging modalities (MRI, ultrasound)
- Enhanced explainability and visualization features
- Integration with electronic health record (EHR) systems
- Mobile application for remote diagnostics
- Expanded treatment recommendation database

## Dependencies

- pydantic - Data validation and settings management
- requests - HTTP requests
- python-dotenv - Environment variable management
- fastapi - API framework
- scikit-learn - Machine learning utilities
- uvicorn - ASGI server
- asyncio - Asynchronous I/O
- PyPDF2 - PDF document processing
- nest_asyncio - Nested asyncio support
- pillow - Image processing
- transformers - Hugging Face transformers
- torch - PyTorch deep learning framework
- keras - Keras deep learning API
- jax & jaxlib - JAX machine learning framework
- ultralytics - YOLOv8 implementation
- python-multipart - Multipart form data parsing
- openai - OpenAI API integration
- python-dotenv - Environment variable management

## License

[MIT License](LICENSE)
demo video:
  https://github.com/user-attachments/assets/4cf88e89-6919-4ada-aacd-2756b874fecf
