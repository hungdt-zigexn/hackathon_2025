#!/usr/bin/env python3
"""Test script để kiểm tra Google API key"""
import os
import sys

# Kiểm tra API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ GOOGLE_API_KEY chưa được set!")
    print("Chạy lệnh: export GOOGLE_API_KEY='your-key-here'")
    sys.exit(1)

print(f"✓ API key tìm thấy: {api_key[:10]}...")

# Test API
try:
    from google import genai
    client = genai.Client(api_key=api_key)

    # Test simple generation với API mới
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello in 5 words"
    )

    if hasattr(response, 'text'):
        result_text = response.text
    elif hasattr(response, 'candidates'):
        result_text = response.candidates[0].content.parts[0].text
    else:
        result_text = str(response)

    print(f"✓ API hoạt động! Response: {result_text}")
    print("\n✅ Google API key hoạt động tốt!")

except Exception as e:
    print(f"❌ Lỗi khi test API: {e}")
    print("\nCó thể:")
    print("1. API key không hợp lệ")
    print("2. Chưa enable Gemini API trong Google Cloud Console")
    print("3. Vấn đề về network/firewall")
    sys.exit(1)
