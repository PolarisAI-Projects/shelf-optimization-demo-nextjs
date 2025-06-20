import uvicorn
import os
import sys

# プロジェクトのルートディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # CORSを有効にしてFastAPIサーバーを起動
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True) 
