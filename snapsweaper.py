import os
import re
import argparse
import base64
import requests
from datetime import datetime

# API Configuration
API_CONFIGS = {
    'dashscope': {  # Aliyun DashScope
        'base_url': "https://dashscope.aliyuncs.com/compatible-mode/v1",
        'model': "qwen-vl-max",
        'key_env': "DASHSCOPE_API_KEY",
        'headers': lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        'payload_format': lambda prompt, image_data: {
            "model": "qwen-vl-max",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }]
        },
        'response_parser': lambda r: r['choices'][0]['message']['content']
    },
    'openai': {  # OpenAI GPT-4 Vision
        'base_url': "https://api.openai.com/v1/chat/completions",
        'model': "gpt-4-vision-preview",
        'key_env': "OPENAI_API_KEY",
        'headers': lambda key: {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        'payload_format': lambda prompt, image_data: {
            "model": "gpt-4-vision-preview",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "url": f"data:image/png;base64,{image_data}"}
                ]
            }],
            "max_tokens": 100
        },
        'response_parser': lambda r: r['choices'][0]['message']['content']
    }
}

# Configuration
API_PROVIDER = os.getenv('API_PROVIDER', 'dashscope')  # Default to DashScope
LANGUAGE = os.getenv('RENAME_LANG', 'zh-tw')  # Default to Traditional Chinese
API_CONFIG = API_CONFIGS[API_PROVIDER]
API_KEY = os.getenv(API_CONFIG['key_env'])

def get_image_description(image_path):
    """Get image description (multi-language support)"""
    try:
        if not API_KEY:
            raise ValueError(f"Missing API key. Please set {API_CONFIG['key_env']}")

        with open(image_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
        
        prompts = {
            'zh-cn': "请用简洁中文描述这张图片的主要内容，不要超过10个字",
            'zh-tw': "請用簡潔繁體中文描述這張圖片的主要內容，不要超過10個字",
            'en': "Describe the main content of this image in brief English within 10 words",
            'jp': "画像の主要内容を10字以内の簡潔な日本語で説明してください"
        }
        
        headers = API_CONFIG['headers'](API_KEY)
        payload = API_CONFIG['payload_format'](prompts[LANGUAGE], base64_data)
        
        response = requests.post(
            API_CONFIG['base_url'],
            json=payload,
            headers=headers,
            timeout=20
        )
        result = response.json()
        
        if response.status_code != 200:
            raise Exception(f"API Error: {result.get('error', {}).get('message', 'Unknown error')}")
            
        return API_CONFIG['response_parser'](result)
    except Exception as e:
        print(f"⚠️ Recognition failed: {str(e)}")
        return None

def process_filename(image_path):
    """处理文件名并生成新名称"""
    filename = os.path.basename(image_path)
    dir_path = os.path.dirname(image_path)
    
    # 匹配文件名模式
    old_format = re.match(r"^(Screen Shot|SCR)-(\d{4}(-\d{2}){2}|\d{8})", filename)
    if not old_format:
        return None
    
    # 处理日期
    raw_date = old_format.group(2)
    date_str = (datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y%m%d") 
                if '-' in raw_date else raw_date)
    
    # 获取描述
    description = get_image_description(image_path)
    if not description:
        return None
    
    # 清理文件名
    clean_desc = re.sub(r'[^\w\u4e00-\u9fff-]', '', description.replace(' ', '_'))
    clean_desc = re.sub(r'_+', '_', clean_desc)
    clean_desc = re.sub(r'-+', '-', clean_desc)
    
    # 生成带自增的文件名
    base_name = f"{date_str}-{clean_desc}.png"
    name_part, ext = os.path.splitext(base_name)
    counter = 1
    new_name = os.path.join(dir_path, base_name)
    
    while os.path.exists(new_name):
        new_name = os.path.join(dir_path, f"{name_part}-{counter}{ext}")
        counter += 1
    
    return new_name

def process_directory(target_dir):
    """处理目录"""
    valid_files = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(root, file)
                if re.match(r"^(Screen Shot|SCR)-(\d{4}(-\d{2}){2}|\d{8})", file):
                    valid_files.append(full_path)
    
    total = len(valid_files)
    print(f"📂 发现 {total} 个待处理文件")
    
    for idx, path in enumerate(valid_files, 1):
        print(f"\n🔧 正在处理 ({idx}/{total}): {os.path.basename(path)}")
        if new_name := process_filename(path):
            try:
                os.rename(path, new_name)
                print(f"   → 重命名为: {os.path.basename(new_name)}")
            except Exception as e:
                print(f"❗ 重命名失败: {str(e)}")

def main():
    """Main entry point"""
    print(f"SnapSweaper v1.0 - Using {API_PROVIDER.upper()} API")
    print("Created by Nick C.\n")
    
    parser = argparse.ArgumentParser(description="SnapSweaper Image Organizer")
    parser.add_argument('path', nargs='?', default=os.getcwd(), help="Target directory")
    parser.add_argument('--lang', choices=['zh-cn', 'zh-tw', 'en', 'jp'], 
                       default='zh-tw', help="Output language")
    parser.add_argument('--api', choices=list(API_CONFIGS.keys()),
                       default='dashscope', help="API provider")
    args = parser.parse_args()
    
    global LANGUAGE, API_PROVIDER, API_CONFIG, API_KEY
    LANGUAGE = args.lang
    if args.api != API_PROVIDER:
        API_PROVIDER = args.api
        API_CONFIG = API_CONFIGS[API_PROVIDER]
        API_KEY = os.getenv(API_CONFIG['key_env'])
    
    if not API_KEY:
        print(f"Error: Missing {API_CONFIG['key_env']} environment variable")
        return
    
    if not os.path.isdir(args.path):
        print(f"Error: Invalid directory - {args.path}")
        return
    
    print(f"\n🛠️ Starting processing: {os.path.abspath(args.path)}")
    process_directory(args.path)
    print("\n✅ Processing completed!")

if __name__ == "__main__":
    main() 