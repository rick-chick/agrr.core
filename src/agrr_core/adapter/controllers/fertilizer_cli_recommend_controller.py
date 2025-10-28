"""CLI controller for fertilizer recommendation."""

import argparse
import json
from typing import Any, Dict, Optional

from agrr_core.framework.services.io.file_service import FileService
from agrr_core.usecase.interactors.fertilizer_llm_recommend_interactor import (
    FertilizerLLMRecommendInteractor,
    FertilizerRecommendRequestDTO,
)
from agrr_core.adapter.presenters.fertilizer_recommend_cli_presenter import FertilizerRecommendCliPresenter


class FertilizerCliRecommendController:
    def __init__(self, interactor: FertilizerLLMRecommendInteractor = None) -> None:
        self._interactor = interactor
        self._file_service = FileService()

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Recommend fertilizer plan (N,P,K in g/m2)")
        parser.add_argument("recommend", nargs="?")
        parser.add_argument("--crop-file", "-c", required=True, help="Path to crop profile JSON (output of 'agrr crop')")
        parser.add_argument("--output", "-o", help="Output file path (JSON). If omitted, prints to stdout")
        parser.add_argument("--json", "-j", action="store_true", help="Output JSON only (no extra text)")
        return parser

    async def handle(self, args: argparse.Namespace) -> str:
        crop_profile = await self._load_crop_profile(args.crop_file)
        req = FertilizerRecommendRequestDTO(crop_profile=crop_profile)
        plan = await self._interactor.execute(req)
        output = FertilizerRecommendCliPresenter.to_json(plan)

        if args.output:
            await self._file_service.write(output, args.output)
            return ""  # quiet when writing to file
        return output if args.json else output

    async def _load_crop_profile(self, path: str) -> Dict[str, Any]:
        content = await self._file_service.read(path)
        data = json.loads(content)
        # Minimal validation: must contain 'crop' with crop_id and name
        if "crop" not in data or "crop_id" not in data["crop"] or "name" not in data["crop"]:
            raise ValueError("Invalid crop profile file: missing crop.crop_id or crop.name")
        return data

    def _serialize_plan(self, plan) -> Dict[str, Any]:
        # Deprecated: kept for compatibility; use presenter
        return FertilizerRecommendCliPresenter.to_dict(plan)


