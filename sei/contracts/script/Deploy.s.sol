// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/RobotMarketplace.sol";
import "../src/TaskAuction.sol";
import "../src/ProofVerification.sol";

/**
 * @title Deploy
 * @dev Deployment script for Robot Swarm Coordination contracts on Sei Network
 */
contract Deploy is Script {
    
    // Deployment configuration
    struct DeploymentConfig {
        address deployer;
        address supervisor;
        address attestor;
        bool verifyContracts;
    }
    
    function run() external {
        // Get deployment configuration
        DeploymentConfig memory config = _getConfig();
        
        console.log("Deploying Robot Swarm Coordination System to Sei Network");
        console.log("Deployer:", config.deployer);
        console.log("Supervisor:", config.supervisor);
        console.log("Attestor:", config.attestor);
        
        vm.startBroadcast(vm.envUint("PRIVATE_KEY"));
        
        // 1. Deploy RobotMarketplace
        console.log("\n=== Deploying RobotMarketplace ===");
        RobotMarketplace marketplace = new RobotMarketplace();
        console.log("RobotMarketplace deployed at:", address(marketplace));
        
        // 2. Deploy TaskAuction with marketplace reference
        console.log("\n=== Deploying TaskAuction ===");
        TaskAuction auction = new TaskAuction(address(marketplace));
        console.log("TaskAuction deployed at:", address(auction));
        
        // 3. Deploy ProofVerification with auction reference
        console.log("\n=== Deploying ProofVerification ===");
        ProofVerification verification = new ProofVerification(address(auction));
        console.log("ProofVerification deployed at:", address(verification));
        
        // 4. Configure roles and permissions
        console.log("\n=== Configuring Roles ===");
        _configureRoles(marketplace, auction, verification, config);
        
        // 5. Initialize system
        console.log("\n=== Initializing System ===");
        _initializeSystem(marketplace, auction, verification);
        
        vm.stopBroadcast();
        
        // 6. Generate deployment summary
        _generateDeploymentSummary(marketplace, auction, verification, config);
        
        console.log("\n🎉 Deployment completed successfully!");
        console.log("Save these addresses for your application configuration.");
    }
    
    function _getConfig() internal view returns (DeploymentConfig memory) {
        address deployer = vm.addr(vm.envUint("PRIVATE_KEY"));
        
        return DeploymentConfig({
            deployer: deployer,
            supervisor: vm.envOr("SUPERVISOR_ADDRESS", deployer), // Default to deployer
            attestor: vm.envOr("ATTESTOR_ADDRESS", deployer),     // Default to deployer
            verifyContracts: vm.envOr("VERIFY_CONTRACTS", false)
        });
    }
    
    function _configureRoles(
        RobotMarketplace marketplace,
        TaskAuction auction,
        ProofVerification verification,
        DeploymentConfig memory config
    ) internal {
        bytes32 supervisorRole = keccak256("SUPERVISOR_ROLE");
        bytes32 attestorRole = keccak256("ATTESTOR_ROLE");
        
        // Grant supervisor role for task management
        if (config.supervisor != config.deployer) {
            marketplace.grantRole(supervisorRole, config.supervisor);
            auction.grantRole(supervisorRole, config.supervisor);
            console.log("Granted SUPERVISOR_ROLE to:", config.supervisor);
        }
        
        // Grant attestor role for proof verification
        if (config.attestor != config.deployer) {
            marketplace.grantRole(attestorRole, config.attestor);
            auction.grantRole(attestorRole, config.attestor);
            verification.grantRole(attestorRole, config.attestor);
            console.log("Granted ATTESTOR_ROLE to:", config.attestor);
        }
        
        console.log("Role configuration completed");
    }
    
    function _initializeSystem(
        RobotMarketplace marketplace,
        TaskAuction auction,
        ProofVerification verification
    ) internal {
        // Set up sample verification criteria for common task types
        _setupSampleVerificationCriteria(verification);
        
        console.log("System initialization completed");
    }
    
    function _setupSampleVerificationCriteria(ProofVerification verification) internal {
        // Sample task IDs for different task types
        uint256[2] memory zoneA = [uint256(600), uint256(400)]; // Zone A coordinates (scaled)
        uint256[2] memory zoneB = [uint256(1400), uint256(400)]; // Zone B coordinates
        uint256[2] memory zoneC = [uint256(1000), uint256(1600)]; // Zone C coordinates
        
        // Criteria for Zone A scanning task
        verification.setVerificationCriteria(
            1, // taskId 1
            zoneA,
            200, // 2m tolerance (scaled by 100)
            300, // 5 minutes max
            2,   // minimum 2 images
            true, // requires GPS
            true  // requires images
        );
        
        // Criteria for Zone B delivery task
        verification.setVerificationCriteria(
            2, // taskId 2
            zoneB,
            150, // 1.5m tolerance
            600, // 10 minutes max
            1,   // minimum 1 image
            true, // requires GPS
            true  // requires images
        );
        
        // Criteria for Zone C reconnaissance
        verification.setVerificationCriteria(
            3, // taskId 3
            zoneC,
            300, // 3m tolerance
            450, // 7.5 minutes max
            3,   // minimum 3 images
            true, // requires GPS
            true  // requires images
        );
        
        console.log("Sample verification criteria configured");
    }
    
    function _generateDeploymentSummary(
        RobotMarketplace marketplace,
        TaskAuction auction,
        ProofVerification verification,
        DeploymentConfig memory config
    ) internal view {
        console.log("\n╔══════════════════════════════════════════════════════════╗");
        console.log("║              DEPLOYMENT SUMMARY                          ║");
        console.log("╠══════════════════════════════════════════════════════════╣");
        console.log("║ Robot Swarm Coordination System                         ║");
        console.log("║ Deployed to Sei Network                                 ║");
        console.log("╚══════════════════════════════════════════════════════════╝");
        
        console.log("\n📋 CONTRACT ADDRESSES:");
        console.log("RobotMarketplace:", address(marketplace));
        console.log("TaskAuction:", address(auction));
        console.log("ProofVerification:", address(verification));
        
        console.log("\n🔐 ROLE ASSIGNMENTS:");
        console.log("Admin:", config.deployer);
        console.log("Supervisor:", config.supervisor);
        console.log("Attestor:", config.attestor);
        
        console.log("\n⚙️  CONFIGURATION:");
        console.log("Auction Duration: 30 seconds");
        console.log("Task Timeout: 300 seconds (5 minutes)");
        console.log("Verification Timeout: 60 seconds");
        
        console.log("\n🤖 NEXT STEPS:");
        console.log("1. Update your MCP tools with these contract addresses");
        console.log("2. Configure robot controllers with the marketplace address");
        console.log("3. Set up Rivalz ADCS oracle integration if using external verification");
        console.log("4. Register robots in the marketplace");
        console.log("5. Create your first mission and start the demo!");
        
        console.log("\n💡 USEFUL COMMANDS:");
        console.log("Register Robot:");
        console.log("  cast send", address(marketplace), '"registerRobot(string,uint256[])"', '"robot_1"', '"[120,100,80,90,85]"');
        console.log("\nCreate Task:");
        console.log("  cast send", address(auction), '"createTask(uint256,string,string,uint256[2],uint256[],uint256)"', 
                   "1", '"scan"', '"Scan Zone A"', '"[600,400]"', '"[100,80,70,80,70]"', "1000000000000000000");
        
        console.log("\n🌐 NETWORK INFO:");
        console.log("Network: Sei Testnet");
        console.log("Chain ID:", block.chainid);
        console.log("Block Number:", block.number);
        console.log("Timestamp:", block.timestamp);
    }
}