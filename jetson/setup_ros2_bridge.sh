#!/bin/bash
# Jetson Orin Nano - ROS 2 Humble & PX4 MicroXRCE-DDS Bridge Setup Script
# 이 스크립트는 젯슨 보드에서 PX4 비행 제어기와 통신하기 위한 필수 브릿지 환경을 자동 구축합니다.

echo "=========================================================="
echo " Starting ROS 2 & MicroXRCE-DDS Bridge Setup on Jetson"
echo "=========================================================="

# 1. Update and Upgrade
sudo apt update && sudo apt upgrade -y

# 2. Install Dependencies
echo "Installing dependencies..."
sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-pip git cmake build-essential

# 3. MicroXRCE-DDS Agent Installation
# 이 에이전트는 PX4(Client)와 ROS2(DDS) 간의 통신 브릿지 역할을 합니다.
echo "Cloning and building MicroXRCE-DDS-Agent..."
cd ~
if [ ! -d "Micro-XRCE-DDS-Agent" ]; then
    git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
    cd Micro-XRCE-DDS-Agent
    mkdir build && cd build
    cmake ..
    make -j$(nproc)
    sudo make install
    sudo ldconfig /usr/local/lib/
else
    echo "Micro-XRCE-DDS-Agent already exists."
fi

# 4. Create ROS 2 Workspace for PX4 Msgs
echo "Setting up ROS 2 workspace (px4_ros_com)..."
mkdir -p ~/px4_ws/src
cd ~/px4_ws/src

# Clone PX4 msgs and ros_com repositories (Humble branch)
if [ ! -d "px4_msgs" ]; then
    git clone https://github.com/PX4/px4_msgs.git
fi
if [ ! -d "px4_ros_com" ]; then
    git clone https://github.com/PX4/px4_ros_com.git
fi

# 5. Build the Workspace
echo "Building the px4_ws..."
cd ~/px4_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install

# 6. Setup auto-source in bashrc
if ! grep -q "source ~/px4_ws/install/setup.bash" ~/.bashrc; then
    echo "source ~/px4_ws/install/setup.bash" >> ~/.bashrc
    echo "Added px4_ws to ~/.bashrc"
fi

echo "=========================================================="
echo " Setup Complete! "
echo " "
echo "To run the bridge connecting to Pixhawk via UART (TELEM2):"
echo "  MicroXRCEAgent serial --dev /dev/ttyTHS0 -b 921600"
echo "=========================================================="
