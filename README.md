## Hi there 👋

歡迎造訪 **Pneumonia Detection** 專案！本倉庫提供一套在 **Raspberry Pi 4B (2 GB RAM, arm64, Python 3.11)** 上運行的肺炎 X 光影像判讀圖形介面（GUI）。系統以 **ONNXRuntime** 進行模型推論，介面採用 **Tkinter**，特別針對嵌入式硬體的有限資源進行最佳化。

---

### ✨ 主要特色

| 功能                  | 說明                                          |
| ------------------- | ------------------------------------------- |
| 輕量化部署               | < 120 MB 依賴體積，< 1.3 GB 執行記憶體上限              |
| 多模型管理               | 透過 **Model Manager** 熱插拔 ONNX 模型；支援動態換模不需重啟 |
| 直覺式 GUI             | 拖放影像、按鈕觸發分析；分頁顯示分類、歷史、評估與混淆矩陣               |
| 歷史與結果追蹤             | 自動記錄推論結果、機率分布與原始影像，便於後續審閱                   |
| Confusion Matrix 回溯 | 以圖像與統計方式呈現不同模型／批次的效能比較                      |
| 通知系統                | 執行進度、錯誤與完成事件即時彈窗                            |

---

### 🗂️ 專案結構

```text
pneumonia_detection/
├── app_ui.py                 # 程式進入點，組合並啟動各分頁 UI
├── run.sh                    # Linux/macOS 一鍵啟動指令稿
├── requirements.txt          # Python 相依套件清單
├── front/                    # 介面層 (Tkinter)
│   ├── config.py             # 介面主題與共用樣式
│   ├── apple_styles.py       # macOS Shortcut 風格覆寫
│   ├── drag_drop_handler.py  # 檔案拖放整合
│   ├── tabs_ui.py            # 分頁容器
│   ├── classify_tab_ui.py    # 分類頁
│   ├── model_selection_ui.py # 模型選擇頁
│   ├── history_tab_ui.py     # 推論紀錄頁
│   ├── confusion_matrix_tab_ui.py          # 單次混淆矩陣
│   ├── confusion_matrix_history_tab_ui.py  # 歷史混淆矩陣
│   ├── image_cache.py        # 快取已載入影像
│   └── notification_system.py# 統一訊息彈窗
├── backend/                  # 後端邏輯
│   ├── ModelManager.py       # 模型載入／切換／資訊
│   ├── HistoryManager.py     # 推論結果與影像歷史
│   ├── ImagePreprocessing.py # CLAHE、histogram matching…
│   ├── Inference.py          # ONNXRuntime 推論封裝
│   ├── ConfusionMatrixManager.py # 效能統計與圖像生成
│   └── Evaluation.py         # 整批評估流程
├── models/                   # 放置 .onnx 模型檔
├── history/
│   └── images/               # 分類影像與 JSON 結果
└── confusion_history/
    └── images/               # 過往混淆矩陣快照
```

---
### 📦 已測試相依套件版本 (2025-06-08)

```text
Package           Version
----------------- -----------
coloredlogs       15.0.1
contourpy         1.3.1
cycler            0.12.1
filelock          3.18.0
flatbuffers       25.2.10
fonttools         4.56.0
fsspec            2025.3.0
humanfriendly     10.0
imutils           0.5.4
iniconfig         2.1.0
Jinja2            3.1.6
joblib            1.4.2
kiwisolver        1.4.8
MarkupSafe        3.0.2
matplotlib        3.10.1
mpmath            1.3.0
networkx          3.4.2
numpy             2.2.4
onnxruntime       1.20.1
opencv-python     4.11.0.86
packaging         24.2
pandas            2.2.3
pillow            11.1.0
pip               25.0.1
pluggy            1.5.0
protobuf          6.30.2
pyasn1            0.6.1
pydot             3.0.4
pyparsing         3.2.1
pytest            8.3.5
python-dateutil   2.9.0.post0
python-tkdnd      0.2.1
pytz              2025.1
rsa               4.9
scikit-learn      1.6.1
scipy             1.15.2
seaborn           0.13.2
setuptools        75.8.0
six               1.17.0
sympy             1.13.1
threadpoolctl     3.6.0
torch             2.6.0
torchvision       0.21.0
tqdm              4.67.1
ttkwidgets        0.13.0
typing_extensions 4.12.2
tzdata            2025.1
wheel             0.45.1
onnx              1.17.0
ttkthemes         3.2.2
```



### 🚀 快速開始

```bash


# 1. 安裝相依套件（建議使用 Python 3.11 venv）
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt

# 2. 啟動 GUI（有兩種方式擇一）
(.venv) $ ./run.sh          # Bash 腳本
#   或
(.venv) $ python app_ui.py  # 直接執行 Python 進入點
```

> 💡 **注意**：若系統未安裝 `libatlas` / `openblas`，請先於 Raspberry Pi 上執行 `sudo apt install libatlas-base-dev` 以避免 ONNXRuntime CPU provider 因缺少 BLAS 而報錯。

---

### 🖼️ 使用流程

1. **選擇模型**：於「Model」分頁點選下拉選單，載入欲測試的 `.onnx`。
2. **匯入影像**：在「Classify」分頁拖放胸腔 X 光影像（支援 JPG/PNG）。
3. **分析**：按 **Analyze**；推論結果、機率分布與可解釋性影像將顯示於右側。
4. **查看歷史**：切換至「History」分頁比對多張影像之推論結果。
5. **批次評估**：於「Evaluate」分頁選擇資料夾，執行整批推論並自動產生混淆矩陣與統計。
6. **比對模型效能**：在「Confusion Matrix (History)」檢視不同日期／模型之混淆矩陣快照。

---

### 🏗️ 設計考量

* **純 ASCII 程式註解**：避免 Thonny `UnicodeEncodeError`。
* **單執行緒 GUI + 背景執行緒推論**：保證介面流暢與推論並行。
* **記憶體回收**：大型 NumPy 陣列使用 `with`／`del` 與 `gc.collect()` 額外釋放，以適應 2 GB RAM 限制。
* **再現性**：推論與評估結果皆記錄 JSON；GUI 可復現任一歷史狀態。
* **模組化**：`backend/` 與 `front/` 關注分離，便於單元測試與功能擴充。

---

### 📝 參考與引用

若此專案對您的研究或開發有所幫助，請在論文或報告中引用：

```text
@software{teaman8823_pneumonia_detection_2025,
  author = {Lin, Bing-Hong},
  title  = {Pneumonia Detection on Raspberry Pi 4B},
  year   = {2025},
  url    = {https://github.com/teaman8823/pneumonia_detection}
}
```

---


若對使用方式有任何疑問，或發現錯誤，歡迎開 Issue 與我討論 🙌

