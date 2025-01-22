import sys
import os
import subprocess
try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata

def install_requirements():
    """필요한 패키지들을 자동으로 설치합니다."""
    print("패키지 설치 상태를 확인하고 있습니다...")
    
    # requirements.txt 파일 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(current_dir, 'BE', 'requirements.txt')
    
    try:
        # requirements.txt 파일이 존재하는지 확인
        if not os.path.exists(requirements_path):
            raise FileNotFoundError(f"requirements.txt 파일을 찾을 수 없습니다: {requirements_path}")

        # pip를 최신 버전으로 업그레이드
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # requirements.txt를 이용해 패키지 설치
        print("필요한 패키지들을 설치합니다...")
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "pip", 
            "install", 
            "-r", 
            requirements_path,
            "--extra-index-url",
            "https://download.pytorch.org/whl/cu121"
        ])
        print("패키지 설치가 완료되었습니다.")
        
    except Exception as e:
        print(f"패키지 설치 중 오류가 발생했습니다: {e}")
        input("계속하려면 아무 키나 누르세요...")
        sys.exit(1)

# BE 폴더 경로를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)  # BE의 상위 디렉토리를 추가

def main():
    try:
        # 패키지 설치 확인 및 설치
        install_requirements()
        
        # BE/main.py 실행
        from BE.main import main
        main()
        
    except Exception as e:
        print(f"에러 발생: {e}")
        input("계속하려면 아무 키나 누르세요...")

if __name__ == "__main__":
    main()
