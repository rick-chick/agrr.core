# CLIヘルプ改善サマリー

## 対応完了日
2025-10-19

## 修正内容

### 1. ✅ moves.jsonフォーマットをメインヘルプに追加

**ファイル**: `src/agrr_core/cli.py`

**変更箇所**: Input File Formats セクションに「4. Moves File (JSON)」を追加（191-220行目）

**追加内容**:
```
4. Moves File (JSON) - for 'agrr optimize adjust':
   {
     "moves": [
       {
         "allocation_id": "alloc_001",      // ID from current allocation
         "action": "move",                  // "move", "remove", or "add"
         "to_field_id": "field_2",          // Target field ID
         "to_start_date": "2024-05-15",     // New start date (YYYY-MM-DD)
         "to_area": 12.0                    // Optional: area in m²
       },
       {
         "allocation_id": "alloc_002",
         "action": "remove"                 // Remove allocation
       },
       {
         "action": "add",                   // Add new crop allocation
         "crop_id": "tomato",               // Crop ID from crops.json
         "variety": "Momotaro",             // Optional: variety name
         "to_field_id": "field_1",          // Target field ID
         "to_start_date": "2024-06-01",     // Start date (YYYY-MM-DD)
         "to_area": 15.0                    // Required for add: area in m²
       }
     ]
   }

   Actions:
     - "move": Move existing allocation to different field/date/area
     - "remove": Remove allocation from schedule
     - "add": Add new crop allocation
```

**効果**:
- ✅ 初心者が `agrr --help` だけで moves.json のフォーマットを理解できる
- ✅ 3つのアクション（move, remove, add）すべてを説明
- ✅ 各フィールドの意味をインラインコメントで明示

---

### 2. ✅ README.mdの古いコマンド例を修正

**ファイル**: `README.md`

**修正前**:
```bash
agrr crop crop --query "トマト"  # ❌ cropが2回
agrr optimize-period optimize --crop rice --variety Koshihikari ...  # ❌ 古い形式
```

**修正後**:
```bash
agrr crop --query "トマト"  # ✅ 正しい形式
agrr crop --query "rice Koshihikari" > rice_profile.json  # ✅ 実際の使い方
agrr progress --crop-file rice_profile.json --start-date 2024-05-01 --weather-file weather_data.json
agrr optimize period --crop-file rice_profile.json --evaluation-start 2024-04-01 --evaluation-end 2024-09-30 --weather-file weather_data.json --field-file field_01.json  # ✅ 新しい形式
```

**効果**:
- ✅ コマンドの重複を修正
- ✅ 最新のコマンド形式に統一
- ✅ 実際のワークフロー（crop → progress → optimize）を明示

---

## 検証結果

### 1. メインヘルプの確認
```bash
$ python3 -m agrr_core.cli --help | grep -A 50 "Interaction Rules File"
```

✅ moves.json のフォーマットが正しく表示される

### 2. adjust コマンドの例
```bash
$ python3 -m agrr_core.cli --help | grep -A 5 "Adjust existing allocation"
```

✅ adjust コマンドの例が正しく表示される

### 3. README.mdの確認
```bash
$ head -45 README.md | tail -15
```

✅ 修正後のコマンド例が正しく表示される

---

## ユーザー体験の改善

### 修正前
1. ユーザーが `agrr --help` を見る
2. `agrr optimize adjust` の例を見つける
3. 「moves.jsonってどう書くの？」← **説明がない**
4. `agrr optimize adjust --help` に気づかず諦める

### 修正後
1. ユーザーが `agrr --help` を見る
2. `agrr optimize adjust` の例を見つける
3. Input File Formats セクションで **moves.json のフォーマットを確認**
4. すぐに実装開始できる ✅

---

## 主要な改善点

### 🎯 CLIヘルプだけで完結
- メインヘルプに moves.json のフォーマットを追加
- 3つのアクション（move, remove, add）すべてを説明
- 各フィールドの意味をコメントで明示

### 📚 ドキュメントの一貫性
- README.md のコマンド例を最新形式に統一
- 古い形式（`crop crop`, `optimize-period optimize`）を削除
- 実際のワークフローを反映

### 🚀 即座に使える
- コピー&ペーストですぐに試せる
- 具体的な例（alloc_001, tomato, field_2など）を提示
- オプショナルフィールドを明記

---

## 残っている軽微な改善案（オプション）

以下は今回対応していませんが、将来的に検討できます：

### 1. ドキュメント参照の追加
メインヘルプの末尾に：
```
Documentation:
  docs/guides/ALLOCATION_ADJUST_GUIDE.md - Detailed adjustment guide
  test_data/adjust_moves_example.json - Sample moves file
```

### 2. サンプルファイルへの言及
```
For example files:
  See test_data/ directory for working examples
```

### 3. daemon ヘルプの例の統一
`src/agrr_core/daemon/manager.py` 74行目:
```python
agrr crop --query "トマト Momotaro"  # より具体的に
```

---

## まとめ

✅ **問題1**: moves.json フォーマットがメインヘルプにない → **解決**
✅ **問題2**: README.md に古いコマンド例 → **解決**

CLIユーザーは `agrr --help` だけで：
- 全コマンドの使い方
- 全ファイルフォーマット（moves.json含む）
- 実際の使用例

を理解できるようになりました。

