if [ $1 = "top" ]; then
    sudo cp ./psiruntop.service /etc/systemd/system/psirun.service
else
    sudo cp ./psirun.service /etc/systemd/system/psirun.service
fi
sudo chmod 644 /etc/systemd/system/psirun.service
sudo systemctl daemon-reload
sudo systemctl enable psirun.service
sudo systemctl start psirun.service
