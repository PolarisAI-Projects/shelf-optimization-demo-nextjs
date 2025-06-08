from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import os
import random

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

def calculate_layout_score(df_pos, df_master, df_base):
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

def optimize_step_for_loop(df_pos: pd.DataFrame, df_master: pd.DataFrame, df_base: pd.DataFrame, current_score: float) -> tuple[pd.DataFrame, float]:
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

def get_shelf_layout_data(df_position, daiban_id):
    """特定の台の棚配置データを計算してJSONで返す"""
    df_merged = pd.merge(df_position, df_master, on='商品コード', how='left')
    
    dai_group = df_merged[df_merged['台番号'] == daiban_id]
    if dai_group.empty:
        return None

    # 動的にフェース数を計算
    dynamic_base_data = calculate_dynamic_base_info(df_position)
    dai_base_info = next((item for item in dynamic_base_data if item['台番号'] == daiban_id), None)
    
    if dai_base_info is None:
        print(f"Warning: 台番号 {daiban_id} のbase情報が見つかりません")
        return None
        
    dai_max_width = dai_base_info['フェイス数']
    tandans = sorted(dai_group['棚段番号'].unique())
    
    layout_data = {
        'daiban_id': int(daiban_id),
        'max_width': int(dai_max_width),
        'shelves': []
    }
    
    for tandan in tandans:
        tandan_group = dai_group[dai_group['棚段番号'] == tandan]
        shelf_data = {
            'tandan': int(tandan),
            'items': []
        }
        
        current_pos = 0
        for _, row in tandan_group.sort_values('棚位置').iterrows():
            face_count = int(row['フェース数'])
            attribute = row['飲料属性'] if pd.notna(row['飲料属性']) else '不明'
            
            item_data = {
                'start_pos': current_pos,
                'face_count': face_count,
                'attribute': attribute,
                'color': get_color_for_attribute(attribute)
            }
            shelf_data['items'].append(item_data)
            current_pos += face_count
        
        # 空きスペースの計算
        empty_width = int(dai_max_width) - current_pos
        if empty_width > 0:
            shelf_data['empty_space'] = {
                'start_pos': current_pos,
                'width': empty_width
            }
        
        layout_data['shelves'].append(shelf_data)
    
    return layout_data

def get_color_for_attribute(attribute):
    """飲料属性に応じた色を返す"""
    color_map = {
        'お茶': '#15803d',      # 深い緑茶色
        'コーヒー': '#5d2f0a',   # より黒っぽいコーヒーブラウン
        '不明': '#9ca3af'       # gray-400
    }
    return color_map.get(attribute, '#9ca3af')

def calculate_dynamic_base_info(df_position):
    """棚位置データから台ごとの動的なフェース数を計算"""
    dynamic_base_info = []
    
    # 台ごとにグループ化
    for daiban_id in sorted(df_position['台番号'].unique()):
        dai_group = df_position[df_position['台番号'] == daiban_id]
        
        # 台内の各段ごとのフェース数合計を計算
        max_faces = 0
        for tandan in dai_group['棚段番号'].unique():
            tandan_group = dai_group[dai_group['棚段番号'] == tandan]
            tandan_faces = int(tandan_group['フェース数'].sum())  # intに明示的変換
            max_faces = max(max_faces, tandan_faces)
        
        # 動的なbase_infoを作成（すべての値をPython標準型に変換）
        dynamic_base_info.append({
            '台番号': int(daiban_id),
            'フェイス数': int(max_faces),
            '台高さ': int(1200),  # デフォルト値
            '台幅': int(900 + (int(max_faces) * 20)),  # フェース数に基づく推定値
            '台奥行': int(730),   # デフォルト値
            '段数': int(len(dai_group['棚段番号'].unique()))
        })
    
    return dynamic_base_info

# --- APIエンドポイント定義 ---
@app.get("/api/initial_data")
def get_initial_data():
    """初期データを返す"""
    # 動的にbase_infoを計算
    dynamic_base_data = calculate_dynamic_base_info(df_position_initial)
    
    # 動的base_infoを使用してスコア計算（元のdf_baseの代わりに使用）
    df_dynamic_base = pd.DataFrame(dynamic_base_data)
    initial_score = calculate_layout_score(df_position_initial, df_master, df_dynamic_base)
    
    # NaN値を適切に処理
    position_data = df_position_initial.fillna(0).to_dict('records')
    
    # scoreがNaNの場合は0にする
    if pd.isna(initial_score) or np.isnan(initial_score):
        initial_score = 0
    
    print(f"動的に計算されたbase_info: {dynamic_base_data}")
    
    return JSONResponse({
        "position": position_data,
        "score": float(initial_score),
        "base_info": dynamic_base_data
    })

@app.post("/api/optimize")
async def optimize(request: dict):
    """指定された回数だけ最適化を実行する"""
    df_pos = pd.DataFrame(request['position'])
    iterations = request['iterations']

    # 動的base_infoを計算
    dynamic_base_data = calculate_dynamic_base_info(df_pos)
    df_dynamic_base = pd.DataFrame(dynamic_base_data)
    
    current_score = calculate_layout_score(df_pos, df_master, df_dynamic_base)

    for _ in range(iterations):
        df_pos, current_score = optimize_step_for_loop(df_pos, df_master, df_dynamic_base, current_score)

    # NaN値を適切に処理
    position_data = df_pos.fillna(0).to_dict('records')
    
    # scoreがNaNの場合は0にする
    if pd.isna(current_score) or np.isnan(current_score):
        current_score = 0

    return JSONResponse({
        "position": position_data,
        "score": float(current_score),
    })

@app.post("/api/layout_data")
async def get_layout_data(request: dict):
    """現在の棚データから指定された台のレイアウトデータを返す"""
    df_pos = pd.DataFrame(request['position'])
    daiban_id = request['daiban_id']
    layout_data = get_shelf_layout_data(df_pos, daiban_id)
    
    if layout_data:
        return JSONResponse(layout_data)
    else:
        return JSONResponse({"error": "Could not generate layout data"}, status_code=404)
