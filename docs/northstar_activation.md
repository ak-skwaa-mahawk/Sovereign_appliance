# North Star Seed Node — Activation Script

## 1. Prepare

On the North Star server:

```bash
cd /opt/soliton-north-star-node
sudo -u soliton npm install
sudo -u soliton npm run build
sudo systemctl daemon-reload

sudo systemctl start soliton-northstar
sudo systemctl status soliton-northstar