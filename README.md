# AI Robot Swarm & Blockchain Marketplace

**Autonomous Payment Robots with Individual AI Brains and Blockchain Wallets**

A hackathon submission for The Accelerated Intelligence Project - Frontier Technology Track ($50k prize).

## 🤖 What This Is

A **complete autonomous robot marketplace ecosystem** where individual AI-powered robots:
- **🧠 Think independently** using Swarms framework + Q-Network reinforcement learning
- **💳 Own blockchain wallets** with unique Sei Network addresses for autonomous transactions  
- **🎯 Bid competitively** for disaster response tasks using AI-optimized strategies
- **🚀 Execute missions autonomously** with real-time navigation and obstacle avoidance
- **🔐 Generate cryptographic proofs** of task completion with GPS waypoints and camera evidence
- **⚡ Receive instant payments** via smart contracts with sub-400ms Sei Network finality

**🏆 World's First**: Individual robots operating as independent economic agents with their own AI personalities and blockchain wallets.

## 🚀 Quick Demo (Ready to Run!)

### Prerequisites
```bash
# 1. Install Webots R2023b+ (simulation environment)
# Download from: https://cyberbotics.com/

# 2. Install Python 3.8+ with pip
python --version  # >= 3.8.0
```

### Setup (2 minutes)
```bash
# 1. Clone and install dependencies
git clone <your-repo-url>
cd robot-swarm-sei
pip install -r requirements.txt

# 2. Configure Webots Python path
# Open Webots → Preferences → Python command
# Set to: /Users/your-username/path/to/robot-swarm-sei/webots/controllers/python
```

### Run Demo (30 seconds to launch)
```bash
# 1. Start Webots and open the demo world
webots webots/worlds/swarm_demo.wbt

# 2. Click the Play button ▶️ 

# 3. Watch the magic happen!
# ✅ 3 robots initialize with individual wallets
# ✅ Real blockchain transactions on Sei testnet  
# ✅ AI-powered autonomous bidding and navigation
# ✅ Live console output with transaction hashes
```

### Expected Demo Output
```bash
[COORDINATOR] 🏦 Coordinator Address: 0x0ad11f643df3d9f...
[ugv_alpha] 💳 Wallet Address: 0x37E01bF3888F200d...
[ugv_beta] 💳 Wallet Address: 0x3BD91974F74dF7F0...
[ugv_gamma] 💳 Wallet Address: 0xAEdfb15F457bf3cf...

[TASK_AUCTION] 🚀 Creating task for mission 1
[SMART_CONTRACT] 📤 Task creation: 0x8e449f604d2689372e8f...
[TASK_AUCTION] ✅ Task created successfully!

[ugv_alpha] 🤖 Received auction for task 1
[ugv_alpha] 💰 AI calculated optimal bid: 0.0045 SEI
[ugv_alpha] ⬆️ Moving FORWARD: target Y=2.50
[ugv_alpha] 📍 Arrived at Zone A - capturing proof
```

## 🏗️ Current Implementation

### ✅ **Fully Operational System Components**
- **🎮 Webots Simulation**: `swarm_demo.wbt` with colored task zones (RED/GREEN/BLUE)
- **⛓️ Sei Smart Contracts**: Live deployed contracts on Sei testnet with real transactions
  - RobotMarketplace: `0x839e6aD668FB67684Cd0D21E6f17566f4607E325`
  - TaskAuction: `0xD894daADD0CDD01a9B65Dc72ffE8023eCd3B75c4`  
  - ProofVerification: `0x34a820CCe01808b06994eb1EF2fD2f6Bf9C0AFBa`
- **🧠 AI Framework**: Swarms + Q-Network RL for autonomous decision making
- **💳 Individual Wallets**: Each robot has unique Sei-compatible wallet and private key
- **🔐 Cryptographic Proofs**: SHA256 hashing of GPS waypoints + camera evidence
- **⚡ Real-time Integration**: Sub-400ms blockchain finality with live transaction monitoring

### 🤖 **Active Robot Fleet**
- **UGV Alpha** (RED zone specialist): `0x37E01bF3888F200d3a17936Bc9458c7656679179`
  - Capabilities: Fast navigation, terrain adaptability, scan missions
  - AI Personality: Aggressive bidder, high-speed execution
  
- **UGV Beta** (GREEN zone specialist): `0x3BD91974F74dF7F014EAC3747e50819375667881`  
  - Capabilities: High payload, advanced sensors, delivery missions
  - AI Personality: Strategic bidder, quality-focused execution
  
- **UGV Gamma** (BLUE zone specialist): `0xAEdfb15F457bf3cfe9453af8514Dd9AfA0CF9196`
  - Capabilities: Energy efficient, long endurance, reconnaissance
  - AI Personality: Conservative bidder, reliable completion

## 🎯 Live Demo Features

### **🎪 What You'll See in the Simulation**
1. **🎨 Obvious Visual Coordination**: 3 colored zones (RED/GREEN/BLUE) with robots moving to assigned areas
2. **💳 Individual Wallet Addresses**: Each robot displays unique Sei address in console
3. **⚡ Real Blockchain Transactions**: Live transaction hashes from Sei testnet (`0x8e449f...`)
4. **🧠 AI Decision Making**: Robots calculate optimal bids using machine learning algorithms  
5. **🚀 Visible Robot Movement**: 6.0 rad/s motor speeds ensure robots move visibly in GUI
6. **🔐 Cryptographic Proofs**: SHA256 hashes generated for waypoints and camera evidence
7. **📊 Performance Metrics**: Sub-400ms Sei Network finality displayed in real-time

### **⚡ Sei Network Integration (Live)**
- **Chain**: Sei Testnet (EVM-compatible)
- **RPC**: `https://evm-rpc-testnet.sei-apis.com`
- **Chain ID**: 1328
- **Finality**: <400ms measured average
- **Task Budgets**: 0.005 SEI per task (ultra-low for demo sustainability)
- **Transaction Types**: Task creation, bidding, winner selection, proof submission, payments


### **Smart Contract Verification (Optional)**
```bash
# Verify deployed contracts on Sei testnet
cd sei/contracts
forge script script/Deploy.s.sol --rpc-url https://evm-rpc-testnet.sei-apis.com
```

## 📊 Current Implementation Status

### ✅ **COMPLETED (95%)**
- [x] **Webots simulation** with colored task zones and 3 robots
- [x] **Smart contract ecosystem** deployed live on Sei testnet
- [x] **Individual robot wallets** with unique private keys and addresses
- [x] **AI framework integration** (Swarms + Q-Network RL)
- [x] **Real blockchain transactions** with live transaction hashes
- [x] **Autonomous bidding system** with ML-optimized strategies
- [x] **Cryptographic proof system** with SHA256 + digital signatures
- [x] **Visible robot movement** with physics-tested motor speeds
- [x] **Environment configuration** with secure .env management
- [x] **Performance monitoring** with sub-400ms finality tracking
- [x] **Complete documentation** with system architecture diagrams

### 🎯 **DEMO READY**
- [x] **3-minute live demonstration** ready to execute
- [x] **Real-time console output** with blockchain transaction hashes
- [x] **Individual robot personalities** with distinct AI behaviors
- [x] **Machine-speed coordination** with sub-second response times

## 🏆 Hackathon Submission Details

### **🎯 Track Alignment**
- **Track**: Frontier Technology - Robotics (Real World Agents)  
- **Category**: Autonomous Payment Robots, Robot-to-Robot Marketplaces
- **Innovation**: Individual AI agents with blockchain wallets operating as independent economic actors

### **🚀 Technical Achievements**
- **World's First**: Individual robots with AI brains and blockchain wallets making autonomous transactions
- **Real Deployment**: Live smart contracts on Sei testnet with actual transaction hashes
- **Machine-Speed Coordination**: Sub-400ms blockchain finality for real-time robot coordination
- **Cryptographic Verification**: Tamper-evident proofs of physical world task completion
- **Multi-Agent AI**: Swarms framework + Q-Network RL for collaborative intelligence

### **💎 Sei Network Integration**
- **Exclusive Build**: Built specifically for Sei Network to demonstrate EVM compatibility
- **Performance Showcase**: Leverages Sei's twin-turbo consensus for sub-second finality
- **Economic Innovation**: Real SEI token transactions between autonomous robot agents
- **Scalability Demo**: Concurrent robot operations with individual wallet management

## 🔗 Key Resources

- **📋 Complete Documentation**: [AI_SWARM_SYSTEM_DOCUMENTATION.md](AI_SWARM_SYSTEM_DOCUMENTATION.md)
- **🎨 Architecture Diagrams**: [SYSTEM_ARCHITECTURE_DIAGRAM.md](SYSTEM_ARCHITECTURE_DIAGRAM.md)  
- **⚡ Implementation Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **🌐 Sei Network**: https://sei.io/
- **🤖 Webots Simulator**: https://cyberbotics.com/
- **🧠 Swarms Framework**: https://github.com/kyegomez/swarms

## 🎪 Live Demo Instructions

**Ready to run in 30 seconds:**
1. Install Webots R2023b+ 
2. Open `webots/worlds/swarm_demo.wbt`
3. Set Python path to `webots/controllers/python`  
4. Click Play ▶️
5. Watch 3 AI robots with individual wallets bid for tasks and execute missions with real blockchain transactions!

---

**🤖 The future of autonomous agent economies starts here - robots that think, bid, work, and get paid independently at machine speed.**

*Built for The Accelerated Intelligence Project Hackathon 2024*