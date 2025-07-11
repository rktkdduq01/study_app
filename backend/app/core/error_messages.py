"""
User-friendly error messages mapping
"""
from typing import Dict, Optional
from enum import Enum


class ErrorCategory(str, Enum):
    """Error categories for grouping related errors"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    SERVER = "server"
    BUSINESS = "business"
    RATE_LIMIT = "rate_limit"
    MAINTENANCE = "maintenance"


# User-friendly error messages by error code
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    # Authentication errors
    "AUTH001": {
        "message": "로그인이 필요합니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "다시 로그인해주세요"
    },
    "AUTH002": {
        "message": "로그인 정보가 만료되었습니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "보안을 위해 다시 로그인해주세요"
    },
    "AUTH003": {
        "message": "잘못된 이메일 또는 비밀번호입니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "입력 정보를 확인하고 다시 시도해주세요"
    },
    "AUTH004": {
        "message": "계정이 잠겼습니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "고객센터에 문의하거나 비밀번호를 재설정해주세요"
    },
    "AUTH005": {
        "message": "이메일 인증이 필요합니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "이메일로 전송된 인증 링크를 클릭해주세요"
    },
    
    # Authorization errors
    "PERM001": {
        "message": "접근 권한이 없습니다",
        "category": ErrorCategory.AUTHORIZATION,
        "action": "필요한 권한이 있는지 확인해주세요"
    },
    "PERM002": {
        "message": "프리미엄 기능입니다",
        "category": ErrorCategory.AUTHORIZATION,
        "action": "프리미엄 구독이 필요한 기능입니다"
    },
    "PERM003": {
        "message": "연령 제한 콘텐츠입니다",
        "category": ErrorCategory.AUTHORIZATION,
        "action": "보호자의 승인이 필요합니다"
    },
    
    # Validation errors
    "VAL001": {
        "message": "입력 정보를 확인해주세요",
        "category": ErrorCategory.VALIDATION,
        "action": "빨간색으로 표시된 항목을 수정해주세요"
    },
    "VAL002": {
        "message": "필수 정보가 누락되었습니다",
        "category": ErrorCategory.VALIDATION,
        "action": "모든 필수 항목을 입력해주세요"
    },
    "VAL003": {
        "message": "올바른 이메일 형식이 아닙니다",
        "category": ErrorCategory.VALIDATION,
        "action": "example@email.com 형식으로 입력해주세요"
    },
    "VAL004": {
        "message": "비밀번호가 너무 약합니다",
        "category": ErrorCategory.VALIDATION,
        "action": "8자 이상, 대소문자와 숫자를 포함해주세요"
    },
    
    # Network errors
    "NET001": {
        "message": "인터넷 연결을 확인해주세요",
        "category": ErrorCategory.NETWORK,
        "action": "네트워크 연결 후 다시 시도해주세요"
    },
    "NET002": {
        "message": "서버에 연결할 수 없습니다",
        "category": ErrorCategory.NETWORK,
        "action": "잠시 후 다시 시도해주세요"
    },
    "NET003": {
        "message": "요청 시간이 초과되었습니다",
        "category": ErrorCategory.NETWORK,
        "action": "네트워크 상태를 확인하고 다시 시도해주세요"
    },
    
    # Server errors
    "SRV001": {
        "message": "일시적인 오류가 발생했습니다",
        "category": ErrorCategory.SERVER,
        "action": "잠시 후 다시 시도해주세요"
    },
    "SRV002": {
        "message": "서비스 점검 중입니다",
        "category": ErrorCategory.MAINTENANCE,
        "action": "점검 시간: 00:00 - 02:00"
    },
    "SRV003": {
        "message": "파일 업로드에 실패했습니다",
        "category": ErrorCategory.SERVER,
        "action": "파일 크기와 형식을 확인해주세요"
    },
    
    # Business logic errors
    "BIZ001": {
        "message": "이미 존재하는 계정입니다",
        "category": ErrorCategory.BUSINESS,
        "action": "다른 이메일을 사용하거나 로그인해주세요"
    },
    "BIZ002": {
        "message": "퀘스트를 완료할 수 없습니다",
        "category": ErrorCategory.BUSINESS,
        "action": "필요한 조건을 모두 충족했는지 확인해주세요"
    },
    "BIZ003": {
        "message": "포인트가 부족합니다",
        "category": ErrorCategory.BUSINESS,
        "action": "퀘스트를 완료하여 포인트를 획득하세요"
    },
    "BIZ004": {
        "message": "이미 참여한 활동입니다",
        "category": ErrorCategory.BUSINESS,
        "action": "다른 활동을 선택해주세요"
    },
    
    # Rate limiting
    "RATE001": {
        "message": "너무 많은 요청을 보냈습니다",
        "category": ErrorCategory.RATE_LIMIT,
        "action": "1분 후에 다시 시도해주세요"
    },
    "RATE002": {
        "message": "로그인 시도 횟수를 초과했습니다",
        "category": ErrorCategory.RATE_LIMIT,
        "action": "5분 후에 다시 시도해주세요"
    }
}


def get_user_message(
    error_code: str,
    fallback_message: Optional[str] = None,
    context: Optional[Dict[str, any]] = None
) -> Dict[str, str]:
    """
    Get user-friendly error message for an error code
    
    Args:
        error_code: Error code to look up
        fallback_message: Fallback message if code not found
        context: Additional context to customize message
        
    Returns:
        Dictionary with message, category, and action
    """
    if error_code in ERROR_MESSAGES:
        message_data = ERROR_MESSAGES[error_code].copy()
        
        # Apply context if provided
        if context:
            if "retry_after" in context:
                message_data["action"] = f"{context['retry_after']}초 후에 다시 시도해주세요"
            if "required_role" in context:
                message_data["action"] = f"{context['required_role']} 권한이 필요합니다"
        
        return message_data
    
    # Default fallback
    return {
        "message": fallback_message or "오류가 발생했습니다",
        "category": ErrorCategory.SERVER,
        "action": "문제가 지속되면 고객센터에 문의해주세요"
    }


def get_field_error_message(field: str, error_type: str) -> str:
    """
    Get user-friendly error message for field validation
    
    Args:
        field: Field name
        error_type: Type of validation error
        
    Returns:
        User-friendly error message
    """
    field_names = {
        "email": "이메일",
        "password": "비밀번호",
        "username": "사용자명",
        "phone": "전화번호",
        "age": "나이",
        "name": "이름",
        "title": "제목",
        "content": "내용",
        "amount": "금액"
    }
    
    error_messages = {
        "required": "{field}을(를) 입력해주세요",
        "invalid": "올바른 {field} 형식이 아닙니다",
        "too_short": "{field}이(가) 너무 짧습니다",
        "too_long": "{field}이(가) 너무 깁니다",
        "duplicate": "이미 사용 중인 {field}입니다",
        "not_found": "{field}을(를) 찾을 수 없습니다",
        "min_value": "{field}의 최소값을 확인해주세요",
        "max_value": "{field}의 최대값을 확인해주세요"
    }
    
    friendly_field = field_names.get(field, field)
    template = error_messages.get(error_type, "{field}을(를) 확인해주세요")
    
    return template.format(field=friendly_field)