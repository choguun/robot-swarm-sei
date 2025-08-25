# Robot Swarm Smart Contracts

Smart contracts for autonomous robot coordination and payments on Sei Network, built for sub-400ms finality and machine-speed transactions.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Run setup assistant
./setup.sh

# Or manually copy and configure
cp .env.example .env
# Edit .env with your private key
```

### 2. Deploy Contracts
```bash
# Deploy to Sei testnet (recommended)
./deploy.sh

# Deploy to Sei mainnet (production)
./deploy.sh sei-mainnet
```

### 3. Integration
- Update coordinator with deployed contract addresses
- Configure MCP tools with new addresses  
- Register robots and start demo!

## 📋 Prerequisites

- **Foundry**: Smart contract toolkit
- **Sei Wallet**: With private key and testnet SEI tokens
- **Node.js 18+**: For MCP integration

### Install Foundry
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Get Testnet Tokens
Visit [Sei Faucet](https://faucet.sei-apis.com/) and request testnet SEI tokens.

## 🏗️ Contract Architecture

### Core Contracts

#### `RobotMarketplace.sol`
- Robot registration and capability tracking
- Reputation system with task completion history
- Active robot discovery and statistics

#### `TaskAuction.sol` 
- Task creation with escrow mechanism
- Real-time bidding system with automatic winner selection
- Payment release on task completion

#### `ProofVerification.sol`
- Cryptographic proof submission and validation
- Integration with Rivalz ADCS oracle network
- Automated verification with manual fallback

## ⚙️ Configuration

### Environment Variables (.env)

**Required:**
```bash
PRIVATE_KEY=your_wallet_private_key_without_0x_prefix
```

**Optional:**
```bash
# Network settings (pre-configured)
SEI_TESTNET_RPC=https://evm-rpc-testnet.sei-apis.com
SEI_TESTNET_CHAIN_ID=1329

# Contract verification
SEI_ETHERSCAN_API_KEY=your_seitrace_api_key

# System parameters
DEMO_MODE=true
AUCTION_DURATION=30
PLATFORM_FEE_BPS=200
```

### Deployment Configuration

The deployment script automatically:
- ✅ Deploys all three contracts with proper linking
- ✅ Configures roles and permissions  
- ✅ Sets up sample verification criteria
- ✅ Outputs integration information

## 🔧 Manual Operations

### Register Robot
```bash
cast send $MARKETPLACE_ADDRESS \
  "registerRobot(string,uint256[])" \
  "ugv_alpha" \
  "[120,100,80,90,85]" \
  --rpc-url sei-testnet \
  --private-key $PRIVATE_KEY
```

### Create Task
```bash
cast send $AUCTION_ADDRESS \
  "createTask(uint256,string,string,uint256[2],uint256[],uint256)" \
  1 \
  "scan" \
  "Scan disaster zone A" \
  "[600,400]" \
  "[100,80,70,80,70]" \
  "1000000000000000000" \
  --value 1000000000000000000 \
  --rpc-url sei-testnet \
  --private-key $PRIVATE_KEY
```

### Place Bid
```bash
cast send $AUCTION_ADDRESS \
  "placeBid(uint256,uint256)" \
  1 \
  120 \
  --rpc-url sei-testnet \
  --private-key $PRIVATE_KEY
```

## 🔍 Contract Verification

After deployment, verify contracts on Seitrace:

```bash
forge verify-contract \
  --chain-id 1329 \
  --num-of-optimizations 1000 \
  --constructor-args $CONSTRUCTOR_ARGS \
  $CONTRACT_ADDRESS \
  src/RobotMarketplace.sol:RobotMarketplace \
  --etherscan-api-key $SEI_ETHERSCAN_API_KEY
```

## 📊 Performance Metrics

### Sei Network Advantages
- **Finality**: <400ms average transaction confirmation
- **Gas Costs**: ~0.01 SEI per transaction (~$0.0001)
- **Throughput**: 5,000+ TPS capability
- **EVM Compatible**: Full Ethereum tooling support

### Gas Estimates
| Operation | Gas Used | Cost (SEI) |
|-----------|----------|------------|
| Register Robot | ~80,000 | ~0.008 |
| Create Task | ~120,000 | ~0.012 |
| Place Bid | ~50,000 | ~0.005 |
| Submit Proof | ~90,000 | ~0.009 |

## 🔐 Security Features

- **Role-based Access Control**: Admin, Supervisor, Attestor roles
- **Escrow Protection**: Funds locked until task completion
- **Proof Requirements**: Cryptographic validation mandatory
- **Timeout Handling**: Automatic re-auction on failures
- **Reentrancy Guards**: Protection against common attacks

## 🧪 Testing

```bash
# Run all tests
forge test

# Run with gas reporting
forge test --gas-report

# Run specific test file
forge test --match-path test/TaskAuction.t.sol

# Fork testing against live network
forge test --fork-url sei-testnet
```

## 📁 Project Structure

```
sei/contracts/
├── src/                    # Smart contract sources
│   ├── RobotMarketplace.sol
│   ├── TaskAuction.sol
│   └── ProofVerification.sol
├── script/
│   └── Deploy.s.sol       # Deployment script
├── test/                  # Contract tests (optional)
├── .env                   # Environment configuration
├── .env.example          # Configuration template
├── deploy.sh             # Deployment helper
├── setup.sh              # Setup assistant
└── foundry.toml          # Foundry configuration
```

## 🚨 Security Notes

- **Never commit .env files** - they contain private keys
- **Use separate wallets** for testing vs production
- **Verify contract addresses** before integration
- **Test thoroughly** on testnet before mainnet deployment
- **Keep private keys secure** and backed up

## 🆘 Troubleshooting

### Common Issues

**❌ "Private key not found"**
```bash
# Check .env file exists and contains PRIVATE_KEY
cat .env | grep PRIVATE_KEY
```

**❌ "Insufficient funds for gas"**
```bash
# Get testnet tokens from faucet
# Check balance
cast balance $YOUR_ADDRESS --rpc-url sei-testnet
```

**❌ "Contract not found"**
```bash
# Verify deployment succeeded
cast code $CONTRACT_ADDRESS --rpc-url sei-testnet
```

**❌ "Network timeout"**
```bash
# Try alternative RPC endpoint
# Check Sei network status
```

### Getting Help

- **Documentation**: [Sei Network Docs](https://docs.sei.io/)
- **Faucet**: [Get Testnet Tokens](https://faucet.sei-apis.com/)
- **Explorer**: [Seitrace](https://seitrace.com/)
- **RPC Status**: [Sei API Status](https://status.sei-apis.com/)

## 🎯 Integration Guide

After successful deployment:

1. **Update Coordinator**: Add contract addresses to `coordinator_supervisor.py`
2. **Configure MCP Tools**: Update `sei-client.ts` with addresses  
3. **Set Demo Mode**: Change `demo_mode: false` for live blockchain calls
4. **Register Robots**: Use marketplace contract to register your robot fleet
5. **Start Demo**: Launch Webots simulation and watch live transactions!

---

**🤖 Ready to deploy autonomous robot payments on Sei Network!** 

The contracts are optimized for machine-speed transactions with sub-400ms finality - perfect for real-time robot coordination and instant payments.