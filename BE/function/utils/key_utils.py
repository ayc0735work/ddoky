def format_key_info(key_info):
    """키 정보를 표시 가능한 문자열로 포맷팅

    Args:
        key_info (dict): 키 정보 딕셔너리

    Returns:
        str: 포맷팅된 키 정보 문자열
    """
    if not key_info:
        return ""
    
    # key_code 가져오기
    key_code = key_info.get('key_code', '')
    if not key_code:
        return ""
    
    # 수정자 키 처리
    modifiers = key_info.get('modifiers', 0)
    modifier_text = ""
    
    if modifiers & 0x04000000:  # Qt.ControlModifier
        modifier_text += "Ctrl+"
    if modifiers & 0x02000000:  # Qt.ShiftModifier
        modifier_text += "Shift+"
    if modifiers & 0x08000000:  # Qt.AltModifier
        modifier_text += "Alt+"
    
    return f"{modifier_text}{key_code}"
