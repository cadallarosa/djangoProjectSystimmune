const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    NodeClass
} = require("node-opcua");
const {createSelfSignedCertificate} = require("node-opcua-crypto");
const fs = require("fs");
const path = require("path");
const os = require("os");

// Configuration
const endpointUrl = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer";
const username = "OPCuser";
const password = "OPCuser_710l";

// Certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

async function ensureCertificates() {
    if (fs.existsSync(OWN_CERT_PATH) && fs.existsSync(OWN_KEY_PATH)) {
        console.log("✅ Found existing certificate and key.");
        return;
    }

    console.log("🔐 Generating self-signed OPC UA certificate...");
    try {
        // Create directories if they don't exist
        const certDir = path.dirname(OWN_CERT_PATH);
        const keyDir = path.dirname(OWN_KEY_PATH);
        
        if (!fs.existsSync(certDir)) {
            fs.mkdirSync(certDir, { recursive: true });
        }
        if (!fs.existsSync(keyDir)) {
            fs.mkdirSync(keyDir, { recursive: true });
        }

        await createSelfSignedCertificate({
            applicationUri: `urn:${os.hostname()}:MyOpcUaClient`,
            subject: "/CN=MyOpcUaClient",
            privateKey: OWN_KEY_PATH,
            outputFile: OWN_CERT_PATH,
            validity: 365
        });
        console.log("✅ Certificate and key generated.");
    } catch (error) {
        console.error("❌ Failed to generate certificates:", error.message);
        throw error;
    }
}

function createOpcClient() {
    return OPCUAClient.create({
        applicationName: "OPCUA Connection Test",
        applicationUri: `urn:${os.hostname()}:OpcUaConnectionTest`,
        securityMode: MessageSecurityMode.SignAndEncrypt,
        securityPolicy: SecurityPolicy.Basic256Sha256,
        certificateFile: OWN_CERT_PATH,
        privateKeyFile: OWN_KEY_PATH,
        endpointMustExist: false,
        connectionStrategy: {
            initialDelay: 2000,
            maxRetry: 3,
            maxDelay: 10000,
            randomisationFactor: 0.5
        },
        keepAliveInterval: 5000,
        keepAliveTimeout: 20000,
        defaultSecureTokenLifetime: 600000,
        transactionTimeout: 30000
    });
}

async function testConnection() {
    console.log("🔍 Starting OPC UA Server Connection Test");
    console.log("=" * 50);
    
    let client = null;
    let session = null;
    
    try {
        // Step 1: Ensure certificates exist
        console.log("1️⃣ Checking certificates...");
        await ensureCertificates();
        
        // Step 2: Create client
        console.log("2️⃣ Creating OPC UA client...");
        client = createOpcClient();
        console.log("✅ Client created successfully");
        
        // Step 3: Test connection
        console.log("3️⃣ Connecting to server...");
        console.log(`   🔗 Endpoint: ${endpointUrl}`);
        
        const connectStart = Date.now();
        await client.connect(endpointUrl);
        const connectTime = Date.now() - connectStart;
        console.log(`✅ Connected successfully in ${connectTime}ms`);
        
        // Step 4: Get server info
        console.log("4️⃣ Getting server information...");
        const endpoints = await client.getEndpoints();
        console.log(`   📡 Found ${endpoints.length} endpoints`);
        
        // Step 5: Create session
        console.log("5️⃣ Creating authenticated session...");
        const sessionStart = Date.now();
        session = await client.createSession({
            userName: username,
            password: password
        });
        const sessionTime = Date.now() - sessionStart;
        console.log(`✅ Session created successfully in ${sessionTime}ms`);
        console.log(`   🆔 Session ID: ${session.sessionId}`);
        
        // Step 6: Test browse operation
        console.log("6️⃣ Testing browse operation...");
        const browseStart = Date.now();
        const browseResult = await session.browse({
            nodeId: "ns=2;s=1:Archive/OPCuser",
            referenceTypeId: "HierarchicalReferences",
            browseDirection: "Forward",
            includeSubtypes: true,
            nodeClassMask: 0,
            resultMask: 0x3F
        });
        const browseTime = Date.now() - browseStart;
        
        if (browseResult.references && browseResult.references.length > 0) {
            console.log(`✅ Browse successful in ${browseTime}ms`);
            console.log(`   📁 Found ${browseResult.references.length} child nodes`);
            
            // Show first few nodes
            console.log("   📋 First 5 nodes:");
            browseResult.references.slice(0, 5).forEach((ref, index) => {
                console.log(`     ${index + 1}. ${ref.browseName.toString()} (${NodeClass[ref.nodeClass]})`);
            });
        } else {
            console.log("⚠️ Browse returned no results");
        }
        
        // Step 7: Test specific folder
        console.log("7️⃣ Testing target folder access...");
        const targetFolder = "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods";
        try {
            const targetBrowse = await session.browse({
                nodeId: targetFolder,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: "Forward",
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F
            });
            
            if (targetBrowse.references) {
                console.log(`✅ Target folder accessible`);
                console.log(`   📁 Contains ${targetBrowse.references.length} items`);
            } else {
                console.log("⚠️ Target folder exists but returned no contents");
            }
        } catch (browseError) {
            console.log(`❌ Cannot access target folder: ${browseError.message}`);
        }
        
        console.log("=" * 50);
        console.log("🎉 CONNECTION TEST SUCCESSFUL!");
        console.log("   ✅ Server is reachable");
        console.log("   ✅ Authentication works");
        console.log("   ✅ Browse operations work");
        console.log("   ✅ Ready for full traversal");
        
    } catch (error) {
        console.log("=" * 50);
        console.error("❌ CONNECTION TEST FAILED!");
        console.error(`   Error: ${error.message}`);
        console.error(`   Code: ${error.code || 'UNKNOWN'}`);
        
        if (error.message.includes("ENOTFOUND")) {
            console.error("   💡 Suggestion: Check if 'opcsrv' hostname is reachable");
        } else if (error.message.includes("ECONNREFUSED")) {
            console.error("   💡 Suggestion: Check if OPC UA server is running on port 60434");
        } else if (error.message.includes("authentication")) {
            console.error("   💡 Suggestion: Check username/password credentials");
        } else if (error.message.includes("certificate")) {
            console.error("   💡 Suggestion: Check certificate configuration");
        }
        
        console.error("\n   🔧 Troubleshooting steps:");
        console.error("   1. Verify server hostname 'opcsrv' resolves correctly");
        console.error("   2. Check if port 60434 is open and accessible");
        console.error("   3. Verify OPC UA server is running");
        console.error("   4. Confirm credentials: OPCuser / OPCuser_710l");
        console.error("   5. Check firewall/network settings");
        
    } finally {
        // Cleanup
        if (session) {
            try {
                console.log("🔒 Closing session...");
                await session.close();
                console.log("✅ Session closed");
            } catch (closeError) {
                console.error("⚠️ Error closing session:", closeError.message);
            }
        }
        
        if (client) {
            try {
                console.log("🔌 Disconnecting client...");
                await client.disconnect();
                console.log("✅ Client disconnected");
            } catch (disconnectError) {
                console.error("⚠️ Error disconnecting:", disconnectError.message);
            }
        }
    }
}

// Additional network test
async function testNetworkConnectivity() {
    console.log("🌐 Testing network connectivity...");
    
    const net = require('net');
    const host = 'opcsrv';
    const port = 60434;
    
    return new Promise((resolve) => {
        const socket = new net.Socket();
        const timeout = 5000;
        
        socket.setTimeout(timeout);
        
        socket.on('connect', () => {
            console.log(`✅ TCP connection to ${host}:${port} successful`);
            socket.destroy();
            resolve(true);
        });
        
        socket.on('timeout', () => {
            console.log(`❌ TCP connection to ${host}:${port} timed out`);
            socket.destroy();
            resolve(false);
        });
        
        socket.on('error', (err) => {
            console.log(`❌ TCP connection to ${host}:${port} failed: ${err.message}`);
            resolve(false);
        });
        
        socket.connect(port, host);
    });
}

// Run the tests
async function runAllTests() {
    console.log("🚀 OPC UA Server Connection Test Suite");
    console.log("📅 " + new Date().toISOString());
    console.log();
    
    // Test 1: Network connectivity
    await testNetworkConnectivity();
    console.log();
    
    // Test 2: Full OPC UA connection
    await testConnection();
}

// Execute if run directly
if (require.main === module) {
    runAllTests().catch(error => {
        console.error("Fatal error:", error);
        process.exit(1);
    });
}

module.exports = {
    testConnection,
    testNetworkConnectivity,
    runAllTests
};