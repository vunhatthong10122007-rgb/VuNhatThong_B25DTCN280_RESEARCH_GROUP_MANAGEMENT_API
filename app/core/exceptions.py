from fastapi import HTTPException, status


# Lỗi 400
class BadRequestException(HTTPException):
    def __init__(self, detail="Dữ liệu không hợp lệ"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# Lỗi 404   
class NotFoundException(HTTPException):
    def __init__(self, detail="Không tìm thấy dữ liệu"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# Lỗi 403
class ForbiddenException(HTTPException):
    def __init__(self, detail="Không đủ quyền truy cập"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# Lỗi 401
class UnauthorizedException(HTTPException):
    def __init__(self, detail="Bạn chưa đăng nhập"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
