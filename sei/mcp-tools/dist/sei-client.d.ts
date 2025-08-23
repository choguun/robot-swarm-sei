/**
 * Sei Network Client for Robot Swarm Coordination
 * Handles all blockchain interactions with sub-400ms finality tracking
 */
import { SeiNetworkConfig, ContractAddresses, MCPToolResponse, TransactionResult } from './types.js';
export declare class SeiClient {
    private config;
    private contractAddresses;
    private provider;
    private wallet;
    private contracts;
    constructor(config: SeiNetworkConfig, contractAddresses: ContractAddresses);
    private _initializeContracts;
    /**
     * Execute transaction with finality tracking
     */
    private executeTransaction;
    /**
     * Register robot in marketplace
     */
    registerRobot(robotId: string, capabilities: number[]): Promise<MCPToolResponse<TransactionResult>>;
    /**
     * Create new task
     */
    createTask(missionId: number, taskType: string, description: string, location: [number, number], requiredCapabilities: number[], budget: string): Promise<MCPToolResponse<{
        taskId: number;
    } & TransactionResult>>;
    /**
     * Place bid for task
     */
    placeBid(taskId: number, estimatedTime: number): Promise<MCPToolResponse<TransactionResult>>;
    /**
     * Close auction and select winner
     */
    closeAuction(taskId: number): Promise<MCPToolResponse<TransactionResult>>;
    /**
     * Submit proof of task completion
     */
    submitProof(taskId: number, waypointsHash: string, imageHashes: string[], completionTime: number): Promise<MCPToolResponse<TransactionResult>>;
    /**
     * Manual proof verification (for demo)
     */
    verifyProof(taskId: number, success: boolean, result: string): Promise<MCPToolResponse<TransactionResult>>;
    /**
     * Get task details
     */
    getTaskDetails(taskId: number): Promise<MCPToolResponse<any>>;
    /**
     * Get active tasks
     */
    getActiveTasks(): Promise<MCPToolResponse<number[]>>;
    /**
     * Get active robots
     */
    getActiveRobots(): Promise<MCPToolResponse<string[]>>;
    /**
     * Get robot statistics
     */
    getRobotStats(robotAddress: string): Promise<MCPToolResponse<any>>;
    /**
     * Get current finality time (Sei network performance)
     */
    getFinality(): Promise<MCPToolResponse<number>>;
    /**
     * Get current gas price
     */
    getGasPrice(): Promise<MCPToolResponse<string>>;
    /**
     * Get current block number
     */
    getBlockNumber(): Promise<MCPToolResponse<number>>;
    /**
     * Get wallet address
     */
    getWalletAddress(): string;
    /**
     * Get network configuration
     */
    getNetworkConfig(): SeiNetworkConfig;
}
//# sourceMappingURL=sei-client.d.ts.map