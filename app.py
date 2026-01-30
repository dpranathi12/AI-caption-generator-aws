import boto3
import json
import cv2
from PIL import Image
from transformers import ViTImageProcessor, ViTForImageClassification
import torch

# ---------------------------------------------------------
# AWS BEDROCK CLIENT (Nova Lite v1)
# ---------------------------------------------------------
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def bedrock_generate(prompt):
    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = bedrock.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json"
    )

    data = json.loads(response["body"].read())
    return data["output"]["message"]["content"][0]["text"]


# ---------------------------------------------------------
# LOAD VISION MODEL (ViT)
# ---------------------------------------------------------
print("Loading ViT Image Model...")
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224")
print("Vision model loaded!\n")


# ---------------------------------------------------------
# IMAGE CLASSIFICATION FUNCTION
# ---------------------------------------------------------
def classify_image(pil_img):
    inputs = processor(images=pil_img, return_tensors="pt")
    outputs = model(**inputs)
    pred = outputs.logits.argmax(-1).item()
    return model.config.id2label[pred]


# ---------------------------------------------------------
# VIDEO FRAME EXTRACTION — MIDDLE FRAME
# ---------------------------------------------------------
def extract_middle_frame(video_path):
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mid = total_frames // 2

    cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
    success, frame = cap.read()
    cap.release()

    if not success:
        raise Exception("Could not extract frame!")

    # Convert BGR (OpenCV) → RGB (PIL)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


# ---------------------------------------------------------
# GENERATE CAPTIONS + HASHTAGS USING BEDROCK
# ---------------------------------------------------------
def generate_caption_and_hashtags(theme):
    caption_prompt = f"""
Generate 3 Instagram captions for: {theme}

1. Aesthetic (under 12 words)
2. Funny (under 12 words)
3. Influencer style (under 12 words)
"""

    hashtags_prompt = f"""
Generate 15 Instagram hashtags for {theme}.
Rules:
- lowercase
- no spaces
- comma separated
"""

    captions = bedrock_generate(caption_prompt)
    hashtags = bedrock_generate(hashtags_prompt)

    return captions, hashtags


# ---------------------------------------------------------
# MAIN HANDLER — IMAGE OR VIDEO
# ---------------------------------------------------------
def process_file(path):
    # IMAGE FILES
    if path.lower().endswith((".jpg", ".jpeg", ".png")):
        print("Processing IMAGE...\n")
        img = Image.open(path)
        label = classify_image(img)

    # VIDEO FILES
    elif path.lower().endswith((".mp4", ".mov", ".mkv")):
        print("Processing VIDEO...\n")
        img = extract_middle_frame(path)
        label = classify_image(img)

    else:
        print("Unsupported file!")
        return

    print("Detected Theme:", label)

    captions, hashtags = generate_caption_and_hashtags(label)

    print("\n✨ CAPTIONS:\n", captions)
    print("\n🔖 HASHTAGS:\n", hashtags)


# ---------------------------------------------------------
# RUN SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    file_path = input("Enter image/video file path: ")
    process_file(file_path)










