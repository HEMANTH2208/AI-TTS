"""
Simple test script to verify voice upload functionality
"""

import requests
import os

def test_upload():
    """Test the voice upload endpoint"""
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000")
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Start it with: python app.py")
        return
    
    # Test with a dummy file (you can replace with actual audio file)
    print("\n📤 Testing voice upload...")
    
    # Create a test file if it doesn't exist
    test_file = "test_audio.txt"
    if not os.path.exists(test_file):
        with open(test_file, 'w') as f:
            f.write("This is a test file")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'audio': ('test.mp3', f, 'audio/mpeg')}
            data = {
                'voice_name': 'Test Voice',
                'training_text': 'Test training text',
                'duration': '15'
            }
            
            response = requests.post(
                "http://localhost:5000/api/upload-clone",
                files=files,
                data=data
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("\n✅ Upload test PASSED!")
            else:
                print("\n❌ Upload test FAILED!")
                print("Check the error message above")
                
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    print("=" * 60)
    print("Voice Upload Test")
    print("=" * 60)
    test_upload()
    print("=" * 60)
