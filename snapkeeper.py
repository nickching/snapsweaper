import os
import re
import argparse
import base64
import requests
from datetime import datetime

# Configuration
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LANGUAGE = os.getenv('RENAME_LANG', 'en')  # Default to English
API_KEY = os.getenv('DASHSCOPE_API_KEY')
MODEL_NAME = "qwen-vl-max"

def get_image_description(image_path):
    """Get image description (multi-language support)"""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        with open(image_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        
        prompts = {
            'zh-hans': "请用简洁中文描述这张图片的主要内容，不要超过10个字",
            'zh-hant': "請用簡潔繁體中文描述這張圖片的主要內容，不要超過10個字",
            'en': "Describe the main content of this image in brief English within 10 words",
            'jp': "画像の主要内容を10字以内の簡潔な日本語で説明してください"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts[LANGUAGE]},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_data}"
                    }}
                ]
            }]
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=20
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"⚠️ Recognition failed: {str(e)}")
        return None

def process_filename(image_path):
    """Process filename and generate new name"""
    filename = os.path.basename(image_path)
    dir_path = os.path.dirname(image_path)
    
    # Match filename patterns
    old_format = re.match(r"^(Screen Shot|SCR)-(\d{4}(-\d{2}){2}|\d{8})", filename)
    if not old_format:
        return None
    
    # Process date
    raw_date = old_format.group(2)
    date_str = (datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y%m%d") 
                if '-' in raw_date else raw_date)
    
    # Get description
    description = get_image_description(image_path)
    if not description:
        return None
    
    # Sanitize filename
    clean_desc = re.sub(r'[^\w\u4e00-\u9fff-]', '', description.replace(' ', '_'))
    clean_desc = re.sub(r'_+', '_', clean_desc)
    clean_desc = re.sub(r'-+', '-', clean_desc)
    
    # Generate filename with auto-increment
    base_name = f"{date_str}-{clean_desc}.png"
    name_part, ext = os.path.splitext(base_name)
    counter = 1
    new_name = os.path.join(dir_path, base_name)
    
    while os.path.exists(new_name):
        new_name = os.path.join(dir_path, f"{name_part}-{counter}{ext}")
        counter += 1
    
    return new_name

def process_directory(target_dir):
    """Process directory"""
    valid_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(root, file)
                if re.match(r"^(Screen Shot|SCR)-(\d{4}(-\d{2}){2}|\d{8})", file):
                    valid_files.append(full_path)
    
    total = len(valid_files)
    print(f"📂 Found {total} files to process")
    
    for idx, path in enumerate(valid_files, 1):
        print(f"\n🔧 Processing ({idx}/{total}): {os.path.basename(path)}")
        if new_name := process_filename(path):
            try:
                os.rename(path, new_name)
                print(f"   → Renamed to: {os.path.basename(new_name)}")
            except Exception as e:
                print(f"❗ Rename failed: {str(e)}")

def main():
    """Main entry point"""
    print(r"""
   ___                _   __
  / _ \ ___ _ __ ___ | | / /___  _ __ ___
 / /_)/ _ \ '_ ` _ \| |/ / __ \| '_ ` _ \
/ ___/  __/ | | | | | |\ \ ___/| | | | | |
\/    \___|_| |_| |_|_|\_\____/|_| |_| |_| v3.0
    """)
    
    parser = argparse.ArgumentParser(description="SnapKeeper Image Organizer")
    parser.add_argument('path', nargs='?', default=os.getcwd(), help="Target directory")
    parser.add_argument('--lang', choices=['zh-hans', 'zh-hant', 'en', 'jp'], 
                       default='en', help="Output language")
    args = parser.parse_args()
    
    global LANGUAGE
    LANGUAGE = args.lang
    
    if not os.path.isdir(args.path):
        print(f"Error: Invalid directory - {args.path}")
        return
    
    print(f"\n🛠️ Starting processing: {os.path.abspath(args.path)}")
    process_directory(args.path)
    print("\n✅ Processing completed!")

if __name__ == "__main__":
    main() 