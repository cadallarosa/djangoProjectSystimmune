const path = require("path");
const os = require("os");

// Platform-safe certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const config = {
    opcua: {
        endpointUrl: "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer",
        applicationName: "OPCUA Browser",
        applicationUri: "urn:SI-CF8MJX3:UnifiedAutomation:UaExpert",
        certificateFile: path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem"),
        privateKeyFile: path.join(CERT_FOLDER, "own", "private", "private_key.pem"),
        connectionTimeout: 60000,
        sessionTimeout: 3600000,
        keepAliveInterval: 5000,
        keepAliveTimeout: 60000,
        defaultSecureTokenLifetime: 3600000,
        transactionTimeout: 60000,
        timeout: 24 * 60 * 60 * 1000,
        maxRetries: 5,
        retryDelay: 2000,
        initialDelay: 2000,
        maxDelay: 60000,
        randomisationFactor: 0.5
    },
    
    database: {
        host: '127.0.0.1',
        port: 3306,
        user: 'cdallarosa',
        password: '$ystImmun3!2022',
        database: 'djangoP1_db',
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
        // Removed invalid MySQL2 options: acquireTimeout, timeout, reconnect, etc.
    },
    
    traversal: {
        maxDepth: 100,
        batchSize: 1000,
        checkpointInterval: 2000,
        maxVariablesToFind: 50000,
        cacheExpiry: 30000,
        operationTimeout: 60000,
        healthCheckInterval: 30000,
        endBranchVariable: "UV 1_280",
        skippedFolders: ["FracPoolTables", "Documentation", "PeakTables"],
        timeout: 24 * 60 * 60 * 1000
    },
    
    folders: [
        "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods"
    ],
    
    server: {
        host: "0.0.0.0",
        port: 3000
    },
    
    files: {
        selectedVariables: "variables.json",
        logFile: "akta_logs.log"
    },
    
    python: {
        scriptPath: "read_historical_data.py",
        timeout: 600000 // 10 minutes
    }
};

module.exports = config;