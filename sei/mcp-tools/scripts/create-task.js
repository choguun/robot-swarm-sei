#!/usr/bin/env node
/**
 * Create Task on Sei Network
 * Called by Python coordinator to create tasks on blockchain
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
  "function createTask(uint256 missionId, string memory taskType, string memory description, uint256[2] memory location, uint256[] memory requiredCapabilities, uint256 budget) external payable returns (uint256)"
];

async function createTask() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const taskId = args[args.indexOf('--task-id') + 1];
    const taskType = args[args.indexOf('--type') + 1];
    const description = args[args.indexOf('--description') + 1] || `Task ${taskId}`;
    const locationStr = args[args.indexOf('--location') + 1];
    const budget = args[args.indexOf('--budget') + 1];
    
    // Parse location
    const [x, y] = locationStr.split(',').map(Number);
    const location = [Math.floor(x * 100), Math.floor(y * 100)]; // Scale coordinates
    
    // Default capabilities
    const requiredCapabilities = [100, 80, 70, 80, 70];
    const budgetWei = ethers.parseEther(budget || "0.001");
    
    console.log(`[BLOCKCHAIN] Creating task ${taskId} on Sei Network...`);
    console.log(`[BLOCKCHAIN] Type: ${taskType}, Location: [${location}], Budget: ${budget} SEI`);
    
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
    
    // Create task transaction
    const tx = await taskAuctionContract.createTask(
      1, // missionId 
      taskType,
      description,
      location,
      requiredCapabilities,
      budgetWei,
      { value: budgetWei, gasLimit: 500000 }
    );
    
    console.log(`[BLOCKCHAIN] Transaction submitted: ${tx.hash}`);
    
    // Wait for confirmation
    const receipt = await tx.wait();
    const finality = Date.now() - startTime;
    
    const gasUsed = receipt.gasUsed;
    const gasPrice = tx.gasPrice;
    const txCost = (gasUsed * gasPrice) / 1e18;
    
    console.log(`[BLOCKCHAIN] ✅ Task created successfully!`);
    console.log(`[BLOCKCHAIN] 🚀 Finality: ${finality}ms`);
    console.log(`[BLOCKCHAIN] ⛽ Gas used: ${gasUsed.toString()}`);
    console.log(`[BLOCKCHAIN] 💰 Cost: ${txCost.toFixed(6)} SEI`);
    console.log(`[BLOCKCHAIN] 📝 Block: ${receipt.blockNumber}`);
    
    // Return result for Python coordinator
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
    console.error(`[BLOCKCHAIN] Error creating task:`, error.message);
    const result = {
      success: false,
      error: error.message
    };
    console.log(JSON.stringify(result));
    process.exit(1);
  }
}

createTask();