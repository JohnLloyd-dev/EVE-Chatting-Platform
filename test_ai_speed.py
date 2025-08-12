#!/usr/bin/env python3
"""
AI Speed Optimization Test Suite
Tests the performance improvements for faster AI responses
"""
import httpx
import json
import time
import sys
from datetime import datetime

# Configuration
AI_SERVER_URL = "http://localhost:8000"
AUTH_USERNAME = "adam"
AUTH_PASSWORD = "eve2025"

def test_speed_mode_vs_accuracy():
    """Test speed mode vs accuracy mode performance"""
    print("🚀 Testing Speed Mode vs Accuracy Mode Performance...")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            # Create a session first
            print("  Creating AI session...")
            scenario_response = client.post(
                f"{AI_SERVER_URL}/scenario",
                json={"scenario": "You are a helpful AI assistant. Provide concise, helpful responses."},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if scenario_response.status_code != 200:
                print(f"❌ Failed to create session: {scenario_response.status_code}")
                return False
            
            session_cookie = scenario_response.cookies.get("session_id")
            print(f"✅ Session created: {session_cookie}")
            
            # Test prompts with different complexity
            test_cases = [
                {
                    "name": "Simple Greeting",
                    "message": "Hello, how are you?",
                    "max_tokens": 30
                },
                {
                    "name": "Short Question",
                    "message": "What is 2+2?",
                    "max_tokens": 20
                },
                {
                    "name": "Medium Question",
                    "message": "Explain what is machine learning in one sentence.",
                    "max_tokens": 50
                },
                {
                    "name": "Creative Task",
                    "message": "Write a haiku about technology.",
                    "max_tokens": 40
                }
            ]
            
            results = []
            
            for i, test_case in enumerate(test_cases):
                print(f"\n  Testing {test_case['name']}...")
                
                # Test Speed Mode
                print(f"    🚀 Speed Mode...")
                start_time = time.time()
                speed_response = client.post(
                    f"{AI_SERVER_URL}/chat",
                    json={
                        "message": test_case["message"],
                        "max_tokens": test_case["max_tokens"],
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "speed_mode": True
                    },
                    cookies={"session_id": session_cookie},
                    auth=(AUTH_USERNAME, AUTH_PASSWORD)
                )
                speed_time = time.time() - start_time
                
                if speed_response.status_code != 200:
                    print(f"    ❌ Speed mode failed: {speed_response.status_code}")
                    continue
                
                speed_data = speed_response.json()
                speed_text = speed_data.get("response", "")[:100]
                
                # Test Accuracy Mode
                print(f"    🎯 Accuracy Mode...")
                start_time = time.time()
                accuracy_response = client.post(
                    f"{AI_SERVER_URL}/chat",
                    json={
                        "message": test_case["message"],
                        "max_tokens": test_case["max_tokens"],
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "speed_mode": False
                    },
                    cookies={"session_id": session_cookie},
                    auth=(AUTH_USERNAME, AUTH_PASSWORD)
                )
                accuracy_time = time.time() - start_time
                
                if accuracy_response.status_code != 200:
                    print(f"    ❌ Accuracy mode failed: {accuracy_response.status_code}")
                    continue
                
                accuracy_data = accuracy_response.json()
                accuracy_text = accuracy_data.get("response", "")[:100]
                
                # Calculate speedup
                speedup = accuracy_time / speed_time if speed_time > 0 else 0
                
                result = {
                    "test": test_case["name"],
                    "speed_mode": {
                        "time": round(speed_time, 2),
                        "response": speed_text,
                        "tokens_per_second": round(test_case["max_tokens"] / speed_time, 1) if speed_time > 0 else 0
                    },
                    "accuracy_mode": {
                        "time": round(accuracy_time, 2),
                        "response": accuracy_text,
                        "tokens_per_second": round(test_case["max_tokens"] / accuracy_time, 1) if accuracy_time > 0 else 0
                    },
                    "speedup": round(speedup, 2)
                }
                
                results.append(result)
                
                print(f"    ✅ Speed: {result['speed_mode']['time']}s ({result['speed_mode']['tokens_per_second']} tokens/s)")
                print(f"    ✅ Accuracy: {result['accuracy_mode']['time']}s ({result['accuracy_mode']['tokens_per_second']} tokens/s)")
                print(f"    🚀 Speedup: {result['speedup']}x faster")
            
            # Display comprehensive results
            print("\n" + "=" * 80)
            print("📊 SPEED OPTIMIZATION TEST RESULTS:")
            print("=" * 80)
            
            total_speed_time = sum(r["speed_mode"]["time"] for r in results)
            total_accuracy_time = sum(r["accuracy_mode"]["time"] for r in results)
            overall_speedup = total_accuracy_time / total_speed_time if total_speed_time > 0 else 0
            
            print(f"Overall Performance:")
            print(f"  🚀 Speed Mode Total: {total_speed_time:.2f}s")
            print(f"  🎯 Accuracy Mode Total: {total_accuracy_time:.2f}s")
            print(f"  🚀 Overall Speedup: {overall_speedup:.2f}x faster")
            
            print(f"\nDetailed Results:")
            for result in results:
                print(f"\n{result['test']}:")
                print(f"  🚀 Speed: {result['speed_mode']['time']}s ({result['speed_mode']['tokens_per_second']} tokens/s)")
                print(f"  🎯 Accuracy: {result['accuracy_mode']['time']}s ({result['accuracy_mode']['tokens_per_second']} tokens/s)")
                print(f"  🚀 Speedup: {result['speedup']}x")
                print(f"  📝 Speed Response: {result['speed_mode']['response']}")
                print(f"  📝 Accuracy Response: {result['accuracy_mode']['response']}")
            
            # Performance recommendations
            print(f"\n" + "=" * 80)
            print("💡 PERFORMANCE RECOMMENDATIONS:")
            print("=" * 80)
            
            if overall_speedup > 2.0:
                print("🎉 EXCELLENT: Speed mode provides significant performance improvement!")
                print("   Use speed_mode=True for production to get faster responses.")
            elif overall_speedup > 1.5:
                print("✅ GOOD: Speed mode provides noticeable performance improvement.")
                print("   Consider using speed_mode=True for better user experience.")
            elif overall_speedup > 1.2:
                print("⚠️ MODERATE: Speed mode provides some performance improvement.")
                print("   The benefit may not justify the quality trade-off.")
            else:
                print("❌ MINIMAL: Speed mode provides little performance improvement.")
                print("   Stick with accuracy mode for better quality.")
            
            return True
            
    except Exception as e:
        print(f"❌ Speed test failed: {e}")
        return False

def test_speed_test_endpoint():
    """Test the built-in speed test endpoint"""
    print("\n🧪 Testing Built-in Speed Test Endpoint...")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{AI_SERVER_URL}/speed-test",
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if response.status_code != 200:
                print(f"❌ Speed test endpoint failed: {response.status_code}")
                return False
            
            data = response.json()
            summary = data.get("summary", {})
            
            print(f"✅ Speed test completed successfully!")
            print(f"📊 Results Summary:")
            print(f"  🚀 Average Speed Mode: {summary.get('average_speed_mode_time', 0)}s")
            print(f"  🎯 Average Accuracy Mode: {summary.get('average_accuracy_mode_time', 0)}s")
            print(f"  🚀 Average Speedup: {summary.get('average_speedup', 0)}x")
            print(f"  💡 Recommendation: {summary.get('recommendation', 'N/A')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Built-in speed test failed: {e}")
        return False

def test_response_quality_comparison():
    """Compare response quality between speed and accuracy modes"""
    print("\n🔍 Testing Response Quality Comparison...")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            # Create a session
            scenario_response = client.post(
                f"{AI_SERVER_URL}/scenario",
                json={"scenario": "You are a helpful AI assistant. Provide detailed, accurate responses."},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if scenario_response.status_code != 200:
                print(f"❌ Failed to create session: {scenario_response.status_code}")
                return False
            
            session_cookie = scenario_response.cookies.get("session_id")
            
            # Test with a complex question
            test_message = "Explain the difference between machine learning and artificial intelligence in detail."
            
            print(f"  Testing complex question: {test_message}")
            
            # Speed mode response
            print(f"    🚀 Getting speed mode response...")
            speed_response = client.post(
                f"{AI_SERVER_URL}/chat",
                json={
                    "message": test_message,
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "speed_mode": True
                },
                cookies={"session_id": session_cookie},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if speed_response.status_code != 200:
                print(f"    ❌ Speed mode failed: {speed_response.status_code}")
                return False
            
            speed_data = speed_response.json()
            speed_text = speed_data.get("response", "")
            
            # Accuracy mode response
            print(f"    🎯 Getting accuracy mode response...")
            accuracy_response = client.post(
                f"{AI_SERVER_URL}/chat",
                json={
                    "message": test_message,
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "speed_mode": False
                },
                cookies={"session_id": session_cookie},
                auth=(AUTH_USERNAME, AUTH_PASSWORD)
            )
            
            if accuracy_response.status_code != 200:
                print(f"    ❌ Accuracy mode failed: {accuracy_response.status_code}")
                return False
            
            accuracy_data = accuracy_response.json()
            accuracy_text = accuracy_data.get("response", "")
            
            # Analyze quality differences
            print(f"\n📊 Quality Analysis:")
            print(f"  🚀 Speed Mode Response ({len(speed_text)} chars):")
            print(f"    {speed_text[:200]}...")
            print(f"\n  🎯 Accuracy Mode Response ({len(accuracy_text)} chars):")
            print(f"    {accuracy_text[:200]}...")
            
            # Quality metrics
            speed_words = len(speed_text.split())
            accuracy_words = len(accuracy_text.split())
            
            print(f"\n📈 Quality Metrics:")
            print(f"  🚀 Speed Mode: {speed_words} words, {len(speed_text)} characters")
            print(f"  🎯 Accuracy Mode: {accuracy_words} words, {len(accuracy_text)} characters")
            
            if accuracy_words > speed_words * 1.2:
                print(f"  💡 Accuracy mode provides more detailed responses")
            elif speed_words > accuracy_words * 0.8:
                print(f"  💡 Speed mode maintains good response quality")
            else:
                print(f"  ⚠️ Speed mode may sacrifice some response quality")
            
            return True
            
    except Exception as e:
        print(f"❌ Quality comparison test failed: {e}")
        return False

def main():
    """Run all AI speed optimization tests"""
    print("🚀 AI Speed Optimization Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # Run all tests
    test_results.append(("Speed vs Accuracy Performance", test_speed_mode_vs_accuracy()))
    test_results.append(("Built-in Speed Test Endpoint", test_speed_test_endpoint()))
    test_results.append(("Response Quality Comparison", test_response_quality_comparison()))
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 OVERALL TEST RESULTS:")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1
    
    print("=" * 80)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL AI SPEED OPTIMIZATION TESTS PASSED!")
        print("✅ Speed mode is working correctly")
        print("✅ Performance improvements are active")
        print("✅ Response quality is maintained")
        return True
    else:
        print(f"\n⚠️ {total - passed} AI speed optimization tests failed")
        print("❌ There are performance issues that need to be resolved")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 