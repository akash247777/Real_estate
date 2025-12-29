import os
from PIL import Image
import ollama

# Base folder containing property folders
BASE_FOLDER = r"/content/drive/MyDrive/Propertyimages"

# Iterate through each folder in BASE_FOLDER
for folder_name in os.listdir(BASE_FOLDER):
    folder_path = os.path.join(BASE_FOLDER, folder_name)

    # Skip if not a directory
    if not os.path.isdir(folder_path):
        continue

    # Collect all images in the current folder
    images = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            images.append(os.path.join(folder_path, file))

    # Skip if no images found
    if not images:
        print(f"No images found in {folder_name}. Skipping...")
        continue

    # Prompt for the property description
    prompt = """
    You are an expert real estate property agent with 15+ years of experience.

Analyze ALL the provided property images together and write a professional,
high-conversion property description suitable for premium real estate listings.

While analyzing the ilmages, identify and infer:
- Property type (apartment, villa, independent house, etc.)
- Overall condition (new, renovated, well-maintained)
- Interior highlights (kitchen, granite countertop type if visible, flooring, lighting)
- Bedrooms and bathrooms (if visible)
- Amenities (balcony, parking, pool, modular kitchen, wardrobes, etc.)
- Style and ambiance (luxury, modern, minimal, family-friendly)
- Target buyer profile (family, investor, luxury buyer)

Rules:
- Do NOT mention that the description is generated from images
- Do NOT guess specifics that are not visually evident
- Use confident but realistic real-estate language
- Keep it engaging, professional, and market-ready

Output format:
Title:
Short Description (2–3 lines):
Detailed Description (1–2 paragraphs):
Key Features (bullet points):
    """

    # Call the Ollama API for description
    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "system",
                "content": "You are a professional real estate expert."
            },
            {
                "role": "user",
                "content": prompt,
                "images": images
            }
        ]
    )

    # Extract the description
    description = response["message"]["content"]

    # Save the description to a text file
    output_file = os.path.join(folder_path, f"{folder_name}_description.txt")
    with open(output_file, "w") as f:
        f.write(description)

    print(f"Description for {folder_name} saved to {output_file}")
