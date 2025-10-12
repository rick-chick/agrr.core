"""データフロー層間テストパッケージ.

各層間でのデータの移送が正しく行われることを確認するテスト群。

Layer 1: Repository → Field Entity
  - JSONからFieldエンティティへの変換

Layer 2: Field Entity → Request DTO
  - FieldエンティティがDTOに正しく設定される

Layer 3: Request DTO → Interactor
  - Interactorがfieldからdaily_fixed_costを取得し計算に使用

Layer 4: Response DTO
  - ResponseDTOがFieldとコスト情報を保持
"""

