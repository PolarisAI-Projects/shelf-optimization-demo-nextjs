from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib
import os
import random
import io

# FastAPIアプリケーションを初期化
app = FastAPI()

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.jsアプリのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- データ読み込み ---
# Vercel環境では /var/task/ がカレントディレクトリになることが多いので、
# スクリプトの場所を基準にパスを指定する
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')

try:
    df_base = pd.read_csv(os.path.join(DATA_DIR, '台.csv'))
    df_shelf = pd.read_csv(os.path.join(DATA_DIR, '棚.csv'))
    df_position_initial = pd.read_csv(os.path.join(DATA_DIR, '棚位置.csv'))
    df_master = pd.read_csv(os.path.join(DATA_DIR, '商品.csv'))
    
    print(f"データ読み込み完了:")
    print(f"df_base shape: {df_base.shape}")
    print(f"df_shelf shape: {df_shelf.shape}")
    print(f"df_position_initial shape: {df_position_initial.shape}")
    print(f"df_master shape: {df_master.shape}")
    
    # NaN値をチェック
    print(f"df_base NaN count: {df_base.isnull().sum().sum()}")
    print(f"df_position_initial NaN count: {df_position_initial.isnull().sum().sum()}")
    print(f"df_master NaN count: {df_master.isnull().sum().sum()}")
    
except Exception as e:
    print(f"データ読み込みエラー: {e}")
    # デフォルトの空のDataFrameを作成
    df_base = pd.DataFrame()
    df_shelf = pd.DataFrame()
    df_position_initial = pd.DataFrame()
    df_master = pd.DataFrame()

# --- Streamlitのロジックを関数として再定義 ---
# calculate_layout_score, optimize_step_for_loop, visualize_store_layout
# などの関数をここにペーストします。
# visualize_store_layout は st.pyplot(fig) の代わりに画像を返すように変更します。
def calculate_layout_score(df_pos, df_master, df_base):
    # (元のコードと同じ)
    try:
        score = 0
        if df_pos.empty or df_master.empty or df_base.empty: 
            print("Warning: 空のDataFrameが渡されました")
            return 0
            
        df_merged = pd.merge(df_pos, df_master, on='商品コード', how='left')
        
        if df_merged.empty:
            print("Warning: マージ結果が空です")
            return 0
            
        for (daiban, tandan), group in df_merged.groupby(['台番号', '棚段番号']):
            sorted_group = group.sort_values('棚位置')
            attributes = sorted_group['飲料属性'].to_list()
            product_codes = sorted_group['商品コード'].to_list()
            for i in range(len(attributes) - 1):
                if attributes[i] == attributes[i+1]:
                    score += 1
                    if product_codes[i] == product_codes[i+1]:
                        score += 2
            
            # 台の最大幅をチェック
            dai_base = df_base[df_base['台番号'] == daiban]
            if dai_base.empty:
                print(f"Warning: 台番号 {daiban} が台.csvに見つかりません")
                continue
                
            dai_max_width = dai_base['フェイス数'].iloc[0]
            current_faces = sorted_group['フェース数'].sum()
            empty_width = dai_max_width - current_faces
            if empty_width > 2:
                score -= (empty_width - 2) * 5
                
        print(f"計算されたスコア: {score}")
        return float(score)
        
    except Exception as e:
        print(f"calculate_layout_score エラー: {e}")
        return 0

def optimize_step_for_loop(df_pos: pd.DataFrame, df_master: pd.DataFrame, df_base: pd.DataFrame, current_score: float) -> (pd.DataFrame, float):
    # (元のコードと同じ)
    df_copy = df_pos.copy()
    shelf_counts = df_copy.groupby(['台番号', '棚段番号']).size()
    eligible_shelves = shelf_counts[shelf_counts >= 2].index
    if eligible_shelves.empty: return df_pos, current_score
    daiban, tandan = random.choice(eligible_shelves)
    shelf_df = df_copy[(df_copy['台番号'] == daiban) & (df_copy['棚段番号'] == tandan)]
    indices_to_swap = shelf_df.sample(2).index
    idx1, idx2 = indices_to_swap[0], indices_to_swap[1]
    pos1 = df_copy.loc[idx1, '棚位置']
    pos2 = df_copy.loc[idx2, '棚位置']
    df_copy.loc[idx1, '棚位置'] = pos2
    df_copy.loc[idx2, '棚位置'] = pos1
    new_score = calculate_layout_score(df_copy, df_master, df_base)
    if new_score > current_score:
        return df_copy, new_score
    else:
        return df_pos, current_score

def visualize_shelf_for_api(df_position, daiban_id):
    # API用に特定の台の画像のみを生成する関数
    df_merged = pd.merge(df_position, df_master, on='商品コード', how='left')
    color_map = { 'お茶': 'green', 'コーヒー': 'black', 'コーラ': 'red', '水': 'blue' }
    df_merged['色'] = df_merged['飲料属性'].map(color_map).fillna('grey')

    dai_group = df_merged[df_merged['台番号'] == daiban_id]
    if dai_group.empty:
        return None

    dai_max_width = df_base[df_base['台番号'] == daiban_id]['フェイス数'].iloc[0]
    tandans = sorted(dai_group['棚段番号'].unique())
    num_tandans = len(tandans)
    fig, axes = plt.subplots(nrows=num_tandans, ncols=1, figsize=(12, 1.8 * num_tandans), squeeze=False)

    # ... (visualize_store_layout の描画ロジックをここに移植) ...
    # 省略: 元のコードの for ループ部分をほぼそのまま使用
    for i, tandan in enumerate(tandans):
        ax = axes[i][0]
        tandan_group = dai_group[dai_group['棚段番号'] == tandan]
        ax.set_xlim(0, dai_max_width)
        current_pos = 0
        for _, row in tandan_group.sort_values('棚位置').iterrows():
            face_count = row['フェース数']
            color = row['色']
            attribute = row['飲料属性'] if pd.notna(row['飲料属性']) else '不明'
            rect = patches.Rectangle((current_pos, 0), face_count, 1, linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.8)
            ax.add_patch(rect)
            ax.text(current_pos + face_count / 2, 0.5, f"{attribute}\n({face_count}フェイス)", ha='center', va='center', color='white', fontsize=9, weight='bold')
            current_pos += face_count
        empty_width = dai_max_width - current_pos
        if empty_width > 0:
            rect_empty = patches.Rectangle((current_pos, 0), empty_width, 1, facecolor='none', edgecolor='gray', linestyle='--', linewidth=1)
            ax.add_patch(rect_empty)
            ax.text(current_pos + empty_width / 2, 0.5, "空き", ha='center', va='center', color='gray', fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_ylabel(f'棚段 {tandan}', rotation=0, ha='right', va='center', fontsize=12)
        ax.set_xticks(range(0, dai_max_width + 1))
        ax.set_yticks([])
    axes[-1][0].set_xlabel('フェース位置')
    plt.tight_layout(pad=2.0)

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf

# --- APIエンドポイント定義 ---
@app.get("/api/initial_data")
def get_initial_data():
    """初期データを返す"""
    initial_score = calculate_layout_score(df_position_initial, df_master, df_base)
    
    # NaN値を適切に処理
    position_data = df_position_initial.fillna(0).to_dict('records')
    base_data = df_base.fillna(0).to_dict('records')
    
    # scoreがNaNの場合は0にする
    if pd.isna(initial_score) or np.isnan(initial_score):
        initial_score = 0
    
    return JSONResponse({
        "position": position_data,
        "score": float(initial_score),
        "base_info": base_data
    })

@app.post("/api/optimize")
async def optimize(request: dict):
    """指定された回数だけ最適化を実行する"""
    df_pos = pd.DataFrame(request['position'])
    iterations = request['iterations']

    current_score = calculate_layout_score(df_pos, df_master, df_base)

    for _ in range(iterations):
        df_pos, current_score = optimize_step_for_loop(df_pos, df_master, df_base, current_score)

    # NaN値を適切に処理
    position_data = df_pos.fillna(0).to_dict('records')
    
    # scoreがNaNの場合は0にする
    if pd.isna(current_score) or np.isnan(current_score):
        current_score = 0

    return JSONResponse({
        "position": position_data,
        "score": float(current_score),
    })

@app.post("/api/visualize")
async def visualize(request: dict):
    """現在の棚データから指定された台の画像を生成して返す"""
    df_pos = pd.DataFrame(request['position'])
    daiban_id = request['daiban_id']
    image_buffer = visualize_shelf_for_api(df_pos, daiban_id)
    if image_buffer:
        return StreamingResponse(image_buffer, media_type="image/png")
    return {"error": "Could not generate image"}, 404
