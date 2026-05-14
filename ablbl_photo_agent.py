import cv2
import numpy as np
from PIL import Image, ImageOps
import os
import requests
import argparse

class ABLBLPhotoAgent:
    def __init__(self, grok_api_key):
        """
        Initialize the agent with the Grok API key.
        """
        self.grok_api_key = grok_api_key
        self.grok_api_url = "https://api.x.ai/v1/chat/completions" 
        self.transparent_template_path = "transparent_template.png"
        
    def prepare_template_from_original(self, original_template_path):
        """
        Creates a transparent PNG from the original JPG template.
        This uses color thresholding to remove the inner green/blue/white area
        while attempting to preserve the red background and leaf.
        
        NOTE: For absolute perfection at scale, it is recommended to create 
        the transparent_template.png manually once using an image editor, 
        and then feed it to this agent.
        """
        if not os.path.exists(original_template_path):
            print(f"Error: Template image '{original_template_path}' not found.")
            return False
            
        print("Processing original template to create transparent frame...")
        img = cv2.imread(original_template_path)
        
        # Convert to RGBA
        b, g, r = cv2.split(img)
        alpha = np.ones(b.shape, dtype=b.dtype) * 255
        
        # Hardcoded approximations based on the layout of "ABLBL Digital Photo Frame"
        height, width = img.shape[:2]
        top = int(height * 0.152)
        bottom = int(height * 0.845)
        left = int(width * 0.138)
        right = int(width * 0.862)
        
        # Make the central rectangle transparent, but try to spare the leaf
        # The leaf is in the bottom left, typically brownish/pinkish.
        for y in range(top, bottom):
            for x in range(left, right):
                b_val, g_val, r_val = img[y, x]
                # Heuristic to remove sky (blue/white) and hills (green)
                # Keep leaf colors (which have more red and less green/blue proportionally)
                is_sky = (b_val > 180 and g_val > 180 and r_val > 180) or (b_val > 200 and r_val < 150)
                is_hills = (g_val > r_val and g_val > b_val) or (g_val > 150 and r_val < 180)
                
                if is_sky or is_hills:
                    alpha[y, x] = 0

        rgba = [b, g, r, alpha]
        transparent_img = cv2.merge(rgba)
        
        cv2.imwrite(self.transparent_template_path, transparent_img)
        print(f"Generated transparent template saved as '{self.transparent_template_path}'")
        return True

    def process_user_portrait(self, user_image_path, template_path, output_path="final_composite.png"):
        """
        Takes the user's portrait and merges it behind the transparent template.
        """
        if not os.path.exists(user_image_path):
            print(f"Error: User photo '{user_image_path}' not found.")
            return

        # Check if the template provided is already a transparent PNG
        # If it's a JPG, we need to generate the transparent mask first
        if template_path.lower().endswith(('.jpg', '.jpeg')):
            print("JPG template detected. Attempting to create transparent mask...")
            if not self.prepare_template_from_original(template_path):
                return
            active_template_path = self.transparent_template_path
        else:
            # Assume it's already a transparent PNG
            active_template_path = template_path

        print(f"Processing user portrait: {user_image_path}")
        
        # Load template
        template = Image.open(active_template_path).convert("RGBA")
        temp_w, temp_h = template.size
        
        # Load user portrait
        user_img = Image.open(user_image_path).convert("RGBA")
        
        # Define the inner window size (where the photo will appear)
        # Using the same approximate percentages
        inner_w = int(temp_w * (0.862 - 0.138))
        inner_h = int(temp_h * (0.845 - 0.152))
        
        # Resize and crop user image to fill the inner window perfectly
        user_img_resized = ImageOps.fit(user_img, (inner_w, inner_h), Image.Resampling.LANCZOS)
        
        # Create a new blank composite image
        composite = Image.new("RGBA", template.size, (255, 255, 255, 0))
        
        # Paste the user image in the center area
        offset_x = int(temp_w * 0.138)
        offset_y = int(temp_h * 0.152)
        composite.paste(user_img_resized, (offset_x, offset_y))
        
        # Overlay the frame template on top
        # Because the center of the template is transparent, the user photo shows through
        # and the leaf/borders naturally overlap the user photo!
        composite.alpha_composite(template)
        
        # Convert to RGB to save as high-quality JPG (or keep as PNG)
        final_rgb = composite.convert("RGB")
        final_rgb.save(output_path, "PNG")
        print(f"Success! High-definition composite image saved to '{output_path}'")

    def call_grok_llm(self, prompt):
        """
        Integration with the Grok API.
        Can be used to generate captions for social media based on the portrait.
        """
        print("\n--- Requesting social media caption from Grok ---")
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": "You are a professional social media manager for Aditya Birla Lifestyle Brands. Write short, engaging captions."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(self.grok_api_url, headers=headers, json=data)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            print(f"Grok API Response:\n{content}\n")
            return content
        except Exception as e:
            print(f"Error calling Grok API: {e}")
            return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ABLBL Digital Photo Frame Agent")
    parser.add_argument("--template", type=str, required=True, help="Path to original JPG template or pre-made transparent PNG")
    parser.add_argument("--user_photo", type=str, required=True, help="Path to the user's portrait photo")
    parser.add_argument("--output", type=str, default="final_composite.png", help="Path for the output composite image")
    parser.add_argument("--generate_caption", action="store_true", help="Use Grok API to generate a social media caption")
    args = parser.parse_args()
    
    # Initialize the Agent with the provided Grok API Key
    GROK_API_KEY = "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"
    agent = ABLBLPhotoAgent(grok_api_key=GROK_API_KEY)
    
    # Run the composite process
    agent.process_user_portrait(args.user_photo, args.template, args.output)
    
    if args.generate_caption:
        agent.call_grok_llm("Generate a short, professional LinkedIn caption welcoming a new talent to the 'World of Opportunities' at Aditya Birla Lifestyle Brands.")
