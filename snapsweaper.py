import os
import re
import argparse
import base64
import requests
from datetime import datetime
import json  # 用于格式化JSON输出

# API Configuration
API_CONFIGS = {
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
    },
    'dashscope': {  # Aliyun DashScope
        'base_url': "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
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
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{image_data}"
                    }}
                ]
            }]
        },
        'response_parser': lambda r: r['choices'][0]['message']['content']
    },
    'ollama': {  # Local Ollama
        'base_url': "http://localhost:11434/api/generate",
        'model': "llama3.2-vision",
        'key_env': None,
        'headers': lambda key: {
            "Content-Type": "application/json"
        },
        'payload_format': lambda prompt, image_data: {
            "model": "llama3.2-vision",
            "prompt": prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 50  # 限制输出长度
            }
        },
        'response_parser': lambda r: r['response'].strip()
    }
}

# Configuration
LANGUAGE = os.getenv('RENAME_LANG', 'zh-tw')  # Default to Traditional Chinese
API_PROVIDER = os.getenv('API_PROVIDER', 'openai')  # Default to OpenAI
API_CONFIG = None
API_KEY = None
DEBUG_MODE = False

def check_ollama_service():
    """Check if Ollama service is running and required models are available"""
    try:
        # 检查服务是否运行
        response = requests.get("http://localhost:11434/", timeout=2)
        if response.status_code != 200:
            raise Exception("Ollama service is not running")
        
        # 检查模型是否已安装
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            raise Exception("Cannot check available models")
        
        models = response.json()
        required_models = {
            'llama3.2-vision': False,
            'qwen2.5:32b': False
        }
        
        for model in models['models']:
            for required in required_models:
                if required in model['name']:
                    required_models[required] = True
        
        missing_models = [name for name, found in required_models.items() if not found]
        if missing_models:
            raise Exception(f"Missing required models: {', '.join(missing_models)}")
            
    except requests.exceptions.ConnectionError:
        raise Exception("Cannot connect to Ollama service")
    except Exception as e:
        raise Exception(f"Ollama service error: {str(e)}")

def get_image_content(image_path):
    """First step: Get detailed image content in English"""
    try:
        if API_CONFIG['key_env'] and not API_KEY:
            raise ValueError(f"Missing API key. Please set {API_CONFIG['key_env']}")

        if API_PROVIDER == 'ollama':
            check_ollama_service()

        with open(image_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
            
            if API_PROVIDER != 'ollama':
                base64_data = f"data:image/png;base64,{base64_data}"
        
        # 根据不同的 API 提供商使用不同的提示语
        language_requests = {
            'zh-cn': "Simplified Chinese (简体中文)",
            'zh-tw': "Traditional Chinese (繁體中文)",
            'en': "English",
            'jp': "Japanese (日本語)"
        }
        
        if API_PROVIDER == 'ollama':
            prompt = (
                "You are an image classifier. "
                "Identify the main subject or category of this image in one short phrase. "
                "Focus on WHAT this image is about, not the details. "
                "\n\nExamples:"
                "\nBad: 'A red bicycle parked against a wall with a chain lock'\n"
                "Good: 'Bicycle parking'\n\n"
                "Bad: 'A soccer match with players running after the ball on a green field'\n"
                "Good: 'Soccer game'\n\n"
                "Bad: 'Code editor window showing Python syntax with dark theme'\n"
                "Good: 'Code editor'\n\n"
                "If you cannot identify the image clearly, just reply 'skip'"
            )
        else:
            prompt = (
                "What is the main subject or category of this image? "
                "Give a short, concise answer focusing on the core content. "
                "No details, just the essence."
            )
        
        headers = API_CONFIG['headers'](API_KEY)
        payload = API_CONFIG['payload_format'](prompt, base64_data)
        
        if DEBUG_MODE:
            print("\n🔍 Debug Information (Content Recognition):")
            print(f"API URL: {API_CONFIG['base_url']}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
        
        timeout = 60 if API_PROVIDER == 'ollama' else 20
        response = requests.post(
            API_CONFIG['base_url'],
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code != 200:
            if DEBUG_MODE:
                print(f"Error response body: {response.text}")
            raise Exception(f"API Error: Status {response.status_code}")
            
        result = response.json()
        content = API_CONFIG['response_parser'](result)
        
        if DEBUG_MODE:
            print("\n🔍 Step 1 - Image Recognition:")
            print(f"Result: {content}")
        
        # 检查是否为无效响应
        if not content or content.lower() == 'skip' or len(content) < 3:
            return None
            
        return content
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Content recognition failed: {str(e)}")
        return None

def generate_filename(content):
    """Second step: Generate concise filename in target language"""
    try:
        if not content:
            return None
            
        language_requests = {
            'zh-cn': "简体中文",
            'zh-tw': "繁体中文",
            'en': "英文",
            'jp': "日文"
        }
            
        if API_PROVIDER == 'ollama':
            payload = {
                "model": "qwen2.5:32b",
                "prompt": (
                    f"任务：将英文描述转换为{language_requests[LANGUAGE]}文件名\n\n"
                    f"描述：{content}\n\n"
                    f"要求：\n"
                    f"1. 建议长度在10个字符以内\n"
                    f"2. 保留最核心的含义\n"
                    f"3. 不要解释和标点\n"
                    f"4. 无法总结时输出skip\n\n"
                    f"示例：\n"
                    f"输入：Code editor with Python syntax highlighting\n"
                    f"输出：编程器\n\n"
                    f"输入：Soccer match between two teams on field\n"
                    f"输出：足球赛\n\n"
                    f"输入：Bicycle parking in front of building\n"
                    f"输出：单车位\n\n"
                    f"直接输出文件名："
                ),
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 10,
                    "stop": ["\n", "。", "，", ".", ",", "：", "\"", "'"]
                }
            }
            
            if DEBUG_MODE:
                print("\n🔍 Step 2 - Filename Generation:")
                print(f"Input content: {content}")
                print(f"Using model: qwen2.5:32b")
                
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            if response.status_code != 200:
                if DEBUG_MODE:
                    print(f"Error response: {response.text}")
                return None
                
            result = response.json()
            if DEBUG_MODE:
                print(f"Raw response: {result}")
                
            # 清理响应文本
            filename = result.get('response', '').strip()
            filename = re.sub(r'[^\w\u4e00-\u9fff\s]', '', filename)  # 移除特殊字符
            filename = re.sub(r'\s+', ' ', filename).strip()  # 规范化空格
            
            if DEBUG_MODE:
                print(f"Cleaned filename: {filename}")
            
            # 只检查基本错误
            if not filename or filename.lower() == 'skip':
                print("❌ 错误：模型无法生成合适的文件名")
                return None
            
            return filename
            
        # 对于其他 API，使用原来的方式
        prompt = (
            f"Based on this description: '{content}'\n"
            f"Create a very concise filename in {language_requests[LANGUAGE]}.\n"
            f"Requirements:\n"
            f"- For Chinese: exactly 2-4 characters\n"
            f"- For other languages: exactly 2-3 words\n"
            f"- No sentences, no articles\n"
            f"- Only core meaning\n"
            f"Examples:\n"
            f"- '代码编辑器' not '这是一个代码编辑器界面'\n"
            f"- 'Tokyo Station' not 'This is Tokyo Station'\n"
            f"If unsure, reply 'skip'"
        )
        
        headers = API_CONFIG['headers'](API_KEY)
        payload = API_CONFIG['payload_format'](prompt, "")
        
        if DEBUG_MODE:
            print("\n🔍 Debug Information (Filename Generation):")
            print(f"Content: {content}")
            print(f"Prompt: {prompt}")
        
        response = requests.post(
            API_CONFIG['base_url'],
            json=payload,
            headers=headers,
            timeout=20
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: Status {response.status_code}")
            
        result = response.json()
        return API_CONFIG['response_parser'](result)
        
    except Exception as e:
        print(f"❌ 错误：{str(e)}")
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
    
    if DEBUG_MODE:
        print("\n📝 Processing steps:")
    
    content = get_image_content(image_path)
    if not content:
        if DEBUG_MODE:
            print("❌ Image recognition failed")
        return None
        
    description = generate_filename(content)
    if not description or description.lower() == 'skip':
        if DEBUG_MODE:
            print("❌ Filename generation failed")
        return None
    
    if DEBUG_MODE:
        print(f"✅ Final filename: {description}")
    
    # 清理文件名
    clean_desc = re.sub(r'[^\w\u4e00-\u9fff-]', '', description.replace(' ', '_'))
    clean_desc = re.sub(r'_+', '_', clean_desc)
    clean_desc = re.sub(r'-+', '-', clean_desc)
    clean_desc = clean_desc.strip('_-')
    
    if not clean_desc:
        return None
    
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
    print(f"📂 发现 {total} 个待处理文件\n")
    
    for idx, path in enumerate(valid_files, 1):
        print(f"\n{'='*50}")
        print(f"🔧 处理文件 ({idx}/{total}): {os.path.basename(path)}")
        print(f"{'='*50}")
        
        # Step 1: 图片识别
        print("\n📸 Step 1: 图片识别")
        content = get_image_content(path)
        if not content:
            print("❌ 图片识别失败")
            continue
        print(f"✅ 识别结果: {content}")
        
        # Step 2: 生成文件名
        print("\n📝 Step 2: 生成文件名")
        description = generate_filename(content)
        if not description or description.lower() == 'skip':
            print("❌ 文件名生成失败")
            continue
        print(f"✅ 生成文件名: {description}")
        
        # Step 3: 重命名文件
        if new_name := process_filename(path):
            try:
                os.rename(path, new_name)
                print(f"\n✨ 最终结果: {os.path.basename(new_name)}")
            except Exception as e:
                print(f"❗ 重命名失败: {str(e)}")
        else:
            print("❌ 文件名处理失败")
        
        print(f"\n{'='*50}\n")

def main():
    """Main entry point"""
    print(f"SnapSweaper v1.0")
    print("Created by Nick C.\n")
    
    parser = argparse.ArgumentParser(description="SnapSweaper Image Organizer")
    parser.add_argument('path', nargs='?', default=os.getcwd(), help="Target directory")
    parser.add_argument('--lang', choices=['zh-cn', 'zh-tw', 'en', 'jp'], 
                       default='zh-tw', help="Output language")
    parser.add_argument('--api', choices=list(API_CONFIGS.keys()),
                       default='openai', help="API provider")
    parser.add_argument('--debug', action='store_true',
                       help="Enable debug mode for detailed API information")
    args = parser.parse_args()
    
    global LANGUAGE, API_PROVIDER, API_CONFIG, API_KEY, DEBUG_MODE
    LANGUAGE = args.lang
    API_PROVIDER = args.api
    API_CONFIG = API_CONFIGS[API_PROVIDER]
    
    # 修改 API_KEY 的获取逻辑
    API_KEY = os.getenv(API_CONFIG['key_env']) if API_CONFIG['key_env'] else None
    
    # 修改 API_KEY 的检查逻辑
    if API_CONFIG['key_env'] and not API_KEY:
        print(f"Error: Missing {API_CONFIG['key_env']} environment variable")
        return
    
    print(f"Using {API_PROVIDER.upper()} API")
    
    if not os.path.isdir(args.path):
        print(f"Error: Invalid directory - {args.path}")
        return
    
    print(f"\n🛠️ Starting processing: {os.path.abspath(args.path)}")
    DEBUG_MODE = args.debug
    
    process_directory(args.path)
    print("\n✅ Processing completed!")

if __name__ == "__main__":
    main() 