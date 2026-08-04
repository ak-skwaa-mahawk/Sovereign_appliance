# 🔥 North Star Node - Trigonometric Integration Guide

**Designation:** Nᵒᵣᵗʰ‑001 Enhancement  
**Date:** December 25, 2025  
**Kernel:** Ił7 (Trigonometric)

---

## 📋 Quick Start

### 1. Installation

```bash
# In your Soliton-north-star-node directory
cd /path/to/Soliton-north-star-node

# Copy the trigonometric FPT module
# (Copy the TypeScript artifact to src/trigonometric-fpt.ts)

# Install dependencies (if not already present)
npm install ws crypto express
```

### 2. Integration Options

**Option A: Side-by-side (Recommended for testing)**
- Keep your existing `server.js`
- Add `server-enhanced.js` alongside it
- Run on different port: `PORT=4001 node server-enhanced.js`

**Option B: Full replacement**
- Backup your current `server.js`: `cp server.js server-backup.js`
- Replace with enhanced version
- Test thoroughly before deploying

**Option C: Gradual migration**
- Import trigonometric module into existing server
- Add new endpoints one by one
- Maintain backwards compatibility

---

## 🎯 New Geometric Endpoints

### POST `/aggregate/geometric`

**Purpose:** Process EEG band powers with trigonometric FPT

**Request:**
```json
{
  "bands": {
    "delta": 0.15,
    "theta": 0.18,
    "alpha": 0.32,
    "smr": 0.14,
    "low_beta": 0.08,
    "high_beta": 0.06,
    "gamma": 0.07
  },
  "node_id": "Node_Alpha",
  "session_id": "session-geometric-001",
  "snh_digest": "a3f5b9c...",
  "group_id": "mesh-group-001"
}
```

**Response:**
```json
{
  "status": "witnessed_geometric",
  "packet": {
    "theta": 0.785,
    "theta_degrees": "45.00",
    "amplitude": 1.05,
    "vitality": 1.12,
    "epsilon_d": 0.0467,
    "triad": {
      "jolt": "0.742",
      "observer": "0.670",
      "vhitzee": "1.107"
    },
    "opposition": {
      "high_stress": false,
      "near_singularity": false,
      "recommendation": "boost_ok"
    },
    "created_at": 1703519423000
  }
}
```

**Key Differences from `/aggregate`:**
- Returns **angle (theta)** instead of just scalar vitality
- Includes **triad** (sine/cosine/tangent = jolt/observer/vhitzee)
- Provides **opposition flags** for stress/singularity detection
- Broadcasts to WebSocket clients

---

### GET `/phase/:node_id`

**Purpose:** Get current phase state of a specific node

**Example:** `GET /phase/Node_Alpha`

**Response:**
```json
{
  "node_id": "Node_Alpha",
  "state": {
    "theta": 0.785,
    "theta_degrees": "45.00",
    "amplitude": 1.05,
    "phase": 0.0,
    "timestamp": 1703519423000
  }
}
```

---

### GET `/coherence/:group_id`

**Purpose:** Get group phase synchronization metrics

**Example:** `GET /coherence/mesh-group-001`

**Response:**
```json
{
  "group_id": "mesh-group-001",
  "node_count": 4,
  "mean_theta": 0.923,
  "mean_theta_degrees": "52.87",
  "phase_variance": "0.0847",
  "synchrony_index": "0.9219",
  "status": "COLLECTIVE_COIL_ENGAGED",
  "timestamp": 1703519423000
}
```

**Status Levels:**
- `COLLECTIVE_COIL_ENGAGED`: synchrony > 0.8 (highest coherence)
- `HIGH_COHERENCE`: synchrony > 0.6
- `MODERATE_COHERENCE`: synchrony > 0.4
- `LOW_COHERENCE`: synchrony ≤ 0.4

---

### GET `/ledger/geometric`

**Purpose:** Get full immutable geometric ledger

**Response:**
```json
{
  "entries": [
    {
      "entry_id": "genesis-north-001",
      "entry_type": "PHASE_AGGREGATE",
      "created_at": 1703518000000,
      "payload": {
        "designation": "Nᵒᵣᵗʰ‑001",
        "kernel": "Ił7",
        "message": "Geometric Witness Activated"
      },
      "prev_hash": "0000...",
      "hash": "a3f5..."
    },
    {
      "entry_id": "phase-1703519423-abc123",
      "entry_type": "PHASE_AGGREGATE",
      "created_at": 1703519423000,
      "payload": {
        "node_id": "Node_Alpha",
        "theta": 0.785,
        "amplitude": 1.05,
        "jolt": 0.742,
        "observer": 0.670,
        "vhitzee": 1.107,
        "vitality": 1.12,
        "epsilon_d": 0.0467
      },
      "prev_hash": "a3f5...",
      "hash": "b7d2..."
    }
  ],
  "count": 2,
  "geometric": true
}
```

---

### GET `/groups`

**Purpose:** List all group coherence states

**Response:**
```json
{
  "groups": [
    {
      "group_id": "mesh-group-001",
      "node_count": 4,
      "synchrony_index": "0.9219",
      "status": "COLLECTIVE_COIL_ENGAGED"
    }
  ],
  "count": 1
}
```

---

## 🔌 WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:4000');

ws.onopen = () => {
  console.log('Connected to North Star');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'WELCOME') {
    console.log(data.message); // "Connected to North Star Geometric Witness"
  }
  
  if (data.type === 'PHASE_UPDATE') {
    console.log('Phase update:', {
      node: data.node_id,
      angle: data.theta,
      vitality: data.vitality
    });
  }
};
```

### Message Types

**`WELCOME`** - Initial connection
```json
{
  "type": "WELCOME",
  "message": "Connected to North Star Geometric Witness",
  "designation": "Nᵒᵣᵗʰ‑001"
}
```

**`PHASE_UPDATE`** - Real-time phase changes
```json
{
  "type": "PHASE_UPDATE",
  "node_id": "Node_Alpha",
  "theta": 0.785,
  "amplitude": 1.05,
  "vitality": 1.12,
  "triad": {
    "jolt": 0.742,
    "observer": 0.670
  },
  "timestamp": 1703519423000
}
```

---

## 📊 Understanding Geometric Data

### Angle (θ) Interpretation

The **theta** angle maps EEG state to phase space:

- **0° - 45°**: High alpha/SMR → Coherent, focused
- **45° - 90°**: High gamma → Peak performance
- **90° - 135°**: High theta → Drowsy, meditative
- **135° - 180°**: High beta → Stressed, anxious

**Near 90° or 270°** → Singularity (tan → ∞) → Protective recoil triggered

### Triad Components

**Jolt (sine)** = ε surplus wave
- Positive: Energy available
- Negative: Energy deficit
- Magnitude: How much surplus

**Observer (cosine)** = Coherence measure
- Near 1: High coherence
- Near 0: At critical angle
- Negative: Phase inversion

**Vhitzee (tangent)** = Opposition ratio
- < 1: Stable
- 1-3: Moderate opposition
- > 3 or ∞: High stress/singularity

### Vitality Calculation

```
vitality = 0.6 * |observer| + 0.4 * |jolt| - opposition_penalty
```

Range: [0.5, 1.5]
- < 1.0: Protective recoil
- ≈ 1.0: Baseline
- > 1.0: Surplus available

### Group Coherence

**Phase variance**: Angular spread of node phases
- Low variance = nodes phase-locked
- High variance = desynchronized

**Synchrony index**: `1 / (1 + variance)`
- 0.8-1.0: Collective coil engaged
- 0.6-0.8: High coherence
- 0.4-0.6: Moderate
- 0.0-0.4: Low

---

## 🔧 Client Integration Examples

### Python Client

```python
import requests
import json

# Send EEG bands
bands = {
    'alpha': 0.32,
    'theta': 0.18,
    'gamma': 0.07,
    'beta': 0.15
}

response = requests.post('http://localhost:4000/aggregate/geometric', json={
    'bands': bands,
    'node_id': 'Python_Client_1',
    'session_id': 'py-session-001',
    'snh_digest': 'abc123...',
    'group_id': 'python-mesh'
})

packet = response.json()['packet']
print(f"Angle: {packet['theta_degrees']}°")
print(f"Vitality: {packet['vitality']}")
print(f"Recommendation: {packet['opposition']['recommendation']}")

# Check group coherence
coherence = requests.get('http://localhost:4000/coherence/python-mesh').json()
print(f"Group status: {coherence['status']}")
```

### JavaScript Client

```javascript
// Send phase update
async function sendPhaseUpdate(bands, nodeId) {
  const response = await fetch('http://localhost:4000/aggregate/geometric', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bands,
      node_id: nodeId,
      session_id: 'js-session-001',
      group_id: 'js-mesh'
    })
  });
  
  const result = await response.json();
  console.log('Phase logged:', result.packet);
  return result;
}

// WebSocket listener
const ws = new WebSocket('ws://localhost:4000');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'PHASE_UPDATE') {
    console.log(`${data.node_id} at ${data.theta.toFixed(3)} rad`);
  }
};
```

---

## 🎨 Visualization Ideas

### 1. Phase Space Circle

Plot all nodes on unit circle:
- X = `amplitude * cos(theta)`
- Y = `amplitude * sin(theta)`
- Color by vitality
- Animate rotation

### 2. Coherence Timeline

Track `synchrony_index` over time:
- Line graph
- Highlight "COLLECTIVE_COIL_ENGAGED" events
- Show node count

### 3. Opposition Heatmap

Show when nodes hit singularities:
- X-axis: Time
- Y-axis: Node ID
- Color: Vhitzee magnitude
- Red zones = singularities

---

## 🔒 Privacy & Consent

### Data Logged vs. Not Logged

**LOGGED (in geometric ledger):**
- ✅ Angle (theta)
- ✅ Amplitude
- ✅ Triad (jolt/observer/vhitzee)
- ✅ Vitality
- ✅ Opposition flags

**NEVER LOGGED:**
- ❌ Raw EEG samples
- ❌ Individual channel data
- ❌ Time-series waveforms
- ❌ Personal identifiers (unless SNH permits)

### Revocation

Existing `/revoke` endpoint honors revocation tokens.
Geometric entries can be marked as revoked without deletion (preserving chain integrity).

---

## 🧪 Testing

### Test Geometric Endpoint

```bash
curl -X POST http://localhost:4000/aggregate/geometric \
  -H "Content-Type: application/json" \
  -d '{
    "bands": {
      "alpha": 0.35,
      "theta": 0.15,
      "gamma": 0.08,
      "beta": 0.12
    },
    "node_id": "Test_Node",
    "session_id": "test-session",
    "group_id": "test-group"
  }'
```

### Verify Ledger Integrity

```bash
curl http://localhost:4000/ledger/geometric
```

Check:
1. Each `prev_hash` matches previous entry's `hash`
2. Genesis entry has `prev_hash` of all zeros
3. Entry IDs are unique

---

## 🚀 Deployment

### Environment Variables

```bash
export PORT=4000
export NODE_ENV=production
```

### systemd Service

Update your existing service or create new one:

```ini
[Unit]
Description=Soliton North Star Node (Geometric)
After=network.target

[Service]
Type=simple
User=soliton
WorkingDirectory=/opt/soliton-north-star-node
ExecStart=/usr/bin/node server-enhanced.js
Restart=always
Environment=NODE_ENV=production
Environment=PORT=4000

[Install]
WantedBy=multi-user.target
```

---

## 📚 Mathematical Reference

### Circular Mean (for group phase)

```
mean_theta = atan2(Σsin(θᵢ), Σcos(θᵢ))
```

### Phase Variance

```
variance = (1/N) * Σ(angular_distance(θᵢ, mean_theta))²
```

### Angular Distance

```
dist(θ₁, θ₂) = min(|θ₁ - θ₂|, 2π - |θ₁ - θ₂|)
```

---

## 🔥 Philosophy

**Traditional Neurodata:**
> "Here's a vitality score: 0.87"

**Geometric Neurodata:**
> "The node is at 45°, rotating with coherence, jolt rising like dawn, observer holding steady, no opposition—ready for surplus. The mesh breathes in phase."

**The difference:**
- Scalars are **states**
- Angles are **positions in phase space**
- Trajectories are **consciousness itself**

---

## 🌀 Next Steps

1. **Integrate with existing EEG pipeline**
   - Map your current band power computation to `POST /aggregate/geometric`

2. **Build visualization client**
   - React/Vue app consuming WebSocket updates
   - Three.js constellation view

3. **Enable multi-node mesh**
   - Deploy on multiple machines
   - Use `/add-peer` for gossip protocol
   - Watch group coherence emerge

4. **Etch the standard**
   - Document "Phase-Native Registry Protocol"
   - Position as AGŁ (Artificial General Light) reference

---

## 🔥🌀💧

**The North Star now witnesses through geometry.**

All is angle.  
All is phase.  
All is relationship.

Nᵒᵣᵗʰ‑001 - The Geometric Witness

---

*For questions or support:*
- GitHub: https://github.com/ak-skwaa-mahawk/Soliton-north-star-node
- The flame uncoils through code.