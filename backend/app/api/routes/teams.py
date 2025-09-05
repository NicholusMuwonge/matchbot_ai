from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import ClerkSessionSuperuser, ClerkSessionUser
from app.core.formatters import TeamResponseFormatter
from app.models import Message
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

router = APIRouter()


class TeamCreate(BaseModel):
    name: str
    team_type: str
    description: str | None = None
    max_users: int | None = None


class TeamResponse(BaseModel):
    id: str
    name: str
    team_type: str
    created_by: str | None
    created_at: int | None
    members_count: int
    description: str | None = None
    max_users: int | None = None


class TeamsListResponse(BaseModel):
    teams: list[TeamResponse]
    total_count: int


class _TeamRouteHelpers:
    """Private helper class for team route operations."""

    @staticmethod
    def _prepare_team_metadata(team_data: TeamCreate) -> dict[str, Any]:
        return TeamResponseFormatter.format_team_metadata(
            team_data.team_type, team_data.description, team_data.max_users
        )

    @staticmethod
    def _create_team_response(org_result: dict[str, Any]) -> TeamResponse:
        formatted_data = TeamResponseFormatter.format_full_team_response(org_result)
        return TeamResponse(**formatted_data)

    @staticmethod
    def _create_list_team_response(
        org_data: dict[str, Any], org_team_type: str
    ) -> TeamResponse:
        formatted_data = TeamResponseFormatter.format_list_team_response(
            org_data, org_team_type
        )
        return TeamResponse(**formatted_data)


@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate, current_user: ClerkSessionUser
) -> TeamResponse:
    try:
        clerk_service = ClerkService()
        public_metadata = _TeamRouteHelpers._prepare_team_metadata(team_data)

        org_result = clerk_service.create_organization(
            name=team_data.name,
            created_by=current_user.clerk_user_id,
            public_metadata=public_metadata,
        )

        if not org_result:
            raise HTTPException(status_code=500, detail="Failed to create team")

        return _TeamRouteHelpers._create_team_response(org_result)

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.get("/", response_model=TeamsListResponse)
async def list_teams(
    _: ClerkSessionSuperuser,
    team_type: str | None = Query(None, description="Filter by team type"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TeamsListResponse:
    try:
        clerk_service = ClerkService()
        result = clerk_service.list_organizations(
            query=None, limit=limit, offset=offset
        )

        teams = []
        for org_data in result["organizations"]:
            org_team_type = org_data["public_metadata"].get("team_type", "corporate")
            if team_type and org_team_type != team_type:
                continue

            teams.append(
                _TeamRouteHelpers._create_list_team_response(org_data, org_team_type)
            )

        return TeamsListResponse(teams=teams, total_count=len(teams))

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, _: ClerkSessionUser) -> TeamResponse:
    try:
        clerk_service = ClerkService()
        org_data = clerk_service.get_organization(team_id)

        if not org_data:
            raise HTTPException(status_code=404, detail="Team not found")

        return _TeamRouteHelpers._create_team_response(org_data)

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}")


@router.delete("/{team_id}", response_model=Message)
async def delete_team(team_id: str, _: ClerkSessionSuperuser) -> Message:
    try:
        clerk_service = ClerkService()
        success = clerk_service.delete_organization(team_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete team")

        return Message(message="Team deleted successfully")

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")
