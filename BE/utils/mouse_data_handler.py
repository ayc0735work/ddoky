import json

class MouseDataHandler:
    """마우스 입력 데이터를 처리하는 유틸리티 클래스"""
    
    @staticmethod
    def serialize(mouse_data):
        """마우스 입력 데이터를 문자열로 직렬화
        
        Args:
            mouse_data (dict): 마우스 입력 데이터
            
        Returns:
            str: 직렬화된 문자열
        """
        try:
            # 문자열이 입력된 경우 딕셔너리로 변환
            if isinstance(mouse_data, str):
                return json.dumps({'display_text': mouse_data, 'type': 'mouse_input'})
            
            # 기존 데이터가 딕셔너리인 경우
            if isinstance(mouse_data, dict):
                # type 필드가 없으면 추가
                if 'type' not in mouse_data:
                    mouse_data['type'] = 'mouse_input'
                return json.dumps(mouse_data)
                
            raise ValueError("지원되지 않는 데이터 형식입니다")
        except Exception as e:
            print(f"마우스 데이터 직렬화 중 오류 발생: {str(e)}")
            return json.dumps({'display_text': str(mouse_data), 'type': 'mouse_input'})
            
    @staticmethod
    def deserialize(data_str):
        """문자열을 마우스 입력 데이터로 역직렬화
        
        Args:
            data_str (str): 직렬화된 문자열
            
        Returns:
            dict: 마우스 입력 데이터
        """
        try:
            # 이미 딕셔너리인 경우
            if isinstance(data_str, dict):
                return data_str
                
            # 문자열인 경우 JSON으로 파싱
            data = json.loads(data_str)
            
            # 기본 필드 확인 및 추가
            if 'type' not in data:
                data['type'] = 'mouse_input'
            if 'display_text' not in data:
                data['display_text'] = str(data)
                
            return data
        except Exception as e:
            print(f"마우스 데이터 역직렬화 중 오류 발생: {str(e)}")
            return {'type': 'mouse_input', 'display_text': str(data_str)} 