# SnapSweaper 📸✨

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

智能截圖整理工具 | Intelligent Screenshot Organizer

> 自動將您的截圖使用 AI 智能識別並重新命名，支持多種 AI 模型和多語言輸出。
> Automatically rename your screenshots using AI recognition, supporting multiple AI models and languages.

---

## 目錄 | Table of Contents
- [功能特色 | Features](#功能特色--features)
- [快速開始 | Quick Start](#快速開始--quick-start)
- [使用範例 | Examples](#使用範例--examples)
- [API設定 | API Configuration](#api設定--api-configuration)
- [常見問題 | FAQ](#常見問題--faq)

## 功能特色 | Features 🚀

### 中文版
- 🤖 **智能 AI 支援** - 整合通義千問、OpenAI 等頂級視覺模型
- 📝 **智能命名** - 自動轉換為「YYYYMMDD-描述」格式
- 🌏 **多語言輸出** - 支援繁體/簡體中文、英文、日文
- 🔄 **智能防重複** - 自動處理重複檔案（自動編號）
- 📁 **批量處理** - 支援遞迴處理整個目錄結構

### English Version
- 🤖 **Smart AI Support** - Integrated with DashScope, OpenAI and more
- 📝 **Intelligent Naming** - Auto converts to "YYYYMMDD-description" format
- 🌏 **Multi-language** - Support for Chinese (Traditional/Simplified), English, Japanese
- 🔄 **Duplicate Prevention** - Smart handling of duplicate files (auto-numbering)
- 📁 **Batch Processing** - Recursive directory processing support

## 快速開始 | Quick Start ⚡

### 安裝步驟 | Installation
```bash
# 1. 下載專案 | Clone the repository
git clone https://github.com/nickching/snapsweaper.git
cd snapsweaper

# 2. 安裝依賴 | Install dependencies
pip install -r requirements.txt

# 3. 設定 API 金鑰 | Set API Key (choose one)
export DASHSCOPE_API_KEY="your_key_here"    # For DashScope
export OPENAI_API_KEY="your_key_here"       # For OpenAI
```

### 基本使用 | Basic Usage
```bash
# 使用預設 API（通義千問）| Use default API (DashScope)
python snapsweaper.py ~/Screenshots

# 使用 OpenAI | Use OpenAI
python snapsweaper.py --api openai ~/Screenshots
```

### 語言選項 | Language Options
```bash
python snapsweaper.py [目錄路徑] --lang [語言代碼]

# 支援的語言代碼 | Supported language codes:
# zh-tw: 繁體中文（預設）| Traditional Chinese (Default)
# zh-cn: 簡體中文 | Simplified Chinese
# en: 英文 | English
# jp: 日文 | Japanese
```

## API 設定 | API Configuration ⚙️

### 支援的 API 服務 | Supported API Services
| 服務商 Provider | 環境變數 Env Variable | 模型 Model | 特點 Features |
|----------------|---------------------|------------|--------------|
| 通義千問 DashScope | DASHSCOPE_API_KEY | qwen-vl-max | 中文優化、響應快速 |
| OpenAI | OPENAI_API_KEY | gpt-4-vision-preview | 準確度高、多語言支援佳 |

### 命令列參數 | Command Arguments
| 參數 Parameter | 說明 Description | 預設值 Default | 示例 Example |
|---------------|-----------------|---------------|--------------|
| path | 目標目錄 Target directory | 當前目錄 Current | `~/Screenshots` |
| --lang | 輸出語言 Output language | zh-tw | `--lang en` |
| --api | API 服務商 Provider | dashscope | `--api openai` |

### 檔案命名規則 | Filename Pattern
- 輸入格式 | Input: 
  - `Screen Shot YYYY-MM-DD...`
  - `SCR-YYYYMMDD...`
- 輸出格式 | Output: 
  - `YYYYMMDD-description[-n].png`

## 常見問題 | FAQ ❓

### 使用須知 | Usage Notes
- 🖼️ 支援 PNG、JPG、JPEG 格式圖片
- 📦 建議圖片大小不超過 10MB
- 🔑 請確保 API 金鑰有效且有足夠額度
- 🔄 首次使用建議先測試少量檔案

### 故障排除 | Troubleshooting
- API 金鑰無效：檢查環境變數設置
- 檔案無法識別：確認檔案名稱格式
- 處理失敗：檢查網絡連接和 API 額度

## 授權與貢獻 | License & Contributing 📜

- 授權協議 | License: [MIT License](LICENSE)
- 歡迎提交 Issue 和 Pull Request | Issues and PRs welcome
- 作者 | Author: Nick C. - [GitHub](https://github.com/nickching)

---

💡 **提示**: 首次使用時，建議先在小批量檔案上測試，以熟悉工具的使用方式。  
💡 **Tip**: For first-time users, it's recommended to test with a small batch of files to get familiar with the tool.
