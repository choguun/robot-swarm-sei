/**
 * Type definitions for Robot Swarm Coordination System
 * Sei Network MCP Tools
 */
export interface TaskSpec {
    missionId: number;
    taskType: string;
    description: string;
    location: [number, number];
    requiredCapabilities: number[];
    budget: string;
    priority?: number;
}
export interface BidData {
    robotId: string;
    taskId: number;
    bidAmount: number;
    estimatedTime: number;
    capabilityMatch: number;
    energyCost: number;
    reputation: number;
    batteryLevel: number;
}
export interface ProofBundle {
    taskId: number;
    robotId: string;
    waypointsHash: string;
    imageHashes: string[];
    startTime: number;
    completionTime: number;
}
export interface RobotCapabilities {
    navigation_speed: number;
    payload_capacity: number;
    battery_efficiency: number;
    terrain_adaptability: number;
    sensor_quality: number;
}
export interface TaskDetails {
    taskType: string;
    description: string;
    location: [number, number];
    budget: string;
    state: TaskState;
    assignedRobot: string;
    deadline: number;
    bidCount: number;
}
export declare enum TaskState {
    CREATED = 0,
    AUCTION_OPEN = 1,
    AUCTION_CLOSED = 2,
    ASSIGNED = 3,
    PROOF_SUBMITTED = 4,
    VERIFIED = 5,
    COMPLETED = 6,
    FAILED = 7,
    EXPIRED = 8
}
export interface TransactionResult {
    txHash: string;
    blockNumber?: number;
    gasUsed?: number;
    finality?: number;
}
export interface MissionResult extends TransactionResult {
    missionId: number;
}
export interface TaskResult extends TransactionResult {
    taskId: number;
}
export interface BidResult extends TransactionResult {
    bidId: number;
}
export interface RobotStats {
    robotId: string;
    reputation: number;
    isActive: boolean;
    totalTasksCompleted: number;
    totalTasksFailed: number;
    successRate: number;
}
export interface SeiNetworkConfig {
    rpcUrl: string;
    chainId: number;
    privateKey: string;
    gasPrice?: string;
    gasLimit?: number;
}
export interface ContractAddresses {
    robotMarketplace: string;
    taskAuction: string;
    proofVerification: string;
}
export interface MCPToolResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    txHash?: string;
    finality?: number;
}
export interface SeiMCPTools {
    createTask(spec: TaskSpec): Promise<MCPToolResponse<TaskResult>>;
    registerRobot(robotId: string, capabilities: number[]): Promise<MCPToolResponse<TransactionResult>>;
    placeBid(taskId: number, estimatedTime: number): Promise<MCPToolResponse<BidResult>>;
    closeAuction(taskId: number): Promise<MCPToolResponse<TransactionResult>>;
    selectWinner(taskId: number): Promise<MCPToolResponse<{
        winner: string;
        escrowTx: string;
    }>>;
    submitProof(proof: ProofBundle): Promise<MCPToolResponse<TransactionResult>>;
    verifyProof(taskId: number, success: boolean, result: string): Promise<MCPToolResponse<TransactionResult>>;
    escrowPayment(taskId: number, amount: string): Promise<MCPToolResponse<TransactionResult>>;
    releasePayment(taskId: number, recipient: string): Promise<MCPToolResponse<TransactionResult>>;
    getTaskDetails(taskId: number): Promise<MCPToolResponse<TaskDetails>>;
    getActiveTasks(): Promise<MCPToolResponse<number[]>>;
    getRobotStats(robotAddress: string): Promise<MCPToolResponse<RobotStats>>;
    getActiveRobots(): Promise<MCPToolResponse<string[]>>;
    getFinality(): Promise<MCPToolResponse<number>>;
    getGasPrice(): Promise<MCPToolResponse<string>>;
    getBlockNumber(): Promise<MCPToolResponse<number>>;
}
export interface TaskCreatedEvent {
    taskId: number;
    missionId: number;
    sponsor: string;
    taskType: string;
    location: [number, number];
    budget: string;
    deadline: number;
}
export interface BidPlacedEvent {
    taskId: number;
    robot: string;
    bidAmount: number;
    estimatedTime: number;
    capabilityMatch: number;
    timestamp: number;
}
export interface WinnerSelectedEvent {
    taskId: number;
    winner: string;
    winningBid: number;
    selectionTime: number;
}
export interface TaskCompletedEvent {
    taskId: number;
    robot: string;
    completionTime: number;
    payout: number;
}
export type RobotEvent = TaskCreatedEvent | BidPlacedEvent | WinnerSelectedEvent | TaskCompletedEvent;
//# sourceMappingURL=types.d.ts.map