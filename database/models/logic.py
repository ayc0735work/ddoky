from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Logic:
    """로직 데이터를 표현하는 모델 클래스"""
    id: Optional[int] = None
    uuid: str = ""
    name: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    is_nested: bool = False
    trigger_key: Optional[str] = None
    repeat_count: int = 1
    display_order: int = 0
    items: List['LogicItem'] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.items is None:
            self.items = []
            
    def to_dict(self) -> dict:
        """Logic 객체를 dictionary로 변환"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_nested': self.is_nested,
            'trigger_key': self.trigger_key,
            'repeat_count': self.repeat_count,
            'display_order': self.display_order,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Logic':
        """dictionary에서 Logic 객체 생성"""
        from .logic_item import LogicItem  # 순환 참조 방지를 위해 지역 import
        
        items_data = data.pop('items', [])
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        
        logic = cls(
            **{k: v for k, v in data.items() if k != 'items'},
            created_at=created_at,
            updated_at=updated_at
        )
        
        logic.items = [LogicItem.from_dict(item) for item in items_data]
        return logic 