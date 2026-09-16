from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.user import User

router = APIRouter()


# --- Schemas ---


class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    tags: list[str] = []
    extra_metadata: dict = {}


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[AssetStatus] = None
    tags: Optional[list[str]] = None
    extra_metadata: Optional[dict] = None
    criticality: Optional[str] = None


class AssetResponse(BaseModel):
    id: int
    uuid: str
    name: str
    asset_type: AssetType
    status: AssetStatus
    risk_score: float
    criticality: str
    ip_address: Optional[str]
    hostname: Optional[str]
    tags: list[str]
    created_at: datetime
    last_seen: datetime
    discovery_method: Optional[str]

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AssetStats(BaseModel):
    total_assets: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    by_criticality: dict[str, int]
    avg_risk_score: float
    high_risk_count: int
    new_last_24h: int
    new_last_7d: int


# --- Endpoints ---


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    asset_type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    search: Optional[str] = None,
    min_risk_score: Optional[float] = None,
    max_risk_score: Optional[float] = None,
    tags: Optional[str] = None,
    sort_by: str = Query(
        "risk_score", enum=["risk_score", "name", "created_at", "last_seen"]
    ),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all assets with filtering, sorting, and pagination."""
    query = select(Asset).where(Asset.organization_id == current_user.organization_id)

    # Filters
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    if status:
        query = query.where(Asset.status == status)
    if search:
        query = query.where(
            or_(
                Asset.name.ilike(f"%{search}%"),
                Asset.ip_address.ilike(f"%{search}%"),
                Asset.hostname.ilike(f"%{search}%"),
            )
        )
    if min_risk_score is not None:
        query = query.where(Asset.risk_score >= min_risk_score)
    if max_risk_score is not None:
        query = query.where(Asset.risk_score <= max_risk_score)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.where(Asset.tags.contains([tag]))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Sort
    sort_column = getattr(Asset, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    assets = result.scalars().all()

    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", response_model=AssetStats)
async def get_asset_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get asset statistics overview."""
    base_query = select(Asset).where(
        Asset.organization_id == current_user.organization_id
    )

    total = (
        await db.execute(select(func.count()).select_from(base_query.subquery()))
    ).scalar()

    # By type
    type_query = (
        select(Asset.asset_type, func.count())
        .where(Asset.organization_id == current_user.organization_id)
        .group_by(Asset.asset_type)
    )
    type_result = await db.execute(type_query)
    by_type = {str(row[0]): row[1] for row in type_result.all()}

    # By status
    status_query = (
        select(Asset.status, func.count())
        .where(Asset.organization_id == current_user.organization_id)
        .group_by(Asset.status)
    )
    status_result = await db.execute(status_query)
    by_status = {str(row[0]): row[1] for row in status_result.all()}

    # By criticality
    crit_query = (
        select(Asset.criticality, func.count())
        .where(Asset.organization_id == current_user.organization_id)
        .group_by(Asset.criticality)
    )
    crit_result = await db.execute(crit_query)
    by_criticality = {str(row[0]): row[1] for row in crit_result.all()}

    # Average risk score
    avg_risk = (
        await db.execute(
            select(func.avg(Asset.risk_score)).where(
                Asset.organization_id == current_user.organization_id
            )
        )
    ).scalar() or 0.0

    # High risk count
    high_risk = (
        await db.execute(
            select(func.count()).where(
                and_(
                    Asset.organization_id == current_user.organization_id,
                    Asset.risk_score >= 80,
                )
            )
        )
    ).scalar()

    # New in last 24h and 7d
    from datetime import timedelta

    now = datetime.utcnow()
    new_24h = (
        await db.execute(
            select(func.count()).where(
                and_(
                    Asset.organization_id == current_user.organization_id,
                    Asset.created_at >= now - timedelta(hours=24),
                )
            )
        )
    ).scalar()
    new_7d = (
        await db.execute(
            select(func.count()).where(
                and_(
                    Asset.organization_id == current_user.organization_id,
                    Asset.created_at >= now - timedelta(days=7),
                )
            )
        )
    ).scalar()

    return AssetStats(
        total_assets=total,
        by_type=by_type,
        by_status=by_status,
        by_criticality=by_criticality,
        avg_risk_score=round(float(avg_risk), 2),
        high_risk_count=high_risk,
        new_last_24h=new_24h,
        new_last_7d=new_7d,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific asset by ID."""
    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.organization_id == current_user.organization_id,
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse.model_validate(asset)


@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    asset_data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin", "analyst"])),
):
    """Create a new asset."""
    asset = Asset(
        uuid=str(uuid.uuid4()),
        name=asset_data.name,
        asset_type=asset_data.asset_type,
        ip_address=asset_data.ip_address,
        hostname=asset_data.hostname,
        tags=asset_data.tags,
        extra_metadata=asset_data.extra_metadata,
        organization_id=current_user.organization_id,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return AssetResponse.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin", "analyst"])),
):
    """Update an existing asset."""
    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.organization_id == current_user.organization_id,
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    asset.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(asset)

    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin"])),
):
    """Delete an asset."""
    result = await db.execute(
        select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.organization_id == current_user.organization_id,
            )
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    await db.delete(asset)
    await db.commit()


@router.get("/{asset_id}/related")
async def get_asset_relationships(
    asset_id: int,
    depth: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get related assets (graph traversal). Falls back to empty if Neo4j unavailable."""
    from app.core.database import Neo4jDriver

    driver = await Neo4jDriver.get_driver()
    if driver is None:
        return {
            "asset_id": asset_id,
            "relationships": [],
            "message": "Graph database not available",
        }

    try:
        async with driver.session() as session:
            query = """
            MATCH path = (start:Asset {pulse_id: $asset_id})-[*1..$depth]-(related:Asset)
            RETURN path, nodes(path) as nodes, relationships(path) as rels
            LIMIT 100
            """
            result = await session.run(query, asset_id=asset_id, depth=depth)
            relationships = []
            async for record in result:
                relationships.append(
                    {
                        "path": record["path"],
                        "nodes": record["nodes"],
                        "relationships": record["rels"],
                    }
                )

        return {"asset_id": asset_id, "relationships": relationships}
    except Exception as e:
        return {"asset_id": asset_id, "relationships": [], "error": str(e)}
