import os
from fastapi import HTTPException, UploadFile
import magic
from typing import Tuple

class FileValidator:
    ALLOWED_EXTENSION = '.txt'  # Chỉ chấp nhận .txt
    
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Kiểm tra tính hợp lệ của file:
        1. Chỉ chấp nhận file có đuôi .txt
        2. File không được rỗng
        3. File phải đọc được như text file
        
        Returns: (is_valid, error_message)
        """
        try:
            # 1. Kiểm tra file có tên hợp lệ không
            if not file.filename:
                return False, "Tên file không được để trống"
                
            # 2. Kiểm tra phần mở rộng phải là .txt
            file_ext = os.path.splitext(file.filename.lower())[1]
            if file_ext != FileValidator.ALLOWED_EXTENSION:
                return False, f"Chỉ chấp nhận file .txt. File của bạn có đuôi {file_ext}"
                
            # 3. Đọc và kiểm tra nội dung file
            content = file.file.read()
            file.file.seek(0)  # Reset con trỏ về đầu file
            
            # Kiểm tra file rỗng
            if len(content) == 0:
                return False, "File không được rỗng"
                
            # Kiểm tra có phải là text không
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "File phải là file text hợp lệ (UTF-8)"
                
            return True, ""
            
        except Exception as e:
            return False, f"Lỗi kiểm tra file: {str(e)}""

            # 3. Đọc nội dung file để kiểm tra
            content = file.file.read()
            file.file.seek(0)  # Reset về đầu file

            # Kiểm tra file rỗng
            if len(content) == 0:
                return False, "File không được rỗng"

            # 4. Kiểm tra có đọc được như text không
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "File không phải là file text hợp lệ"

            return True, ""

        except Exception as e:
            return False, f"Lỗi kiểm tra file: {str(e)}"
