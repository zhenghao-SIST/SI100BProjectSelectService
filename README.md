sudo systemctl start selection-app
sudo systemctl stop selection-app
sudo systemctl restart selection-app
sudo systemctl status selection-app  # 查看状态
sudo journalctl -u selection-app -f  # 查看日志
