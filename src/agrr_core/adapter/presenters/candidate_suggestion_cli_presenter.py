"""
候補リスト提示CLI Presenter

このモジュールは候補リスト提示機能のCLI Presenterを実装します。
Table形式とJSON形式の両方の出力をサポートします。
"""
import json
from typing import Optional
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType

class CandidateSuggestionCliPresenter:
    """
    候補リスト提示CLI Presenter
    
    Table形式とJSON形式の両方の出力をサポートします。
    """
    
    def __init__(self):
        """初期化"""
        self.output_format = "table"  # デフォルトはTable形式
    
    def present(self, response: CandidateSuggestionResponseDTO, output_path: str) -> None:
        """
        候補リスト提示結果を出力
        
        Args:
            response: 候補リスト提示レスポンス
            output_path: 出力ファイルパス
        """
        if self.output_format == "table":
            self._present_table_format(response, output_path)
        elif self.output_format == "json":
            self._present_json_format(response, output_path)
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}")

    def _present_table_format(self, response: CandidateSuggestionResponseDTO, output_path: str) -> None:
        """
        Table形式で出力
        
        Args:
            response: 候補リスト提示レスポンス
            output_path: 出力ファイルパス
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("候補リスト提示結果\n")
            f.write("=" * 50 + "\n\n")
            
            if not response.success:
                f.write(f"エラー: {response.message}\n")
                return
            
            if not response.candidates:
                f.write("候補が見つかりませんでした。\n")
                return
            
            f.write(f"生成された候補数: {len(response.candidates)}\n")
            f.write(f"メッセージ: {response.message}\n\n")
            
            # 候補を圃場ごとにグループ化
            field_candidates = {}
            for candidate in response.candidates:
                if candidate.field_id not in field_candidates:
                    field_candidates[candidate.field_id] = []
                field_candidates[candidate.field_id].append(candidate)
            
            # 圃場ごとに出力
            for field_id, candidates in field_candidates.items():
                f.write(f"圃場: {field_id}\n")
                f.write("-" * 30 + "\n")
                
                # 利益順でソート
                candidates.sort(key=lambda c: c.expected_profit, reverse=True)
                
                for i, candidate in enumerate(candidates, 1):
                    f.write(f"  候補 {i}:\n")
                    f.write(f"    タイプ: {self._get_candidate_type_display(candidate.candidate_type)}\n")
                    f.write(f"    開始日: {candidate.start_date.strftime('%Y-%m-%d')}\n")
                    f.write(f"    面積: {candidate.area:.2f} m²\n")
                    f.write(f"    期待利益: ¥{candidate.expected_profit:,.0f}\n")
                    
                    if candidate.candidate_type == CandidateType.INSERT:
                        f.write(f"    作物: {candidate.crop_id}\n")
                    elif candidate.candidate_type == CandidateType.MOVE:
                        f.write(f"    移動元配分: {candidate.allocation_id}\n")
                    
                    f.write("\n")
                
                f.write("\n")

    def _present_json_format(self, response: CandidateSuggestionResponseDTO, output_path: str) -> None:
        """
        JSON形式で出力
        
        Args:
            response: 候補リスト提示レスポンス
            output_path: 出力ファイルパス
        """
        # レスポンスを辞書形式に変換
        output_data = response.to_dict()
        
        # JSON形式で出力
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def _get_candidate_type_display(self, candidate_type: CandidateType) -> str:
        """
        候補タイプの表示文字列を取得
        
        Args:
            candidate_type: 候補タイプ
            
        Returns:
            str: 表示文字列
        """
        if candidate_type == CandidateType.INSERT:
            return "新しい作物挿入"
        elif candidate_type == CandidateType.MOVE:
            return "既存作物移動"
        else:
            return str(candidate_type.value)
