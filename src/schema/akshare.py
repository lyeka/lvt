"""AkShare 数据模型定义。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IndustryBoardItem(BaseModel):
    """行业板块数据项。"""

    board_code: str = Field(description="板块代码，如 BK0457")
    board_name: str = Field(description="板块名称")


class IndustryBoardsResult(BaseModel):
    """行业板块列表查询结果。"""

    total: int = Field(description="板块总数")
    items: list[IndustryBoardItem] = Field(description="板块列表")


class IndustryConstituentItem(BaseModel):
    """行业成分股数据项。"""

    stock_code: str = Field(description="股票代码")
    stock_name: str = Field(description="股票名称")


class IndustryConstituentsResult(BaseModel):
    """行业成分股查询结果。"""

    symbol: str = Field(description="板块代码")
    total: int = Field(description="成分股总数")
    items: list[IndustryConstituentItem] = Field(description="成分股列表")


class SectorFundFlowItem(BaseModel):
    """板块资金流数据项。"""

    sector_name: str = Field(description="板块名称")
    rank: int = Field(description="排名")


class SectorFundFlowResult(BaseModel):
    """板块资金流排名查询结果。"""

    indicator: str = Field(description="指标周期：今日/5日/10日")
    sector_type: str = Field(description="板块类型：行业资金流/概念资金流/地域资金流")
    total: int = Field(description="板块总数")
    items: list[SectorFundFlowItem] = Field(description="资金流排名列表")

