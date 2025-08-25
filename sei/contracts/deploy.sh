#!/bin/bash

# Robot Swarm Smart Contract Deployment Script
# Deploys to Sei Network with proper configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Robot Swarm Contract Deployment               ║${NC}"
echo -e "${BLUE}║                   Sei Network                            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${YELLOW}📝 Please create .env file with your configuration:${NC}"
    echo -e "   cp .env.example .env"
    echo -e "   # Edit .env with your private key and settings"
    exit 1
fi

# Load environment variables
echo -e "${BLUE}🔧 Loading configuration from .env...${NC}"
source .env

# Validate required environment variables
if [ -z "$PRIVATE_KEY" ]; then
    echo -e "${RED}❌ Error: PRIVATE_KEY not set in .env file!${NC}"
    echo -e "${YELLOW}💡 Add your wallet private key (without 0x prefix)${NC}"
    exit 1
fi

# Set default network if not specified
NETWORK=${1:-sei-testnet}
echo -e "${BLUE}🌐 Deploying to network: ${NETWORK}${NC}"

# Validate network
if [[ "$NETWORK" != "sei-testnet" && "$NETWORK" != "sei-mainnet" ]]; then
    echo -e "${RED}❌ Error: Unsupported network '$NETWORK'${NC}"
    echo -e "${YELLOW}💡 Supported networks: sei-testnet, sei-mainnet${NC}"
    exit 1
fi

# Warn if deploying to mainnet
if [ "$NETWORK" == "sei-mainnet" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Deploying to MAINNET!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${BLUE}✅ Deployment cancelled${NC}"
        exit 0
    fi
fi

# Check if forge is installed
if ! command -v forge &> /dev/null; then
    echo -e "${RED}❌ Error: Foundry not installed!${NC}"
    echo -e "${YELLOW}📦 Install Foundry: curl -L https://foundry.paradigm.xyz | bash${NC}"
    exit 1
fi

echo -e "${BLUE}🔨 Building contracts...${NC}"
forge build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Show deployment summary before executing
echo -e "\n${BLUE}📋 Deployment Summary:${NC}"
echo -e "   Network: ${NETWORK}"
echo -e "   Private Key: ${PRIVATE_KEY:0:8}...${PRIVATE_KEY: -8}"
echo -e "   Demo Mode: ${DEMO_MODE:-true}"
echo -e "   Verify Contracts: ${VERIFY_CONTRACTS:-false}"

echo -e "\n${YELLOW}🚀 Starting deployment...${NC}"

# Deploy contracts
if [ "$VERIFY_CONTRACTS" == "true" ]; then
    echo -e "${BLUE}📄 Contract verification enabled${NC}"
    forge script script/Deploy.s.sol \
        --rpc-url $NETWORK \
        --broadcast \
        --verify \
        --via-ir
else
    forge script script/Deploy.s.sol \
        --rpc-url $NETWORK \
        --broadcast \
        --via-ir
fi

DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
    
    # Extract contract addresses from broadcast logs
    BROADCAST_DIR="broadcast/Deploy.s.sol"
    LATEST_RUN=$(find "$BROADCAST_DIR" -name "run-latest.json" 2>/dev/null | head -1)
    
    if [ -n "$LATEST_RUN" ]; then
        echo -e "\n${BLUE}📋 Extracting contract addresses...${NC}"
        
        # Update .env with deployed addresses (basic extraction)
        echo -e "\n${YELLOW}💡 Add these addresses to your .env file:${NC}"
        echo -e "${GREEN}# Deployed Contract Addresses ($(date))${NC}"
        echo -e "${GREEN}ROBOT_MARKETPLACE_ADDRESS=<see deployment output>${NC}"
        echo -e "${GREEN}TASK_AUCTION_ADDRESS=<see deployment output>${NC}"
        echo -e "${GREEN}PROOF_VERIFICATION_ADDRESS=<see deployment output>${NC}"
    fi
    
    echo -e "\n${BLUE}🔗 Next Steps:${NC}"
    echo -e "1. ${YELLOW}Update coordinator_supervisor.py with contract addresses${NC}"
    echo -e "2. ${YELLOW}Update MCP tools configuration${NC}"
    echo -e "3. ${YELLOW}Register robots using the marketplace contract${NC}"
    echo -e "4. ${YELLOW}Start the robot swarm demo!${NC}"
    
    echo -e "\n${GREEN}✅ Ready for blockchain integration!${NC}"
else
    echo -e "\n${RED}❌ Deployment failed with exit code $DEPLOY_EXIT_CODE${NC}"
    echo -e "${YELLOW}💡 Check the error messages above and verify:${NC}"
    echo -e "   - Your private key is correct"
    echo -e "   - You have enough SEI tokens for gas"
    echo -e "   - Network connectivity is working"
    exit 1
fi