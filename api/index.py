# openpyxlのインストールが必要です: pip install openpyxl
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import os
import random
import io
from typing import Any, Dict, List

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

# --- グローバルデータフレーム ---
# アプリケーション全体で共有されるデータ。アップロードやデモデータ読み込みで更新される。
df_base = pd.DataFrame()
df_shelf = pd.DataFrame()
df_position = pd.DataFrame()
df_master = pd.DataFrame()

# --- データ管理関数 ---
def set_global_dataframes(base, shelf, position, master):
    """グローバルなDataFrameを更新する"""
    global df_base, df_shelf, df_position, df_master
    df_base = base.copy()
    df_shelf = shelf.copy()
    df_position = position.copy()
    df_master = master.copy()
    print("グローバルDataFrameが更新されました。")

@app.on_event("startup")
async def startup_event():
    """起動時にCSVからデータを読み込む（フォールバック）"""
    try:
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
        
        base_df = pd.read_csv(os.path.join(DATA_DIR, '台.csv'))
        shelf_df = pd.read_csv(os.path.join(DATA_DIR, '棚.csv'))
        position_df = pd.read_csv(os.path.join(DATA_DIR, '棚位置.csv'))
        master_df = pd.read_csv(os.path.join(DATA_DIR, '商品.csv'))
        
        set_global_dataframes(base_df, shelf_df, position_df, master_df)
        print("CSVデータから初期読み込み完了。")
    except Exception as e:
        print(f"CSVデータの初期読み込みに失敗: {e}。API経由でのデータ設定が必要です。")

# --- 計算・最適化ロジック（変更なし）---
def calculate_layout_score(df_pos, df_master, df_base):
    try:
        score = 0
        if df_pos.empty or df_master.empty or df_base.empty: 
            return 0
            
        df_merged = pd.merge(df_pos, df_master, on='商品コード', how='left')
        
        if df_merged.empty:
            return 0
        
        # 台を統合した全体レイアウトでの左右分離スコア
        all_positions = []
        for (daiban, tandan), group in df_merged.groupby(['台番号', '棚段番号']):
            sorted_group = group.sort_values('棚位置')
            for _, row in sorted_group.iterrows():
                # 台番号を考慮した絶対位置を計算
                base_offset = (row['台番号'] - 1) * 20  # 台間の仮想オフセット
                absolute_pos = base_offset + row['棚位置']
                all_positions.append({
                    'absolute_pos': absolute_pos,
                    'attribute': row['飲料属性'],
                    'daiban': row['台番号'],
                    'tandan': row['棚段番号']
                })
        
        # 絶対位置でソートして全体の配置を評価
        all_positions.sort(key=lambda x: x['absolute_pos'])
        
        # 左右分離の評価：お茶が左、コーヒーが右に配置されているか
        tea_positions = [p['absolute_pos'] for p in all_positions if p['attribute'] == 'お茶']
        coffee_positions = [p['absolute_pos'] for p in all_positions if p['attribute'] == 'コーヒー']
        
        if tea_positions and coffee_positions:
            tea_max = max(tea_positions)
            coffee_min = min(coffee_positions)
            
            # お茶の最右端がコーヒーの最左端より左にある場合、大幅ボーナス
            if tea_max < coffee_min:
                score += 50  # 完全分離ボーナス
            
            # お茶が左寄り、コーヒーが右寄りの度合いを評価
            tea_avg = sum(tea_positions) / len(tea_positions)
            coffee_avg = sum(coffee_positions) / len(coffee_positions)
            if coffee_avg > tea_avg:
                score += int((coffee_avg - tea_avg) * 2)  # 平均位置差ボーナス
        
        # 台別属性集約評価（台1=お茶優先、台2=コーヒー優先）
        for daiban_id, dai_group in df_merged.groupby('台番号'):
            dai_tea_count = len(dai_group[dai_group['飲料属性'] == 'お茶'])
            dai_coffee_count = len(dai_group[dai_group['飲料属性'] == 'コーヒー'])
            
            if daiban_id == 1:
                # 台1はお茶が多いほど高スコア
                if dai_tea_count > dai_coffee_count:
                    score += (dai_tea_count - dai_coffee_count) * 10
                # お茶のみの場合は大幅ボーナス
                if dai_tea_count > 0 and dai_coffee_count == 0:
                    score += 30
            elif daiban_id == 2:
                # 台2はコーヒーが多いほど高スコア
                if dai_coffee_count > dai_tea_count:
                    score += (dai_coffee_count - dai_tea_count) * 10
                # コーヒーのみの場合は大幅ボーナス
                if dai_coffee_count > 0 and dai_tea_count == 0:
                    score += 30
        
        # 塊の連続性評価（従来の改良版）
        for (daiban, tandan), group in df_merged.groupby(['台番号', '棚段番号']):
            sorted_group = group.sort_values('棚位置')
            attributes = sorted_group['飲料属性'].to_list()
            product_codes = sorted_group['商品コード'].to_list()
            for i in range(len(attributes) - 1):
                if attributes[i] == attributes[i+1]:
                    # 同じ属性が横に並ぶ場合のスコア
                    score += 2
                    # 同一商品コードなら追加ボーナス
                    if product_codes[i] == product_codes[i+1]:
                        score += 3
                else:
                    # 属性が切り替わる場合はペナルティ
                    score -= 2  # ペナルティを強化
            
            dai_base_info = df_base[df_base['台番号'] == daiban]
            if dai_base_info.empty: continue
                
            dai_max_width = dai_base_info['フェイス数'].iloc[0]
            current_faces = sorted_group['フェース数'].sum()
            empty_width = dai_max_width - current_faces
            # 空きスペースのペナルティを大幅に緩和（移動促進のため）
            if empty_width > 8:
                score -= (empty_width - 8) * 2
        
        # 縦方向スコアリング（強化版）
        try:
            for daiban_id, dai_group in df_merged.groupby('台番号'):
                dai_base_local = df_base[df_base['台番号'] == daiban_id]
                max_width = 0
                if not dai_base_local.empty:
                    max_width = int(dai_base_local['フェイス数'].iloc[0])
                else:
                    width_candidates = dai_group.groupby('棚段番号')['フェース数'].sum().astype(int)
                    if not width_candidates.empty:
                       max_width = int(width_candidates.max())

                if max_width == 0: continue

                shelf_rows: dict[int, list[str]] = {}
                for tandan_id, tandan_group in dai_group.groupby('棚段番号'):
                    row_attrs = [''] * max_width
                    if '棚位置' not in tandan_group.columns or 'フェース数' not in tandan_group.columns:
                        continue
                    for _, item in tandan_group.iterrows():
                        start_pos = int(item['棚位置'])
                        faces = int(item['フェース数'])
                        attr = item['飲料属性'] if pd.notna(item['飲料属性']) else ''
                        for p in range(start_pos, min(start_pos + faces, max_width)):
                            row_attrs[p] = attr
                    shelf_rows[int(tandan_id)] = row_attrs

                # 縦方向スコアリングを強化 - より重要視
                if len(shelf_rows) >= 2:
                    tandan_sorted = sorted(shelf_rows.keys())
                    for col in range(max_width):
                        vertical_sequence = []
                        for tandan_id in tandan_sorted:
                            curr_attr = shelf_rows[tandan_id][col]
                            if curr_attr != '':
                                vertical_sequence.append(curr_attr)
                        
                        # 縦方向の連続性を重視したスコアリング
                        if len(vertical_sequence) >= 2:
                            consecutive_count = 0
                            for i in range(len(vertical_sequence) - 1):
                                if vertical_sequence[i] == vertical_sequence[i+1]:
                                    consecutive_count += 1
                                else:
                                    score -= 2  # 縦方向で属性が途切れる場合のペナルティ強化
                            
                            # 縦方向の連続性に高いスコアを付与
                            if consecutive_count > 0:
                                score += consecutive_count * 3  # 縦方向を3倍重視
                                
                            # 全体が同じ属性の場合はボーナススコア
                            if len(set(vertical_sequence)) == 1:
                                score += 8  # ボーナス強化
        except Exception as e:
            print(f"縦方向スコア計算エラー: {e}")

        return float(score)
    except Exception as e:
        print(f"calculate_layout_score エラー: {e}")
        return 0

def _compact_and_update_df(df_to_update: pd.DataFrame):
    compacted_df = pd.DataFrame()
    for (daiban_id, tandan_id), group in df_to_update.groupby(['台番号', '棚段番号']):
        sorted_shelf = group.sort_values('棚位置').copy()
        new_pos = 0
        for idx, row in sorted_shelf.iterrows():
            sorted_shelf.loc[idx, '棚位置'] = new_pos
            new_pos += row['フェース数']
        compacted_df = pd.concat([compacted_df, sorted_shelf])
    return compacted_df

def optimize_greedy(df_pos: pd.DataFrame, df_master_local: pd.DataFrame, df_base_local: pd.DataFrame, max_passes: int = 15) -> tuple[pd.DataFrame, float]:
    current_df = df_pos.copy()
    
    current_score = calculate_layout_score(current_df, df_master_local, df_base_local)

    for pass_num in range(max_passes):
        best_score_in_pass = current_score
        best_df_in_pass = None
        
        item_indices = list(current_df.index)
        for i in range(len(item_indices)):
            for j in range(i + 1, len(item_indices)):
                idx1, idx2 = item_indices[i], item_indices[j]
                row1, row2 = current_df.loc[idx1], current_df.loc[idx2]
                
                temp_df = current_df.copy()
                
                # より柔軟なスワップ条件 - 台を超えた移動も許可
                is_swap_possible = False
                
                # 1. 同じ台・同じ棚段内での横移動
                if row1['台番号'] == row2['台番号'] and row1['棚段番号'] == row2['棚段番号']:
                    is_swap_possible = True
                    
                # 2. 台内または台間での移動を積極的に許可
                else:
                    # フェース数が同じ場合は移動を積極的に許可
                    if row1['フェース数'] == row2['フェース数']:
                        is_swap_possible = True
                    # フェース数が異なる場合でも、差が1以下なら許可
                    elif abs(row1['フェース数'] - row2['フェース数']) <= 1:
                        is_swap_possible = True
                    # 常に移動を許可（属性による改善を期待）
                    else:
                        is_swap_possible = True
                
                if is_swap_possible:
                    # 商品コードのスワップ
                    temp_df.loc[idx1, '商品コード'], temp_df.loc[idx2, '商品コード'] = row2['商品コード'], row1['商品コード']
                    
                    # フェース数が異なる場合の特別処理
                    if row1['フェース数'] != row2['フェース数']:
                        # フェース数もスワップして配置を調整
                        temp_df.loc[idx1, 'フェース数'], temp_df.loc[idx2, 'フェース数'] = row2['フェース数'], row1['フェース数']
                    
                    # 台間移動の場合、属性に基づく改善度を事前評価
                    if row1['台番号'] != row2['台番号']:
                        # マスターデータから属性を取得
                        merged_check = pd.merge(temp_df, df_master_local, on='商品コード', how='left')
                        attr1 = merged_check[merged_check.index == idx1]['飲料属性'].iloc[0] if len(merged_check[merged_check.index == idx1]) > 0 else ''
                        attr2 = merged_check[merged_check.index == idx2]['飲料属性'].iloc[0] if len(merged_check[merged_check.index == idx2]) > 0 else ''
                        
                        # 台1にお茶、台2にコーヒーが移動する場合は優先的に評価
                        priority_move = False
                        if (row1['台番号'] == 1 and attr2 == 'お茶') or (row1['台番号'] == 2 and attr2 == 'コーヒー'):
                            priority_move = True
                        if (row2['台番号'] == 1 and attr1 == 'お茶') or (row2['台番号'] == 2 and attr1 == 'コーヒー'):
                            priority_move = True
                else:
                    continue
                
                temp_df = _compact_and_update_df(temp_df)
                new_score = calculate_layout_score(temp_df, df_master_local, df_base_local)

                if new_score > best_score_in_pass:
                    best_score_in_pass = new_score
                    best_df_in_pass = temp_df

        if best_df_in_pass is None: 
            break
        
        current_df = best_df_in_pass
        current_score = best_score_in_pass
        
        print(f"パス {pass_num + 1}: スコア {current_score:.1f}")

    return current_df, current_score

def calculate_dynamic_base_info(df_position):
    dynamic_base_info = []
    if df_position.empty or '台番号' not in df_position.columns:
        return []
    for daiban_id in sorted(df_position['台番号'].unique()):
        dai_group = df_position[df_position['台番号'] == daiban_id]
        max_faces = 0
        if not dai_group.empty:
            tandan_faces = dai_group.groupby('棚段番号')['フェース数'].sum()
            if not tandan_faces.empty:
                max_faces = tandan_faces.max()
        dynamic_base_info.append({
            '台番号': int(daiban_id), 'フェイス数': int(max_faces), '段数': int(len(dai_group['棚段番号'].unique()))
        })
    return dynamic_base_info

def get_color_for_attribute(attribute):
    color_map = {'お茶': '#15803d', 'コーヒー': '#5d2f0a', '不明': '#9ca3af'}
    return color_map.get(attribute, '#9ca3af')

# --- APIエンドポイント定義 ---
@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    """XLSXファイルをアップロードして、マスターデータを更新する"""
    if not file.filename.endswith('.xlsx'):
        return JSONResponse(status_code=400, content={"error": "XLSXファイルを選択してください。"})
    
    try:
        contents = await file.read()
        with io.BytesIO(contents) as f:
            all_sheets = pd.read_excel(f, sheet_name=None)

        required_sheets = ['台', '棚', '商品', '棚位置']
        if not all(sheet in all_sheets for sheet in required_sheets):
            return JSONResponse(status_code=400, content={"error": f"XLSXには次のシートが必要です: {', '.join(required_sheets)}"})
            
        set_global_dataframes(all_sheets['台'], all_sheets['棚'], all_sheets['棚位置'], all_sheets['商品'])
        return JSONResponse({"message": "データが正常にアップロードされ、更新されました。"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"ファイルの処理中にエラーが発生しました: {str(e)}"})

@app.get("/api/initial_data")
def get_initial_data_endpoint():
    """現在のマスターデータから初期レイアウトを生成して返す"""
    if df_position.empty or df_master.empty:
         return JSONResponse({"error": "データが読み込まれていません。"}, status_code=404)

    df_pos_with_faces = df_position.copy()
    df_pos_with_faces['フェース数'].fillna(1, inplace=True); df_pos_with_faces['フェース数'] = df_pos_with_faces['フェース数'].astype(int)

    base_info = calculate_dynamic_base_info(df_pos_with_faces)
    df_dynamic_base = pd.DataFrame(base_info)
    
    initial_score = calculate_layout_score(df_pos_with_faces, df_master, df_dynamic_base)
    position_data = df_pos_with_faces.fillna(0).to_dict('records')
    
    return JSONResponse({
        "position": position_data,
        "score": float(initial_score if not pd.isna(initial_score) else 0),
        "base_info": base_info
    })

@app.get("/api/demo_data")
def get_demo_data_endpoint():
    """デモデータを生成しグローバル変数を更新後、そのデータを返す"""
    if df_master.empty or df_position.empty:
        return JSONResponse({"error": "マスターデータまたは棚位置の初期読み込みに失敗"}, status_code=500)

    try:
        # データが十分あるかチェック
        tea_count = len(df_master[df_master['飲料属性'] == 'お茶'])
        coffee_count = len(df_master[df_master['飲料属性'] == 'コーヒー'])
        if tea_count < 8 or coffee_count < 8:
            return JSONResponse({
                "error": f"デモデータ作成失敗：お茶{tea_count}種類（8種類以上必要）、コーヒー{coffee_count}種類（8種類以上必要）"
            }, status_code=500)
        
        # デモデータ用のサンプルを確保（台2つ分） - replaceを許可して重複も含める
        import time, random
        seed = int(time.time()) % 10000  # 動的なシード
        random.seed(seed)
        teas = df_master[df_master['飲料属性'] == 'お茶'].sample(n=8, replace=True, random_state=seed)
        coffees = df_master[df_master['飲料属性'] == 'コーヒー'].sample(n=8, replace=True, random_state=seed+1)
        # フェース数を 2〜4 の範囲でランダム生成
        face_counts = [random.randint(2, 4) for _ in range(16)]
    except Exception as e:
        print(f"デモデータサンプリングエラー: {e}")
        return JSONResponse({"error": f"デモデータ作成中にエラーが発生しました: {str(e)}"}, status_code=500)
    
    # 台1: 混在パターン（お茶とコーヒーが混在）
    # 段1: コーヒー2種類 + お茶2種類（混在）
    # 段2: お茶2種類 + コーヒー2種類（混在）
    dai1_shelf1_items = pd.concat([coffees.iloc[0:2], teas.iloc[0:2]]).reset_index(drop=True)
    dai1_shelf2_items = pd.concat([teas.iloc[2:4], coffees.iloc[2:4]]).reset_index(drop=True)
    
    # 台2: より複雑な混在パターン
    # 段1: お茶1種類 + コーヒー1種類 + お茶1種類（混在）
    # 段2: コーヒー2種類 + お茶1種類（混在）
    dai2_shelf1_items = pd.concat([teas.iloc[4:5], coffees.iloc[4:5], teas.iloc[5:6]]).reset_index(drop=True)
    dai2_shelf2_items = pd.concat([coffees.iloc[5:7], teas.iloc[0:1]]).reset_index(drop=True)  # 重複使用を許可

    positions = []
    # 台1の配置
    for i, row in dai1_shelf1_items.iterrows():
        positions.append({'台番号': 1, '棚段番号': 1, '棚位置': i, '商品コード': row['商品コード'], 'フェース数': face_counts[i]})
    for i, row in dai1_shelf2_items.iterrows():
        positions.append({'台番号': 1, '棚段番号': 2, '棚位置': i, '商品コード': row['商品コード'], 'フェース数': face_counts[i+4]})
    
    # 台2の配置
    for i, row in dai2_shelf1_items.iterrows():
        positions.append({'台番号': 2, '棚段番号': 1, '棚位置': i, '商品コード': row['商品コード'], 'フェース数': face_counts[i+8]})
    for i, row in dai2_shelf2_items.iterrows():
        positions.append({'台番号': 2, '棚段番号': 2, '棚位置': i, '商品コード': row['商品コード'], 'フェース数': face_counts[i+11]})

    demo_pos = pd.DataFrame(positions)
    demo_pos = _compact_and_update_df(demo_pos)

    demo_base_info = calculate_dynamic_base_info(demo_pos)
    demo_base = pd.DataFrame(demo_base_info)
    
    # 各台に空きスペースを設けるため、フェイス数を拡張
    for i, base_row in demo_base.iterrows():
        demo_base.loc[i, 'フェイス数'] = int(base_row['フェイス数']) + 6  # 6フェース分の空きを追加
    
    demo_shelf = demo_pos[['台番号', '棚段番号']].drop_duplicates().reset_index(drop=True)

    set_global_dataframes(demo_base, demo_shelf, demo_pos, df_master)
    
    return get_initial_data_endpoint()

@app.post("/api/optimize")
async def optimize(request: dict):
    df_pos = pd.DataFrame(request['position'])
    
    # グローバル変数のローカルコピーを作成して競合状態を防ぐ
    if df_master.empty:
        return JSONResponse({"error": "マスターデータが読み込まれていません。"}, status_code=404)
    
    df_master_local = df_master.copy()
    
    dynamic_base_data = calculate_dynamic_base_info(df_pos)
    df_dynamic_base = pd.DataFrame(dynamic_base_data)
    
    df_pos, current_score = optimize_greedy(df_pos, df_master_local, df_dynamic_base)

    position_data = df_pos.fillna(0).to_dict('records')
    
    return JSONResponse({
        "position": position_data,
        "score": float(current_score if not pd.isna(current_score) else 0),
    })

@app.post("/api/layout_data")
async def get_layout_data(request: dict):
    df_pos = pd.DataFrame(request['position'])
    daiban_id = request['daiban_id']
    
    df_merged = pd.merge(df_pos, df_master, on='商品コード', how='left')
    dai_group = df_merged[df_merged['台番号'] == daiban_id]
    if dai_group.empty: return JSONResponse({"error": "Could not generate layout data"}, status_code=404)

    dynamic_base_data = calculate_dynamic_base_info(df_pos)
    dai_base_info = next((item for item in dynamic_base_data if item['台番号'] == daiban_id), None)
    if dai_base_info is None: return JSONResponse({"error": "Could not find base info"}, status_code=404)
        
    dai_max_width = dai_base_info['フェイス数']
    layout_data: Dict[str, Any] = {'daiban_id': int(daiban_id), 'max_width': int(dai_max_width), 'shelves': []}
    
    for tandan in sorted(dai_group['棚段番号'].unique()):
        tandan_group = dai_group[dai_group['棚段番号'] == tandan]
        shelf_data: Dict[str, Any] = {'tandan': int(tandan), 'items': []}
        
        current_pos = 0
        for _, row in tandan_group.sort_values('棚位置').iterrows():
            face_count = int(row['フェース数'])
            attribute = row['飲料属性'] if pd.notna(row['飲料属性']) else '不明'
            
            items_list: List[Dict[str, Any]] = shelf_data['items']
            items_list.append({
                'start_pos': current_pos, 'face_count': face_count,
                'attribute': attribute, 'color': get_color_for_attribute(attribute)
            })
            current_pos += face_count
        
        if int(dai_max_width) - current_pos > 0:
            shelf_data['empty_space'] = {'start_pos': current_pos, 'width': int(dai_max_width) - current_pos}
        
        shelves_list: List[Dict[str, Any]] = layout_data['shelves']
        shelves_list.append(shelf_data)
    
    return JSONResponse(layout_data)
