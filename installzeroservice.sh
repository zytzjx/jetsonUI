 #!/bin/sh
sudo cp ./psirun.service /etc/systemd/system/psirun.service
sudo chmod 644 /etc/systemd/system/psirun.service
sudo systemctl daemon-reload
sudo systemctl enable psirun.service
sudo systemctl start psirun.service
