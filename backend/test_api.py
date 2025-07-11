#!/usr/bin/env python3
"""
API 엔드포인트 테스트 스크립트
FastAPI 서버가 실행중이어야 합니다.
"""

import requests
import json
from datetime import datetime

# 테스트 서버 URL
BASE_URL = "http://localhost:8000"

# 테스트 데이터
test_user = {
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpassword123",
    "full_name": "Test User"
}

test_character = {
    "name": "TestHero",
    "avatar_url": "https://example.com/avatar.png"
}

def print_response(response, title):
    """응답 출력 헬퍼 함수"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_health_check():
    """헬스 체크 테스트"""
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_user_registration():
    """사용자 등록 테스트"""
    response = requests.post(f"{BASE_URL}/api/v1/users/register", json=test_user)
    print_response(response, "User Registration")
    return response.status_code == 201

def test_user_login():
    """사용자 로그인 테스트"""
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print_response(response, "User Login")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_get_current_user(token):
    """현재 사용자 정보 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
    print_response(response, "Get Current User")
    return response.status_code == 200

def test_create_character(token):
    """캐릭터 생성 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/characters/",
        json=test_character,
        headers=headers
    )
    print_response(response, "Create Character")
    return response.json().get("id") if response.status_code == 201 else None

def test_get_character(token, character_id):
    """캐릭터 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/characters/{character_id}",
        headers=headers
    )
    print_response(response, "Get Character")
    return response.status_code == 200

def test_get_quests(token):
    """퀘스트 목록 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/quests/", headers=headers)
    print_response(response, "Get Quests")
    return response.status_code == 200

def test_get_achievements(token):
    """업적 목록 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/achievements/", headers=headers)
    print_response(response, "Get Achievements")
    return response.status_code == 200

def run_tests():
    """모든 테스트 실행"""
    print("\n" + "="*70)
    print("API ENDPOINT TESTS")
    print("="*70)
    
    results = []
    
    # 1. 헬스 체크
    results.append(("Health Check", test_health_check()))
    
    # 2. 사용자 등록
    results.append(("User Registration", test_user_registration()))
    
    # 3. 로그인 및 토큰 획득
    token = test_user_login()
    results.append(("User Login", token is not None))
    
    if token:
        # 4. 현재 사용자 정보 조회
        results.append(("Get Current User", test_get_current_user(token)))
        
        # 5. 캐릭터 생성
        character_id = test_create_character(token)
        results.append(("Create Character", character_id is not None))
        
        if character_id:
            # 6. 캐릭터 조회
            results.append(("Get Character", test_get_character(token, character_id)))
        
        # 7. 퀘스트 목록 조회
        results.append(("Get Quests", test_get_quests(token)))
        
        # 8. 업적 목록 조회
        results.append(("Get Achievements", test_get_achievements(token)))
    
    # 결과 요약
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<30} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the server.")
        print("Please make sure the FastAPI server is running on http://localhost:8000")
        print("\nTo start the server, run:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        exit(1)