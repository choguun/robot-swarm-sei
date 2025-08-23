/**
 * Type definitions for Robot Swarm Coordination System
 * Sei Network MCP Tools
 */
export var TaskState;
(function (TaskState) {
    TaskState[TaskState["CREATED"] = 0] = "CREATED";
    TaskState[TaskState["AUCTION_OPEN"] = 1] = "AUCTION_OPEN";
    TaskState[TaskState["AUCTION_CLOSED"] = 2] = "AUCTION_CLOSED";
    TaskState[TaskState["ASSIGNED"] = 3] = "ASSIGNED";
    TaskState[TaskState["PROOF_SUBMITTED"] = 4] = "PROOF_SUBMITTED";
    TaskState[TaskState["VERIFIED"] = 5] = "VERIFIED";
    TaskState[TaskState["COMPLETED"] = 6] = "COMPLETED";
    TaskState[TaskState["FAILED"] = 7] = "FAILED";
    TaskState[TaskState["EXPIRED"] = 8] = "EXPIRED";
})(TaskState || (TaskState = {}));
//# sourceMappingURL=types.js.map