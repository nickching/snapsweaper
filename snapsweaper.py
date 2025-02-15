import argparse
import os

def main():
    """Main entry point"""
    print("SnapSweaper v1.0 - Intelligent Screenshot Organizer")
    print("Created by Nick C.\n")
    
    # 保留原有参数解析逻辑
    parser = argparse.ArgumentParser(description="SnapSweaper Image Organizer")
    parser.add_argument('path', nargs='?', default=os.getcwd(), help="Target directory")
    parser.add_argument('--lang', choices=['zh-hans', 'zh-hant', 'en', 'jp'], 
                       default='en', help="Output language")
    args = parser.parse_args()
    
    # ...保留后续处理逻辑不变... 