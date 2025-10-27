"""
候補リスト提示Interactor

このモジュールは候補リスト提示機能のビジネスロジックを実装します。
既存の最適化処理に独立した候補提示機能を提供します。
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from agrr_core.usecase.dto.candidate_suggestion_request_dto import CandidateSuggestionRequestDTO
from agrr_core.usecase.dto.candidate_suggestion_response_dto import CandidateSuggestionResponseDTO
from agrr_core.entity.entities.candidate_suggestion_entity import CandidateSuggestion, CandidateType
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.entity.value_objects.optimization_objective import OptimizationObjective
from agrr_core.usecase.interactors.growth_period_optimize_interactor import GrowthPeriodOptimizeInteractor
from agrr_core.usecase.services.violation_checker_service import ViolationCheckerService
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_gateway import CropGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway


class CandidateSuggestionInteractor:
    """
    候補リスト提示Interactor
    
    圃場ごとに利益最高の挿入可能な候補を提示します。
    新しい作物挿入候補と既存作物移動候補の両方をサポートします。
    """
    
    def __init__(
        self,
        allocation_result_gateway: AllocationResultGateway,
        field_gateway: FieldGateway,
        crop_gateway: CropGateway,
        weather_gateway: WeatherGateway,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None
    ):
        """
        初期化
        
        Args:
            allocation_result_gateway: 最適化結果ゲートウェイ
            field_gateway: 圃場ゲートウェイ
            crop_gateway: 作物ゲートウェイ
            weather_gateway: 気象ゲートウェイ
            interaction_rule_gateway: 相互作用ルールゲートウェイ（オプション）
        """
        self._allocation_result_gateway = allocation_result_gateway
        self._field_gateway = field_gateway
        self._crop_gateway = crop_gateway
        self._weather_gateway = weather_gateway
        self._interaction_rule_gateway = interaction_rule_gateway
        
        # 既存のInteractorを再利用
        self._growth_period_optimizer = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            interaction_rule_gateway=interaction_rule_gateway
        )
        
        # ViolationCheckerServiceは後でinteraction rulesと共に初期化
        self._violation_checker = None
        
        # パフォーマンス最適化のためのキャッシュ
        self._gdd_candidates_cache: Dict[str, List[Any]] = {}
        self._crop_profiles_cache: Dict[str, Any] = {}
    
    async def execute(self, request: CandidateSuggestionRequestDTO) -> CandidateSuggestionResponseDTO:
        """
        候補リスト提示を実行
        
        Args:
            request: 候補リスト提示リクエスト
            
        Returns:
            CandidateSuggestionResponseDTO: 候補リスト提示レスポンス
        """
        try:
            # 1. 既存の最適化結果を取得
            allocation_result = await self._allocation_result_gateway.get()
            if not allocation_result:
                return CandidateSuggestionResponseDTO(
                    candidates=[],
                    success=False,
                    message="Failed to load current optimization result"
                )
            
            # 2. 必要なデータを取得
            fields = await self._field_gateway.get_all()
            crops = await self._crop_gateway.get_all()
            weather_data = await self._weather_gateway.get()
            
            # 3. Interaction rulesを読み込んでviolation checkerを初期化
            if self._interaction_rule_gateway:
                try:
                    from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService
                    interaction_rules = await self._interaction_rule_gateway.get_rules()
                    interaction_rule_service = InteractionRuleService(rules=interaction_rules)
                    self._violation_checker = ViolationCheckerService(
                        interaction_rule_service=interaction_rule_service
                    )
                except Exception as e:
                    # Interaction rulesの読み込みに失敗した場合は警告のみ
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to load interaction rules: {e}")
                    self._violation_checker = ViolationCheckerService()
            else:
                self._violation_checker = ViolationCheckerService()
            
            if not fields:
                return CandidateSuggestionResponseDTO(
                    candidates=[],
                    success=False,
                    message="No fields found"
                )
            
            if not crops:
                return CandidateSuggestionResponseDTO(
                    candidates=[],
                    success=False,
                    message="No crops found"
                )
            
            if not weather_data:
                return CandidateSuggestionResponseDTO(
                    candidates=[],
                    success=False,
                    message="No weather data found"
                )
            
            # 3. 対象作物の存在確認
            target_crop = next((c.crop for c in crops if c.crop.crop_id == request.target_crop_id), None)
            if not target_crop:
                return CandidateSuggestionResponseDTO(
                    candidates=[],
                    success=False,
                    message=f"Target crop not found: {request.target_crop_id}"
                )
            
            # 4. 候補を生成
            candidates = await self._generate_candidates(
                allocation_result=allocation_result,
                fields=fields,
                crops=crops,
                target_crop=target_crop,
                weather_data=weather_data,
                planning_start=request.planning_period_start,
                planning_end=request.planning_period_end
            )
            
            # 5. 圃場ごとの最良候補を選択
            best_candidates = self._select_best_candidates_per_field(candidates)
            
            return CandidateSuggestionResponseDTO(
                candidates=best_candidates,
                success=True,
                message=f"Successfully generated {len(best_candidates)} candidates"
            )
            
        except Exception as e:
            import traceback
            return CandidateSuggestionResponseDTO(
                candidates=[],
                success=False,
                message=f"Error generating candidates: {str(e)}\n{traceback.format_exc()}"
            )
    
    async def _generate_candidates(
        self,
        allocation_result: Any,
        fields: List[Field],
        crops: List[Crop],
        target_crop: Crop,
        weather_data: List[Any],
        planning_start: datetime,
        planning_end: datetime
    ) -> List[CandidateSuggestion]:
        """
        候補を生成
        
        Args:
            allocation_result: 既存の最適化結果
            fields: 圃場リスト
            crops: 作物リスト
            target_crop: 対象作物
            weather_data: 気象データ
            planning_start: 計画開始日
            planning_end: 計画終了日
            
        Returns:
            List[CandidateSuggestion]: 生成された候補リスト
        """
        candidates = []
        
        # 1. 新しい作物挿入候補を生成
        insert_candidates = await self._generate_insert_candidates(
            fields=fields,
            target_crop=target_crop,
            weather_data=weather_data,
            planning_start=planning_start,
            planning_end=planning_end,
            existing_allocations=self._extract_existing_allocations(allocation_result)
        )
        candidates.extend(insert_candidates)
        
        # 2. 既存作物移動候補を生成
        move_candidates = await self._generate_move_candidates(
            allocation_result=allocation_result,
            fields=fields,
            crops=crops,
            weather_data=weather_data,
            planning_start=planning_start,
            planning_end=planning_end
        )
        candidates.extend(move_candidates)
        
        return candidates
    
    async def _generate_insert_candidates(
        self,
        fields: List[Field],
        target_crop: Crop,
        weather_data: List[Any],
        planning_start: datetime,
        planning_end: datetime,
        existing_allocations: List[CropAllocation]
    ) -> List[CandidateSuggestion]:
        """
        新しい作物挿入候補を生成
        
        Args:
            fields: 圃場リスト
            target_crop: 対象作物
            weather_data: 気象データ
            planning_start: 計画開始日
            planning_end: 計画終了日
            existing_allocations: 既存の配分
            
        Returns:
            List[CandidateSuggestion]: 挿入候補リスト
        """
        candidates = []
        
        for field in fields:
            # 圃場の利用可能な期間を計算
            available_periods = self._calculate_available_periods(
                field=field,
                existing_allocations=existing_allocations,
                planning_start=planning_start,
                planning_end=planning_end
            )
            
            for start_date, end_date in available_periods:
                # GDD候補を生成
                gdd_candidates = await self._get_gdd_candidates(
                    field=field,
                    crop=target_crop,
                    weather_data=weather_data,
                    start_date=start_date,
                    end_date=end_date
                )
                
                for gdd_candidate in gdd_candidates:
                    # 利益を計算
                    profit = await self._calculate_profit(
                        field=field,
                        crop=target_crop,
                        allocation=gdd_candidate,
                        weather_data=weather_data
                    )
                    
                    # 候補を作成
                    candidate = CandidateSuggestion(
                        field_id=field.field_id,
                        candidate_type=CandidateType.INSERT,
                        crop_id=target_crop.crop_id,
                        start_date=gdd_candidate.start_date,
                        area=gdd_candidate.area_used,
                        expected_profit=profit,
                        move_instruction=None
                    )
                    
                    # Interaction rulesの違反チェック
                    if self._is_candidate_feasible(candidate, existing_allocations, field, target_crop):
                        candidates.append(candidate)
        
        return candidates
    
    async def _generate_move_candidates(
        self,
        allocation_result: Any,
        fields: List[Field],
        crops: List[Crop],
        weather_data: List[Any],
        planning_start: datetime,
        planning_end: datetime
    ) -> List[CandidateSuggestion]:
        """
        既存作物移動候補を生成
        
        Args:
            allocation_result: 既存の最適化結果
            fields: 圃場リスト
            crops: 作物リスト
            weather_data: 気象データ
            planning_start: 計画開始日
            planning_end: 計画終了日
            
        Returns:
            List[CandidateSuggestion]: 移動候補リスト
        """
        candidates = []
        
        # 既存の配分を取得
        existing_allocations = self._extract_existing_allocations(allocation_result)
        
        for allocation in existing_allocations:
            # 現在の圃場以外の圃場を対象とする
            other_fields = [f for f in fields if f.field_id != allocation.field.field_id]
            
            for target_field in other_fields:
                # 移動可能な期間を計算
                available_periods = self._calculate_available_periods(
                    field=target_field,
                    existing_allocations=[a for a in existing_allocations if a.field.field_id == target_field.field_id],
                    planning_start=planning_start,
                    planning_end=planning_end
                )
                
                for start_date, end_date in available_periods:
                    # 移動後の利益を計算
                    profit = await self._calculate_move_profit(
                        source_allocation=allocation,
                        target_field=target_field,
                        new_start_date=start_date,
                        weather_data=weather_data
                    )
                    
                    # MoveInstructionを作成
                    move_instruction = MoveInstruction(
                        allocation_id=allocation.allocation_id,
                        action=MoveAction.MOVE,
                        to_field_id=target_field.field_id,
                        to_start_date=start_date,
                        to_area=allocation.area_used
                    )
                    
                    # 候補を作成
                    candidate = CandidateSuggestion(
                        field_id=target_field.field_id,
                        candidate_type=CandidateType.MOVE,
                        allocation_id=allocation.allocation_id,
                        start_date=start_date,
                        area=allocation.area_used,
                        expected_profit=profit,
                        move_instruction=move_instruction
                    )
                    
                    candidates.append(candidate)
        
        return candidates
    
    def _select_best_candidates_per_field(self, candidates: List[CandidateSuggestion]) -> List[CandidateSuggestion]:
        """
        圃場ごとの最良候補を選択
        
        Args:
            candidates: 全候補リスト
            
        Returns:
            List[CandidateSuggestion]: 圃場ごとの最良候補リスト
        """
        field_candidates = {}
        
        for candidate in candidates:
            if candidate.field_id not in field_candidates:
                field_candidates[candidate.field_id] = candidate
            elif candidate.expected_profit > field_candidates[candidate.field_id].expected_profit:
                field_candidates[candidate.field_id] = candidate
        
        return list(field_candidates.values())
    
    def _extract_existing_allocations(self, allocation_result: Any) -> List[CropAllocation]:
        """
        既存の最適化結果から配分を抽出
        
        Args:
            allocation_result: 最適化結果
            
        Returns:
            List[CropAllocation]: 既存の配分リスト
        """
        allocations = []
        
        if hasattr(allocation_result, 'field_schedules'):
            for field_schedule in allocation_result.field_schedules:
                if hasattr(field_schedule, 'allocations'):
                    allocations.extend(field_schedule.allocations)
        
        return allocations
    
    def _calculate_available_periods(
        self,
        field: Field,
        existing_allocations: List[CropAllocation],
        planning_start: datetime,
        planning_end: datetime
    ) -> List[tuple]:
        """
        圃場の利用可能な期間を計算（fallow periodを考慮）
        
        Args:
            field: 圃場
            existing_allocations: 既存の配分
            planning_start: 計画開始日
            planning_end: 計画終了日
            
        Returns:
            List[tuple]: 利用可能な期間のリスト (start_date, end_date)
        """
        from datetime import timedelta
        
        # 既存の配分の期間を取得（fallow periodを含む）
        occupied_periods = []
        for allocation in existing_allocations:
            if allocation.field.field_id == field.field_id:
                # fallow periodを考慮して終了日を計算
                effective_end_date = allocation.completion_date + timedelta(
                    days=field.fallow_period_days
                )
                occupied_periods.append((allocation.start_date, effective_end_date))
        
        # 利用可能な期間を計算
        available_periods = []
        current_start = planning_start
        
        # 既存の配分を開始日でソート
        occupied_periods.sort(key=lambda x: x[0])
        
        for occupied_start, occupied_end in occupied_periods:
            if current_start < occupied_start:
                available_periods.append((current_start, occupied_start))
            current_start = max(current_start, occupied_end)
        
        # 最後の期間
        if current_start < planning_end:
            available_periods.append((current_start, planning_end))
        
        return available_periods
    
    def _is_candidate_feasible(
        self,
        candidate: CandidateSuggestion,
        existing_allocations: List[CropAllocation],
        field: Field,
        target_crop: Crop
    ) -> bool:
        """
        候補がinteraction rulesに違反していないかをチェック
        
        Args:
            candidate: チェック対象の候補
            existing_allocations: 既存の配分
            field: 圃場
            target_crop: 対象作物
            
        Returns:
            bool: 候補が実行可能かどうか
        """
        # Violation checkerが初期化されていない場合はスキップ
        if self._violation_checker is None:
            return True
        
        # 同じ圃場の既存配分を取得
        field_allocations = [
            alloc for alloc in existing_allocations 
            if alloc.field.field_id == field.field_id
        ]
        
        # 候補をCropAllocationに変換（簡易版）
        from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
        from datetime import timedelta
        
        # 簡易的なCropAllocationを作成（violation checker用）
        candidate_allocation = CropAllocation(
            allocation_id="temp_candidate",
            field=field,
            crop=target_crop,
            area_used=candidate.area,
            start_date=candidate.start_date,
            completion_date=candidate.start_date + timedelta(days=90),  # 仮の期間
            growth_days=90,
            accumulated_gdd=0.0,
            total_cost=0.0,
            expected_revenue=0.0,
            profit=0.0
        )
        
        # 各既存配分との違反チェック
        for existing_allocation in field_allocations:
            violations = self._violation_checker.check_violations(
                allocation=candidate_allocation,
                previous_allocation=existing_allocation,
                all_allocations=existing_allocations
            )
            
            # エラーレベルの違反がある場合は候補を除外
            if not self._violation_checker.is_feasible(violations):
                return False
        
        return True
    
    async def _get_gdd_candidates(
        self,
        field: Field,
        crop: Crop,
        weather_data: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[Any]:
        """
        GDD候補を取得（キャッシュ付き）
        
        Args:
            field: 圃場
            crop: 作物
            weather_data: 気象データ
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[Any]: GDD候補リスト
        """
        cache_key = f"{field.field_id}_{crop.crop_id}_{start_date}_{end_date}"
        
        if cache_key in self._gdd_candidates_cache:
            return self._gdd_candidates_cache[cache_key]
        
        # GrowthPeriodOptimizeInteractorを使用してGDD候補を生成
        from agrr_core.usecase.dto.growth_period_optimize_request_dto import OptimalGrowthPeriodRequestDTO
        
        request = OptimalGrowthPeriodRequestDTO(
            crop_id=crop.crop_id,
            variety="default",
            evaluation_period_start=start_date,
            evaluation_period_end=end_date,
            field=field
        )
        
        try:
            response = await self._growth_period_optimizer.execute(request)
            candidates = response.candidates if response.success else []
        except Exception:
            candidates = []
        
        self._gdd_candidates_cache[cache_key] = candidates
        return candidates
    
    async def _calculate_profit(
        self,
        field: Field,
        crop: Crop,
        allocation: Any,
        weather_data: List[Any]
    ) -> float:
        """
        利益を計算
        
        Args:
            field: 圃場
            crop: 作物
            allocation: 配分
            weather_data: 気象データ
            
        Returns:
            float: 期待利益
        """
        # OptimizationObjectiveを使用して利益を計算
        objective = OptimizationObjective()
        
        try:
            # 配分から利益を計算
            if hasattr(allocation, 'expected_revenue') and hasattr(allocation, 'total_cost'):
                profit = allocation.expected_revenue - allocation.total_cost
            else:
                # 基本的な利益計算
                revenue_per_area = crop.revenue_per_area if hasattr(crop, 'revenue_per_area') else 1000.0
                area = allocation.area_used if hasattr(allocation, 'area_used') else 500.0
                days = (allocation.completion_date - allocation.start_date).days if hasattr(allocation, 'completion_date') and hasattr(allocation, 'start_date') else 90
                
                expected_revenue = revenue_per_area * area
                total_cost = field.daily_fixed_cost * days
                profit = expected_revenue - total_cost
            
            return max(0, profit)  # 負の利益は0に制限
        except Exception:
            return 0.0
    
    async def _calculate_move_profit(
        self,
        source_allocation: CropAllocation,
        target_field: Field,
        new_start_date: datetime,
        weather_data: List[Any]
    ) -> float:
        """
        移動後の利益を計算
        
        Args:
            source_allocation: 移動元の配分
            target_field: 移動先の圃場
            new_start_date: 新しい開始日
            weather_data: 気象データ
            
        Returns:
            float: 移動後の期待利益
        """
        try:
            # 移動後の期間を計算
            if hasattr(source_allocation, 'completion_date') and hasattr(source_allocation, 'start_date'):
                original_days = (source_allocation.completion_date - source_allocation.start_date).days
                new_completion_date = new_start_date + timedelta(days=original_days)
            else:
                new_completion_date = new_start_date + timedelta(days=90)
            
            # 移動先圃場での利益を計算
            if hasattr(source_allocation, 'expected_revenue') and hasattr(source_allocation, 'total_cost'):
                # 既存の利益から移動先圃場のコスト差を調整
                original_profit = source_allocation.expected_revenue - source_allocation.total_cost
                cost_difference = (target_field.daily_fixed_cost - source_allocation.field.daily_fixed_cost) * original_days
                new_profit = original_profit - cost_difference
            else:
                # 基本的な利益計算
                revenue_per_area = 1000.0  # デフォルト値
                area = source_allocation.area_used if hasattr(source_allocation, 'area_used') else 500.0
                days = original_days
                
                expected_revenue = revenue_per_area * area
                total_cost = target_field.daily_fixed_cost * days
                new_profit = expected_revenue - total_cost
            
            return max(0, new_profit)  # 負の利益は0に制限
        except Exception:
            return 0.0
