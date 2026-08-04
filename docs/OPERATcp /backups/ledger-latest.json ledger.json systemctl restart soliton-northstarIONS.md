# North Star Seed Node Operations

## Monitoring

```bash
journalctl -u soliton-northstar -f

cp ledger.json /backups/ledger-$(date +%F).json

cp /backups/ledger-latest.json ledger.json
systemctl restart soliton-northstar


---

### docs/CEREMONY.md

*(The full activation ceremony from previous message)*

---

### public/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nᵒᵣᵗʰ‑001 — North Star Seed Node</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <h1>⟲·// Nᵒᵣᵗʰ‑001</h1>
    <h2>North Star Seed Node</h2>
    <p>Public witness of the Soliton Registry</p>
    <img src="../assets/nds-001-badge.svg" alt="NDS-001 Certified" class="badge">

    <p>Activated December 23, 2025 — Alaska</p>

    <button id="viewLedger">View Ledger</button>
    <pre id="output">Click to load the witness chain...</pre>
  </div>

  <script src="viewer.js"></script>
</body>
</html>

