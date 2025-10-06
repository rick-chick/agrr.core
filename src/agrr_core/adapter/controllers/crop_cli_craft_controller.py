"""CLI controller for crafting crop requirements (adapter layer)."""

import argparse
import asyncio
import json
from typing import Optional

from agrr_core.adapter.gateways.crop_requirement_gateway_impl import (
    CropRequirementGatewayImpl,
)
from agrr_core.adapter.presenters.crop_requirement_craft_presenter import (
    CropRequirementCraftPresenter,
)
from agrr_core.usecase.interactors.crop_requirement_craft_interactor import (
    CropRequirementCraftInteractor,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)


class CropCliCraftController:
    """CLI controller orchestrating the crop requirement craft use case."""

    def __init__(
        self,
        gateway: CropRequirementGatewayImpl,
        presenter: CropRequirementCraftPresenter,
    ) -> None:
        """Initialize with injected gateway and presenter."""
        self.gateway = gateway
        self.presenter = presenter
        # Instantiate interactor inside controller per project rule
        self.interactor = CropRequirementCraftInteractor(
            gateway=self.gateway, presenter=self.presenter
        )

    def create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Crop Requirement CLI - Craft crop stage requirements",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        craft_parser = subparsers.add_parser("crop", help="Craft crop requirements")
        craft_parser.add_argument(
            "--query",
            "-q",
            required=True,
            help='Crop query string (e.g., "トマト", "アイコトマト")',
        )
        craft_parser.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON (default: True)",
        )

        return parser

    async def handle_craft_command(self, args) -> None:
        request = CropRequirementCraftRequestDTO(crop_query=args.query)
        result = await self.interactor.execute(request)

        # Always print JSON; the presenter already wraps success/error
        print(json.dumps(result, ensure_ascii=False))

    async def run(self, args: Optional[list] = None) -> None:
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return

        if parsed_args.command == "crop":
            await self.handle_craft_command(parsed_args)
        else:
            parser.print_help()


