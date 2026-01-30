# Design Document: Instagram Caption Generator

## Overview

The Instagram Caption Generator is a Python-based application that transforms visual media (images and videos) into Instagram-ready content. The system employs a multi-stage pipeline: media validation and preprocessing, computer vision analysis using Vision Transformers, and AI-powered content generation via Amazon Bedrock.

The architecture follows a modular design with clear separation of concerns: media processing, AI inference, and content formatting. This approach ensures maintainability, testability, and the ability to swap individual components as AI models evolve.

## Architecture

The system follows a pipeline architecture with four main stages:

``mermaid
graph TD
    A[Media Upload] --> B[File Validation]
    B --> C{File Type?}
    C -->|Image| D[Image Loader]
    C -->|Video| E[Frame Extractor]
    D --> F[Vision Transformer]
    E --> F
    F --> G[Theme Detection]
    G --> H[Bedrock Service]
    H --> I[Caption Generator]
    H --> J[Hashtag Generator]
    I --> K[Output Formatter]
    J --> K
    K --> L[Structured Response]
```

**Stage 1: Media Processing**
- File validation and type detection
- Image loading or video frame extraction
- Format normalization for AI processing

**Stage 2: Visual Analysis**
- Vision Transformer inference
- Primary theme/object detection
- Confidence scoring and validation

**Stage 3: Content Generation**
- Structured prompt creation based on detected themes
- Parallel caption generation (aesthetic, funny, influencer)
- Hashtag generation with relevance filtering

**Stage 4: Output Formatting**
- Content structuring and validation
- Instagram-compatible formatting
- Error handling and user feedback

## Components and Interfaces

### MediaProcessor
**Responsibility:** Handle file upload, validation, and preprocessing

```python
class MediaProcessor:
    def validate_file(self, file_path: str, file_type: str) -> ValidationResult
    def load_image(self, image_path: str) -> PIL.Image
    def extract_frame(self, video_path: str) -> PIL.Image
    def cleanup_temp_files(self, file_paths: List[str]) -> None
```

**Key Methods:**
- `validate_file()`: Checks file type, size, and integrity
- `load_image()`: Loads and normalizes image files
- `extract_frame()`: Uses OpenCV to extract middle frame from videos
- `cleanup_temp_files()`: Manages temporary file lifecycle

### VisionAnalyzer
**Responsibility:** Analyze visual content using Vision Transformer

```python
class VisionAnalyzer:
    def __init__(self, model_name: str = "google/vit-base-patch16-224")
    def analyze_image(self, image: PIL.Image) -> ThemeResult
    def preprocess_image(self, image: PIL.Image) -> torch.Tensor
    def postprocess_predictions(self, predictions: torch.Tensor) -> str
```

**Key Methods:**
- `analyze_image()`: Main inference method returning detected theme
- `preprocess_image()`: Converts PIL Image to model-compatible tensor
- `postprocess_predictions()`: Maps model outputs to human-readable themes

### BedrockService
**Responsibility:** Interface with Amazon Bedrock for text generation

```python
class BedrockService:
    def __init__(self, region: str, model_id: str = "amazon.nova-lite-v1:0")
    def generate_captions(self, theme: str) -> CaptionSet
    def generate_hashtags(self, theme: str) -> List[str]
    def create_prompt(self, theme: str, content_type: str) -> str
```

**Key Methods:**
- `generate_captions()`: Creates three caption styles based on theme
- `generate_hashtags()`: Generates 15 relevant hashtags
- `create_prompt()`: Builds structured prompts for different content types

### ContentFormatter
**Responsibility:** Format and structure final output

```python
class ContentFormatter:
    def format_output(self, captions: CaptionSet, hashtags: List[str]) -> FormattedOutput
    def validate_caption_length(self, caption: str) -> bool
    def format_hashtags(self, hashtags: List[str]) -> str
```

**Key Methods:**
- `format_output()`: Creates final structured response
- `validate_caption_length()`: Ensures captions are under 12 words
- `format_hashtags()`: Formats hashtags as comma-separated lowercase string

## Data Models

### Core Data Structures

```python
@dataclass
class ValidationResult:
    is_valid: bool
    file_type: str
    error_message: Optional[str] = None
    file_size: int = 0

@dataclass
class ThemeResult:
    theme: str
    confidence: float
    alternative_themes: List[str] = field(default_factory=list)

@dataclass
class CaptionSet:
    aesthetic: str
    funny: str
    influencer: str
    
    def validate_lengths(self) -> bool:
        return all(len(caption.split()) <= 12 for caption in [self.aesthetic, self.funny, self.influencer])

@dataclass
class FormattedOutput:
    captions: CaptionSet
    hashtags: str
    processing_time: float
    theme_detected: str
```

### Configuration Models

```python
@dataclass
class ModelConfig:
    vision_model: str = "google/vit-base-patch16-224"
    bedrock_model: str = "amazon.nova-lite-v1:0"
    bedrock_region: str = "us-east-1"
    max_file_size_mb: int = 50
    supported_image_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png"])
    supported_video_formats: List[str] = field(default_factory=lambda: ["mp4", "mov", "mkv"])

@dataclass
class ProcessingConfig:
    caption_max_words: int = 12
    hashtag_count: int = 15
    timeout_seconds: int = 30
    retry_attempts: int = 3
```

### Error Handling Models

```python
class ProcessingError(Exception):
    def __init__(self, message: str, error_type: str, recoverable: bool = False):
        self.message = message
        self.error_type = error_type
        self.recoverable = recoverable
        super().__init__(self.message)

class ValidationError(ProcessingError):
    pass

class VisionAnalysisError(ProcessingError):
    pass

class ContentGenerationError(ProcessingError):
    pass
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: File Format Validation
*For any* file with a supported extension (jpg, jpeg, png, mp4, mov, mkv), the validation system should accept the file as valid for processing
**Validates: Requirements 1.1, 1.2**

### Property 2: Invalid File Rejection
*For any* file with an unsupported extension or exceeding size limits, the validation system should reject the file and return a descriptive error message
**Validates: Requirements 1.3, 1.4**

### Property 3: File Integrity Validation
*For any* uploaded file, the system should validate file integrity before processing and reject corrupted files with appropriate error messages
**Validates: Requirements 1.5**

### Property 4: Video Frame Extraction Consistency
*For any* valid video file, the frame extractor should consistently extract the middle frame and convert it to a format compatible with the Vision Transformer
**Validates: Requirements 2.1, 2.4**

### Property 5: Vision Analysis Completeness
*For any* valid image input (uploaded or extracted), the Vision Transformer should produce a descriptive theme label as a non-empty string
**Validates: Requirements 3.1, 3.3, 3.5**

### Property 6: Caption Generation Completeness
*For any* detected theme, the caption generator should produce exactly three captions (aesthetic, funny, influencer), each under 12 words and relevant to the theme
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6**

### Property 7: Hashtag Generation Specification
*For any* detected theme, the hashtag generator should produce exactly 15 hashtags in lowercase, comma-separated format with no spaces, relevant to the theme
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 8: Output Format Consistency
*For any* successful processing result, the output should be structured with clearly separated captions and copy-ready hashtags, requiring no additional formatting
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 9: Error Handling Robustness
*For any* processing failure scenario, the system should return descriptive error messages and handle timeouts gracefully with appropriate retry logic
**Validates: Requirements 7.1, 7.2, 7.5**

### Property 10: Resource Management
*For any* processing operation (successful or failed), the system should clean up all temporary files and optimize memory usage throughout the pipeline
**Validates: Requirements 7.3, 8.4, 8.5**

### Property 11: Performance Requirements
*For any* typical media file, processing should complete within specified time limits (10 seconds for images, 15 seconds for videos) with progress indicators for large files
**Validates: Requirements 8.1, 8.2, 8.3**

### Property 12: Privacy and Logging
*For any* error that occurs, the system should log debugging information while protecting user privacy and not exposing sensitive data
**Validates: Requirements 7.4**

## Error Handling

The system implements comprehensive error handling across all processing stages:

### Validation Errors
- **File Type Errors**: Clear messages for unsupported formats
- **File Size Errors**: Specific feedback about size limits
- **Integrity Errors**: Detection and reporting of corrupted files

### Processing Errors
- **Vision Analysis Failures**: Graceful handling of model inference errors
- **Frame Extraction Failures**: OpenCV error handling with cleanup
- **Content Generation Failures**: Bedrock service error handling with retries

### Service Integration Errors
- **Network Timeouts**: Exponential backoff retry strategy
- **Authentication Failures**: Clear AWS credential error messages
- **Rate Limiting**: Appropriate backoff and retry mechanisms

### Error Recovery Strategy
```python
class ErrorHandler:
    def handle_with_retry(self, operation: Callable, max_retries: int = 3) -> Any:
        for attempt in range(max_retries):
            try:
                return operation()
            except RecoverableError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
            except NonRecoverableError:
                raise
```

## Testing Strategy

The testing approach combines unit testing for specific scenarios with property-based testing for comprehensive coverage:

### Unit Testing Focus
- **Integration Points**: Testing component interactions and data flow
- **Edge Cases**: Boundary conditions like maximum file sizes, minimum video lengths
- **Error Scenarios**: Specific failure modes and error message validation
- **Configuration Validation**: Testing different model and service configurations

### Property-Based Testing Focus
- **Input Validation**: Testing file validation across all supported and unsupported formats
- **Content Generation**: Verifying caption and hashtag generation properties across diverse themes
- **Format Compliance**: Ensuring output always meets Instagram formatting requirements
- **Resource Management**: Verifying cleanup and memory optimization across all execution paths

### Testing Configuration
- **Property Test Iterations**: Minimum 100 iterations per property test
- **Test Framework**: pytest with hypothesis for property-based testing
- **AWS Mocking**: Use moto library for Bedrock service testing
- **Vision Model Mocking**: Mock HuggingFace transformers for deterministic testing

### Test Tagging Strategy
Each property-based test will be tagged with comments referencing the design document:
```python
def test_caption_generation_completeness():
    """Feature: instagram-caption-generator, Property 6: Caption Generation Completeness"""
    # Test implementation
```

### Performance Testing
- **Load Testing**: Concurrent file processing capabilities
- **Memory Profiling**: Memory usage during video processing
- **Timing Validation**: Verification of processing time requirements
- **Resource Monitoring**: Temporary file cleanup verification