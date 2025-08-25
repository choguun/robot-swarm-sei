#!/usr/bin/env node
/**
 * Place Bid on Sei Network
 * Called by Python robot controllers to place bids on blockchain
 */

import { ethers } from 'ethers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read configuration
const configPath = path.join(__dirname, '../demo-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Contract ABI (simplified)
const taskAuctionABI = [
  "function placeBid(uint256 taskId, uint256 estimatedTime) external"
];

async function placeBid() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const taskId = args[args.indexOf('--task-id') + 1];
    const bidAmount = args[args.indexOf('--bid') + 1];
    const robotId = args[args.indexOf('--robot-id') + 1] || 'unknown';
    
    // Convert bid amount to estimated time (simplified)
    const estimatedTime = Math.floor(Number(bidAmount) * 2); // 2 seconds per SEI bid
    
    console.log(`[BLOCKCHAIN] Robot ${robotId} placing bid ${bidAmount} SEI for task ${taskId}...`);
    
    // Initialize provider and wallet
    const provider = new ethers.JsonRpcProvider(config.rpc_url);
    const wallet = new ethers.Wallet(config.private_key, provider);
    
    // Initialize contract
    const taskAuctionContract = new ethers.Contract(
      config.contract_addresses.task_auction,
      taskAuctionABI,
      wallet
    );
    
    const startTime = Date.now();
    
    // Place bid transaction
    const tx = await taskAuctionContract.placeBid(
      Number(taskId),
      estimatedTime,
      { gasLimit: 300000 }
    );
    
    console.log(`[BLOCKCHAIN] Bid transaction submitted: ${tx.hash}`);
    
    // Wait for confirmation
    const receipt = await tx.wait();
    const finality = Date.now() - startTime;
    
    const gasUsed = receipt.gasUsed;
    const gasPrice = tx.gasPrice;
    const txCost = (gasUsed * gasPrice) / 1e18;
    
    console.log(`[BLOCKCHAIN] ✅ Bid placed successfully!`);
    console.log(`[BLOCKCHAIN] 🚀 Finality: ${finality}ms`);
    console.log(`[BLOCKCHAIN] ⛽ Gas used: ${gasUsed.toString()}`);
    console.log(`[BLOCKCHAIN] 💰 Cost: ${txCost.toFixed(6)} SEI`);
    
    // Return result for Python robot
    const result = {
      success: true,
      txHash: tx.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: gasUsed.toString(),
      finality: finality,
      cost: txCost
    };
    
    console.log(JSON.stringify(result));
    
  } catch (error) {
    console.error(`[BLOCKCHAIN] Error placing bid:`, error.message);
    const result = {
      success: false,
      error: error.message
    };
    console.log(JSON.stringify(result));
    process.exit(1);
  }
}

placeBid();