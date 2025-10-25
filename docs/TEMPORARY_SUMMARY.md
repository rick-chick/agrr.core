## まとめ

### 基本方針
- **閾値チェック**: ViolationCheckerService → 警告表示用
- **収益計算**: YieldImpactAccumulator → コスト換算

### 重複について
- 同じ温度データを2回チェックするが、目的が異なるため許容
- 保守性と独立性を優先
