#!/usr/bin/env python3
"""Python 파일들의 syntax 및 import 오류를 검사하는 스크립트"""

import ast
import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict

def check_syntax(file_path: str) -> Tuple[bool, str]:
    """파일의 syntax를 검사합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax Error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_imports(file_path: str) -> List[str]:
    """파일의 import 문제를 검사합니다."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    try:
                        # 표준 라이브러리나 설치된 패키지 확인
                        importlib.util.find_spec(module_name)
                    except (ImportError, ModuleNotFoundError):
                        errors.append(f"Import Error: Cannot import '{module_name}' at line {node.lineno}")
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module:
                    try:
                        # 상대 경로 import는 건너뛰기
                        if node.level > 0:
                            continue
                        importlib.util.find_spec(module)
                    except (ImportError, ModuleNotFoundError):
                        errors.append(f"Import Error: Cannot import from '{module}' at line {node.lineno}")
    
    except Exception as e:
        errors.append(f"Error checking imports: {str(e)}")
    
    return errors

def main():
    # 검사할 파일 목록
    files_to_check = [
        "backend/app/main.py",
        "backend/app/core/config.py",
        "backend/app/core/security.py",
        "backend/app/core/database.py",
        "backend/app/core/exceptions.py",
        "backend/app/api/v1/router.py",
        "backend/app/api/v1/endpoints/auth.py",
        "backend/app/api/v1/endpoints/users.py",
        "backend/app/api/v1/endpoints/characters.py",
        "backend/app/api/v1/endpoints/quests.py",
        "backend/app/api/v1/endpoints/achievements.py",
        "backend/app/models/user.py",
        "backend/app/models/character.py",
        "backend/app/models/quest.py",
        "backend/app/models/achievement.py",
        "backend/app/schemas/user.py",
        "backend/app/schemas/character.py",
        "backend/app/schemas/quest.py",
        "backend/app/schemas/achievement.py",
        "backend/app/services/character_service.py",
        "backend/app/services/quest_service.py",
        "backend/app/services/achievement_service.py",
    ]
    
    # 현재 디렉토리 저장
    original_dir = os.getcwd()
    
    # backend 디렉토리로 이동하여 모듈 경로 설정
    backend_dir = Path(original_dir) / "backend"
    if backend_dir.exists():
        sys.path.insert(0, str(backend_dir))
    
    results = {}
    
    for file_path in files_to_check:
        full_path = Path(original_dir) / file_path
        if not full_path.exists():
            results[file_path] = {"exists": False, "syntax_ok": False, "errors": ["File not found"]}
            continue
        
        syntax_ok, syntax_error = check_syntax(str(full_path))
        import_errors = check_imports(str(full_path))
        
        all_errors = []
        if not syntax_ok:
            all_errors.append(syntax_error)
        all_errors.extend(import_errors)
        
        results[file_path] = {
            "exists": True,
            "syntax_ok": syntax_ok,
            "errors": all_errors
        }
    
    # 결과 출력
    print("=== Python 파일 검사 결과 ===\n")
    
    error_count = 0
    for file_path, result in results.items():
        if not result["exists"]:
            print(f"❌ {file_path}: 파일을 찾을 수 없습니다.")
            error_count += 1
        elif result["errors"]:
            print(f"❌ {file_path}:")
            for error in result["errors"]:
                print(f"   - {error}")
            error_count += 1
        else:
            print(f"✅ {file_path}: OK")
    
    print(f"\n총 {len(results)}개 파일 중 {error_count}개 파일에서 오류가 발견되었습니다.")

if __name__ == "__main__":
    main()