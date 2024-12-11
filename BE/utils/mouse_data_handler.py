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
            return json.dumps(mouse_data)
        except Exception as e:
            print(f"마우스 데이터 직렬화 중 오류 발생: {str(e)}")
            return "{}"
            
    @staticmethod
    def deserialize(data_str):
        """문자열을 마우스 입력 데이터로 역직렬화
        
        Args:
            data_str (str): 직렬화된 문자열
            
        Returns:
            dict: 마우스 입력 데이터
        """
        try:
            return json.loads(data_str)
        except Exception as e:
            print(f"마우스 데이터 역직렬화 중 오류 발생: {str(e)}")
            return {} 