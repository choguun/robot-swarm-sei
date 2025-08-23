# Robot Swarm Coordination for Sei Network

**Autonomous Payment Robots with Robot-to-Robot Marketplaces**

A hackathon submission for The Accelerated Intelligence Project - Frontier Technology Track ($50k prize).

## 🤖 What This Is

An autonomous robot swarm system where robots independently:
- **Bid** for disaster response tasks in real-time auctions
- **Execute** missions with verifiable proof capture
- **Receive payments** automatically via Sei blockchain smart contracts
- **Build reputation** affecting future marketplace success

Built exclusively on **Sei Network** with sub-400ms finality for machine-speed coordination.

## 🚀 Quick Start

### Prerequisites
```bash
# Install Webots (simulation environment)
# Download from: https://cyberbotics.com/

# Install Node.js 18+ and Python 3.8+
node --version  # >= 18.0.0
python --version  # >= 3.8.0

# Install Foundry (smart contract toolkit)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Setup
```bash
# Clone repository
git clone https://github.com/[username]/robot-swarm-sei
cd robot-swarm-sei

# Install dependencies
npm install
pip install -r requirements.txt

# Deploy contracts to Sei testnet
npm run deploy-contracts

# Configure Sei MCP connection
npm run setup-sei-connection

# Start simulation
webots webots/worlds/disaster_city.wbt

# Run demo
npm run run-demo
```

## 🏗️ Architecture

### System Components
- **Webots Simulation**: Disaster city with autonomous robots
- **Sei Smart Contracts**: Auction, escrow, and payment systems
- **Rivalz ADCS Oracle**: Proof verification and attestation
- **MCP Integration**: Seamless blockchain operations
- **Real-time Dashboard**: Demo visualization

### Robot Types
- **UGVs (Unmanned Ground Vehicles)**: Navigation, heavy lifting, debris clearing
- **Drones**: Aerial reconnaissance, fast delivery, area scanning
- **Capabilities**: Each robot has unique speed, payload, battery, and sensor specs

## 🎯 Demo Highlights

1. **Real-time Auctions**: Robots bid for tasks based on capability and cost
2. **Sei Integration**: Sub-400ms transaction finality displayed live
3. **Autonomous Execution**: Robots navigate and capture cryptographic proofs
4. **Smart Payments**: Automatic escrow and release via attestation
5. **Market Dynamics**: Reputation systems affect bidding success

## 🧪 Testing

```bash
# Run all tests
npm test

# Test individual components
npm run test-contracts    # Smart contract tests
npm run test-mcp         # MCP tool tests
python -m pytest        # Python controller tests
```

## 📋 Development Status

- [x] Repository structure and setup
- [ ] Webots world and robot models
- [ ] Smart contract implementation
- [ ] MCP tools integration
- [ ] Robot bidding algorithms
- [ ] Proof verification system
- [ ] Demo dashboard
- [ ] Video demonstration

## 🏆 Hackathon Submission

**Track**: Frontier Technology - Robotics (Real World Agents)
**Value Prop**: Robot-to-Robot Marketplaces with Autonomous Payments
**Blockchain**: Sei Network (exclusive)
**Innovation**: Machine-speed coordination with verifiable execution

## 📞 Links

- **Sei Network**: https://sei.io/
- **Webots**: https://cyberbotics.com/
- **Rivalz ADCS**: https://rivalz.ai/
- **Hackathon Info**: https://t.me/+qrwumRQV9-A0NWVh

---

*Built for The Accelerated Intelligence Project Hackathon 2024*