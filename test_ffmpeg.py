import os
import subprocess

def test_ffmpeg():
    print("Testing FFmpeg installation...")
    
    # Test direct path
    direct_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    if os.path.exists(direct_path):
        print("✓ FFmpeg found at direct path")
        try:
            result = subprocess.run([direct_path, '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ FFmpeg works via direct path")
                print(f"Version: {result.stdout.splitlines()[0]}")
            else:
                print("✗ FFmpeg direct path execution failed")
        except Exception as e:
            print(f"✗ Direct path error: {e}")
    else:
        print("✗ FFmpeg not found at direct path")
    
    # Test system PATH
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFmpeg found in system PATH")
            print(f"Version: {result.stdout.splitlines()[0]}")
        else:
            print("✗ FFmpeg not in system PATH")
    except FileNotFoundError:
        print("✗ FFmpeg not found in system PATH")

if __name__ == "__main__":
    test_ffmpeg()