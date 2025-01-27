from dataclasses import dataclass
from typing import Optional, Any
import json

@dataclass
class LogicItem:
    """로직 아이템 데이터를 표현하는 모델 클래스"""
    id: Optional[int] = None
    logic_id: Optional[int] = None
    item_order: int = 0
    item_type: str = ""
    item_data: dict = None
    
    def __post_init__(self):
        if self.item_data is None:
            self.item_data = {}
            
    def to_dict(self) -> dict:
        """LogicItem 객체를 dictionary로 변환"""
        return {
            'id': self.id,
            'logic_id': self.logic_id,
            'item_order': self.item_order,
            'item_type': self.item_type,
            'item_data': self.item_data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LogicItem':
        """dictionary에서 LogicItem 객체 생성"""
        # item_data가 문자열로 저장되어 있을 경우 처리
        item_data = data.get('item_data')
        if isinstance(item_data, str):
            item_data = json.loads(item_data)
            
        return cls(
            id=data.get('id'),
            logic_id=data.get('logic_id'),
            item_order=data.get('item_order', 0),
            item_type=data.get('item_type', ''),
            item_data=item_data
        ) 