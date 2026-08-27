#!/bin/bash
echo "==========================================="
echo "카메라 드라이버 자동 설치를 시작합니다..."
echo "==========================================="

sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository -y "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt-get update
sudo apt-get install -y librealsense2-utils librealsense2-dev

echo "==========================================="
echo "설치가 완료되었습니다! 이제 다음 명령어를 치세요:"
echo "realsense-viewer"
echo "==========================================="
