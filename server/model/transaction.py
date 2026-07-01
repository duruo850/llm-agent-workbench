from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import PrivateAttr
from sqlalchemy import Column, DateTime, Index, func
from sqlmodel import Field, SQLModel
from langchain_core.documents import Document


class Transaction(SQLModel, table=True):
    """交易：ORM 表 + API 序列化（SQLModel 合一）。"""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_transacted_at", "transacted_at"),
        Index("ix_transactions_account_id", "account_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    account_id: int | None = Field(default=None, foreign_key="accounts.id")
    amount: Decimal = Field(max_digits=12, decimal_places=2, gt=0)
    category: str = Field(max_length=100)
    merchant: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=500)
    transacted_at: datetime = Field(sa_column=Column(DateTime(timezone=False), nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )

    # 语义检索命中时的相似度（非 DB 列，仅内存携带）
    _search_score: float | None = PrivateAttr(default=None)

    @property
    def search_score(self) -> float | None:
        return self._search_score

    @search_score.setter
    def search_score(self, value: float | None) -> None:
        self._search_score = value

    def embedding_text(self) -> str:
        """格式化为 Milvus embedding 原文。"""
        date = self.transacted_at.strftime("%Y-%m-%d")
        merchant = self.merchant or ""
        note = self.note or ""
        return f"{date} {self.category} {merchant} {note} {self.amount}元"
        
    @classmethod
    def from_document(cls, doc: Document, *, score: float | None = None) -> Transaction:
        """从 Document 实例转化成 Transaction 实例。

        Args:
            doc: Document 实例。
            score: 相似度得分。

        Returns:
            Transaction: _description_
        """
        data = doc.metadata or {}
        data["search_score"] = score
        return cls.from_dict(data)
        
    def to_document(self) -> Document:
        """转化成 Document 实例。

        Returns:
            Document: Document 实例。
        """
        return Document(
            page_content=self.embedding_text(),
            metadata={
                "account_id": self.account_id,
                "transaction_id": self.id,
                "category": self.category,
                "merchant": self.merchant or "",
                "note": self.note or "",
                "amount": str(self.amount),
                "transacted_at": self.transacted_at.isoformat(),
            },
        )
        
    def doc_id(self) -> str:
        """文档 ID。用于 Milvus 的文档 ID。

        Returns:
            str: 文档 ID
        """
        return f"{self.account_id}_{self.id}"

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> Transaction:
        """
        从 dict 字段格式转化成 Transaction 实例。
        Args:
            data: dict 字段格式（如 Milvus metadata)
        Returns:
            Transaction 实例。
        """
        txn = cls(
            id=int(data.get("transaction_id", 0)),
            account_id=int(data.get("account_id", 0)),
            amount=Decimal(str(data.get("amount", "0"))),
            category=str(data.get("category", "")),
            merchant=str(data.get("merchant", "")),
            note=str(data.get("note", "")),
            transacted_at=datetime.fromisoformat(str(data.get("transacted_at", ""))),
            search_score=data.get("search_score"),
        )
        if created_raw := data.get("created_at"):
            txn.created_at = datetime.fromisoformat(str(created_raw))
        return txn

    def to_dict(self) -> dict[object]:
        """
        转化成dict字段格式
        """
        assert self.id is not None
        return {
            "text": self.embedding_text(),
            "transaction_id": self.id,
            "account_id": self.account_id,
            "category": self.category,
            "merchant": self.merchant,
            "note": self.note,
            "amount": str(self.amount),
            "transacted_at": self.transacted_at.isoformat(),
            "score": self.search_score,
        }
