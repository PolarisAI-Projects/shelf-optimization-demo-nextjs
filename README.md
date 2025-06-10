# 棚割り最適化エンジン

飲料商品の棚割り配置を最適化するWebアプリケーションです。お茶とコーヒーの属性に基づいて、効率的な商品配置を自動計算します。

## 🚀 技術スタック

- **フロントエンド**: Next.js 15.3.3 + TypeScript + Tailwind CSS
- **バックエンド**: Python FastAPI + pandas + matplotlib
- **デプロイ**: Vercel (Next.js + Python Serverless Functions)

## 📋 機能概要

### 🎯 主要機能
- **デモデータ読み込み**: サンプルデータで即座に動作確認
- **Excelファイルアップロード**: 独自データでの最適化実行
- **リアルタイム最適化**: グリーディアルゴリズムによる配置最適化
- **視覚化**: 台・棚・商品配置の直感的な表示
- **結果エクスポート**: 最適化結果のExcelダウンロード

### 📊 対応データ形式
- **台.csv**: 台番号、フェイス数、段数
- **棚.csv**: 台番号、棚段番号
- **商品.csv**: 商品コード、商品名、飲料属性（お茶/コーヒー）
- **棚位置.csv**: 台番号、棚段番号、棚位置、商品コード、フェース数

## 🧮 最適化アルゴリズム

### アルゴリズム概要
**グリーディ最適化アルゴリズム**を採用し、商品配置の段階的改善を行います。

### 📈 スコアリング体系

#### 1. **左右分離スコア（最重要）**
```python
# お茶を左側、コーヒーを右側に配置
if tea_max_position < coffee_min_position:
    score += 50  # 完全分離ボーナス

# 平均位置による評価
if coffee_avg_position > tea_avg_position:
    score += (coffee_avg - tea_avg) * 2
```

#### 2. **台別属性集約スコア**
```python
# 台1: お茶優先配置
if daiban_id == 1 and tea_count > coffee_count:
    score += (tea_count - coffee_count) * 10
    if coffee_count == 0:  # お茶のみ
        score += 30

# 台2: コーヒー優先配置  
if daiban_id == 2 and coffee_count > tea_count:
    score += (coffee_count - tea_count) * 10
    if tea_count == 0:  # コーヒーのみ
        score += 30
```

#### 3. **横方向連続性スコア**
```python
# 同じ属性が隣接する場合
if attributes[i] == attributes[i+1]:
    score += 2
    if product_codes[i] == product_codes[i+1]:
        score += 3  # 同一商品ボーナス
else:
    score -= 2  # 属性切り替えペナルティ
```

#### 4. **縦方向連続性スコア（強化）**
```python
# 縦方向の同一属性配置
for consecutive_count in vertical_sequence:
    score += consecutive_count * 3  # 横方向の3倍重視

# 縦一列が同じ属性の場合
if len(set(vertical_sequence)) == 1:
    score += 8  # 高ボーナス
```

### 🔄 最適化プロセス

#### **Phase 1: 初期化**
```python
current_score = calculate_layout_score(initial_layout)
no_improvement_count = 0
```

#### **Phase 2: 反復改善（最大15パス）**
```python
for pass_num in range(max_passes=15):
    best_improvement = None
    
    # 全商品ペアの組み合わせを評価
    for item1, item2 in all_combinations:
        if is_swap_beneficial(item1, item2):
            new_layout = swap_items(item1, item2)
            new_score = calculate_layout_score(new_layout)
            
            if new_score > current_score:
                best_improvement = (new_layout, new_score)
    
    # 改善があれば適用、なければ早期終了判定
    if best_improvement:
        current_layout, current_score = best_improvement
        no_improvement_count = 0
    else:
        no_improvement_count += 1
        if no_improvement_count >= 2:
            break  # 早期終了
```

#### **Phase 3: スワップ条件**
```python
def is_swap_beneficial(item1, item2):
    # 1. 同一台・同一棚段内での移動
    if same_shelf(item1, item2):
        return True
    
    # 2. フェース数による制約
    if abs(item1.faces - item2.faces) <= 1:
        return True
    
    # 3. 属性改善による移動
    if improves_attribute_separation(item1, item2):
        return True
    
    return False
```

### ⚡ パフォーマンス最適化

#### **計算量削減**
- **早期終了**: 2回連続改善なしで終了
- **スワップ制約**: フェース数差による制限
- **属性優先**: 台1→お茶、台2→コーヒーの移動を優先評価

#### **Vercel設定**
```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 300,  // 5分タイムアウト
      "memory": 1024       // 1GB メモリ
    }
  }
}
```

### 📊 最適化結果の評価指標

1. **分離度**: お茶とコーヒーの左右分離状況
2. **集約度**: 台別の属性集中度
3. **連続性**: 同一属性・商品の隣接度
4. **効率性**: 空きスペースの最小化

## 🛠 開発・デプロイ

### ローカル開発
```bash
# フロントエンド起動
npm run dev

# バックエンド起動  
python ./start_api.py
```

### 本番デプロイ
```bash
git push origin main  # Vercel自動デプロイ
```

## 📁 プロジェクト構造

```
├── src/app/                 # Next.js App Router
│   ├── page.tsx            # メインページ
│   ├── components/         # React コンポーネント
│   └── utils/api.ts        # API通信ユーティリティ
├── api/                    # Python FastAPI
│   ├── index.py           # メインAPIファイル
│   └── data/              # サンプルCSVデータ
├── vercel.json            # Vercel設定
└── requirements.txt       # Python依存関係
```

## 🎯 使用方法

1. **デモデータ読み込み**: 「デモデータを読み込む」ボタンクリック
2. **最適化実行**: 「最適化を実行」ボタンクリック  
3. **結果確認**: 視覚化された配置とスコアを確認
4. **エクスポート**: 「結果をダウンロード」でExcel出力

## 📈 今後の拡張予定

- **多属性対応**: お茶・コーヒー以外の商品カテゴリ
- **制約条件追加**: 商品間の相性・売上データ連携
- **AI最適化**: 機械学習による配置パターン学習
- **リアルタイム更新**: 在庫変動に応じた動的再配置
