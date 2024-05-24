from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    # 调用默认的异常处理器获取标准的错误响应
    response = exception_handler(exc, context)

    # 如果异常是 ValidationError，定制响应格式
    if isinstance(exc, ValidationError):
        custom_response_data = {
            "msg": exc.detail,
            "data": None,
            "code": response.status_code
        }
        return Response(custom_response_data, status=response.status_code)

    # 如果不是 ValidationError，返回默认的错误响应，包含错误代码
    if response is not None:
        custom_response_data = {
            "msg": response.data,
            "data": None,
            "code": response.status_code
        }
        return Response(custom_response_data, status=response.status_code)

    return response
