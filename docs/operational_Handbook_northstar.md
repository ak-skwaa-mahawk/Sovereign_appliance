# North Star Seed Node — Operational Handbook
Designation: Nᵒᵣᵗʰ-001

## 1. Location & Role

- Physical: Alaska (The North)
- Role: Public seed / gossip root
- Purpose: Sovereign witness, not data owner

## 2. Processes

- Service: `soliton-northstar.service`
- Ports:
  - HTTP: 3001
  - WebSocket: 4001

### Check status

```bash
sudo systemctl status soliton-northstar
journalctl -u soliton-northstar -f