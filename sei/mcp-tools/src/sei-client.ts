/**
 * Sei Network Client for Robot Swarm Coordination
 * Handles all blockchain interactions with sub-400ms finality tracking
 */

import { ethers } from 'ethers';
import { SeiNetworkConfig, ContractAddresses, MCPToolResponse, TransactionResult } from './types.js';

export class SeiClient {
  private provider: ethers.JsonRpcProvider;
  private wallet: ethers.Wallet;
  private contracts: {
    robotMarketplace?: ethers.Contract;
    taskAuction?: ethers.Contract;
    proofVerification?: ethers.Contract;
  } = {};

  constructor(
    private config: SeiNetworkConfig,
    private contractAddresses: ContractAddresses
  ) {
    this.provider = new ethers.JsonRpcProvider(config.rpcUrl);
    this.wallet = new ethers.Wallet(config.privateKey, this.provider);
    
    this._initializeContracts();
  }

  private _initializeContracts() {
    // Contract ABIs (simplified for key functions)
    const robotMarketplaceABI = [
      "function registerRobot(string memory robotId, uint256[] memory capabilities) external",
      "function getRobotStats(address robot) external view returns (string memory, uint256, bool, uint256, uint256, uint256)",
      "function getActiveRobots() external view returns (address[] memory)",
      "function recordTaskCompletion(address robot, bool success) external"
    ];

    const taskAuctionABI = [
      "function createTask(uint256 missionId, string memory taskType, string memory description, uint256[2] memory location, uint256[] memory requiredCapabilities, uint256 budget) external payable returns (uint256)",
      "function placeBid(uint256 taskId, uint256 estimatedTime) external",
      "function closeAuction(uint256 taskId) external",
      "function getTaskDetails(uint256 taskId) external view returns (string memory, string memory, uint256[2] memory, uint256, uint8, address, uint256, uint256)",
      "function getActiveTasks() external view returns (uint256[] memory)",
      "function submitTaskCompletion(uint256 taskId, address robot, bool success, bytes32 proofHash) external"
    ];

    const proofVerificationABI = [
      "function submitProof(uint256 taskId, bytes32 waypointsHash, bytes32[] memory imageHashes, uint256 completionTime) external",
      "function manualVerification(uint256 taskId, bool success, string memory resultMessage) external",
      "function getProofSubmission(uint256 taskId) external view returns (address, bytes32, bytes32[] memory, uint256, uint8, string memory)"
    ];

    if (this.contractAddresses.robotMarketplace) {
      this.contracts.robotMarketplace = new ethers.Contract(
        this.contractAddresses.robotMarketplace,
        robotMarketplaceABI,
        this.wallet
      );
    }

    if (this.contractAddresses.taskAuction) {
      this.contracts.taskAuction = new ethers.Contract(
        this.contractAddresses.taskAuction,
        taskAuctionABI,
        this.wallet
      );
    }

    if (this.contractAddresses.proofVerification) {
      this.contracts.proofVerification = new ethers.Contract(
        this.contractAddresses.proofVerification,
        proofVerificationABI,
        this.wallet
      );
    }
  }

  /**
   * Execute transaction with finality tracking
   */
  private async executeTransaction(
    contractMethod: any,
    methodName: string
  ): Promise<MCPToolResponse<TransactionResult>> {
    try {
      const startTime = Date.now();
      
      // Send transaction
      const tx = await contractMethod;
      console.log(`${methodName} transaction sent: ${tx.hash}`);
      
      // Wait for confirmation
      const receipt = await tx.wait(1);
      const finality = Date.now() - startTime;
      
      console.log(`${methodName} confirmed in ${finality}ms (Sei target: <400ms)`);
      
      return {
        success: true,
        data: {
          txHash: receipt.hash,
          blockNumber: receipt.blockNumber,
          gasUsed: receipt.gasUsed.toString(),
          finality
        },
        txHash: receipt.hash,
        finality
      };
      
    } catch (error: any) {
      console.error(`${methodName} failed:`, error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Register robot in marketplace
   */
  async registerRobot(robotId: string, capabilities: number[]): Promise<MCPToolResponse<TransactionResult>> {
    if (!this.contracts.robotMarketplace) {
      return { success: false, error: "RobotMarketplace contract not initialized" };
    }

    try {
      const tx = this.contracts.robotMarketplace.registerRobot(robotId, capabilities);
      return await this.executeTransaction(tx, 'registerRobot');
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Create new task
   */
  async createTask(
    missionId: number,
    taskType: string,
    description: string,
    location: [number, number],
    requiredCapabilities: number[],
    budget: string
  ): Promise<MCPToolResponse<{ taskId: number } & TransactionResult>> {
    if (!this.contracts.taskAuction) {
      return { success: false, error: "TaskAuction contract not initialized" };
    }

    try {
      const startTime = Date.now();
      
      const tx = await this.contracts.taskAuction.createTask(
        missionId,
        taskType,
        description,
        location,
        requiredCapabilities,
        budget,
        { value: budget }
      );
      
      const receipt = await tx.wait(1);
      const finality = Date.now() - startTime;
      
      // Extract task ID from logs
      const taskCreatedEvent = receipt.logs.find((log: any) => 
        log.topics[0] === ethers.id('TaskCreated(uint256,uint256,address,string,uint256[2],uint256,uint256)')
      );
      
      let taskId = 0;
      if (taskCreatedEvent) {
        const decoded = ethers.AbiCoder.defaultAbiCoder().decode(
          ['uint256', 'uint256', 'address', 'string', 'uint256[2]', 'uint256', 'uint256'],
          taskCreatedEvent.data
        );
        taskId = Number(decoded[0]);
      }
      
      console.log(`Task ${taskId} created in ${finality}ms`);
      
      return {
        success: true,
        data: {
          taskId,
          txHash: receipt.hash,
          blockNumber: receipt.blockNumber,
          gasUsed: receipt.gasUsed.toString(),
          finality
        },
        txHash: receipt.hash,
        finality
      };
      
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Place bid for task
   */
  async placeBid(taskId: number, estimatedTime: number): Promise<MCPToolResponse<TransactionResult>> {
    if (!this.contracts.taskAuction) {
      return { success: false, error: "TaskAuction contract not initialized" };
    }

    try {
      const tx = this.contracts.taskAuction.placeBid(taskId, estimatedTime);
      return await this.executeTransaction(tx, 'placeBid');
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Close auction and select winner
   */
  async closeAuction(taskId: number): Promise<MCPToolResponse<TransactionResult>> {
    if (!this.contracts.taskAuction) {
      return { success: false, error: "TaskAuction contract not initialized" };
    }

    try {
      const tx = this.contracts.taskAuction.closeAuction(taskId);
      return await this.executeTransaction(tx, 'closeAuction');
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Submit proof of task completion
   */
  async submitProof(
    taskId: number,
    waypointsHash: string,
    imageHashes: string[],
    completionTime: number
  ): Promise<MCPToolResponse<TransactionResult>> {
    if (!this.contracts.proofVerification) {
      return { success: false, error: "ProofVerification contract not initialized" };
    }

    try {
      const tx = this.contracts.proofVerification.submitProof(
        taskId,
        waypointsHash,
        imageHashes,
        completionTime
      );
      return await this.executeTransaction(tx, 'submitProof');
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Manual proof verification (for demo)
   */
  async verifyProof(taskId: number, success: boolean, result: string): Promise<MCPToolResponse<TransactionResult>> {
    if (!this.contracts.proofVerification) {
      return { success: false, error: "ProofVerification contract not initialized" };
    }

    try {
      const tx = this.contracts.proofVerification.manualVerification(taskId, success, result);
      return await this.executeTransaction(tx, 'verifyProof');
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get task details
   */
  async getTaskDetails(taskId: number): Promise<MCPToolResponse<any>> {
    if (!this.contracts.taskAuction) {
      return { success: false, error: "TaskAuction contract not initialized" };
    }

    try {
      const result = await this.contracts.taskAuction.getTaskDetails(taskId);
      
      return {
        success: true,
        data: {
          taskType: result[0],
          description: result[1],
          location: result[2],
          budget: result[3].toString(),
          state: result[4],
          assignedRobot: result[5],
          deadline: Number(result[6]),
          bidCount: Number(result[7])
        }
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get active tasks
   */
  async getActiveTasks(): Promise<MCPToolResponse<number[]>> {
    if (!this.contracts.taskAuction) {
      return { success: false, error: "TaskAuction contract not initialized" };
    }

    try {
      const result = await this.contracts.taskAuction.getActiveTasks();
      const taskIds = result.map((id: any) => Number(id));
      
      return {
        success: true,
        data: taskIds
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get active robots
   */
  async getActiveRobots(): Promise<MCPToolResponse<string[]>> {
    if (!this.contracts.robotMarketplace) {
      return { success: false, error: "RobotMarketplace contract not initialized" };
    }

    try {
      const result = await this.contracts.robotMarketplace.getActiveRobots();
      
      return {
        success: true,
        data: result
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get robot statistics
   */
  async getRobotStats(robotAddress: string): Promise<MCPToolResponse<any>> {
    if (!this.contracts.robotMarketplace) {
      return { success: false, error: "RobotMarketplace contract not initialized" };
    }

    try {
      const result = await this.contracts.robotMarketplace.getRobotStats(robotAddress);
      
      return {
        success: true,
        data: {
          robotId: result[0],
          reputation: Number(result[1]),
          isActive: result[2],
          totalTasksCompleted: Number(result[3]),
          totalTasksFailed: Number(result[4]),
          successRate: Number(result[5])
        }
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get current finality time (Sei network performance)
   */
  async getFinality(): Promise<MCPToolResponse<number>> {
    try {
      const startTime = Date.now();
      const blockNumber = await this.provider.getBlockNumber();
      const finality = Date.now() - startTime;
      
      return {
        success: true,
        data: finality
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get current gas price
   */
  async getGasPrice(): Promise<MCPToolResponse<string>> {
    try {
      const gasPrice = await this.provider.getFeeData();
      
      return {
        success: true,
        data: gasPrice.gasPrice?.toString() || '0'
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get current block number
   */
  async getBlockNumber(): Promise<MCPToolResponse<number>> {
    try {
      const blockNumber = await this.provider.getBlockNumber();
      
      return {
        success: true,
        data: blockNumber
      };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get wallet address
   */
  getWalletAddress(): string {
    return this.wallet.address;
  }

  /**
   * Get network configuration
   */
  getNetworkConfig(): SeiNetworkConfig {
    return { ...this.config, privateKey: '[REDACTED]' };
  }
}