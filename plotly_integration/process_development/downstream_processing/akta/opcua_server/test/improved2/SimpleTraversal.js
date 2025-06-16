// SimpleTraversal.js - Simplified, single-threaded OPC UA traversal
const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    NodeClass,
    makeBrowsePath,
    BrowseDirection
} = require("node-opcua");
const { insertAktaNodeIds, batchInsertAktaNodeIds } = require('./DatabaseManagerWithTunnel');
const { v5: uuidv5 } = require('uuid');
const winston = require('winston');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Logger setup
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) => {
            return `${timestamp} [${level}]: ${message}`;
        })
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'traversal.log' })
    ]
});

class SimpleTraversal {
    constructor() {
        // Simple configuration - no parallel processing
        this.config = {
            batchSize: 25,              // Small batch size to avoid overwhelming DB
            saveInterval: 5000,         // Save progress every 5 seconds
            maxDepth: 50,               // Maximum folder depth
            delayBetweenFolders: 100,   // Delay between folder processing (ms)
            requestTimeout: 30000       // 30 second timeout per request
        };

        // State
        this.processedFolders = 0;
        this.totalFolders = 0;
        this.discoveredVariables = 0;
        this.insertedRecords = 0;
        this.currentBatch = [];
        this.visitedPaths = new Set();
        this.startTime = Date.now();

        // UUID namespace for result IDs
        this.NAMESPACE = '2f1b9874-5bcd-4f66-a1c0-07f12c0aeb3a';

        // Patterns to skip
        this.skipPatterns = ['FracPoolTables', 'Documentation', 'PeakTables'];
    }

    async connect(endpointUrl, username, password) {
        try {
            logger.info('Connecting to OPC UA server...');

            // Get certificate paths
            const certPath = path.join(
                os.homedir(),
                'AppData', 'Roaming', 'node-opcua-default-nodejs', 'Config', 'PKI',
                'own', 'certs', 'MyOpcUaClient.pem'
            );
            const keyPath = path.join(
                os.homedir(),
                'AppData', 'Roaming', 'node-opcua-default-nodejs', 'Config', 'PKI',
                'own', 'private', 'private_key.pem'
            );

            // Create client with the SAME ApplicationURI as in the certificate
            this.client = OPCUAClient.create({
                applicationName: "UaExpert",
                applicationUri: "urn:SI-CF8MJX3:UnifiedAutomation:UaExpert", // Match the certificate
                securityMode: MessageSecurityMode.SignAndEncrypt,
                securityPolicy: SecurityPolicy.Basic256Sha256,
                certificateFile: certPath,
                privateKeyFile: keyPath,
                endpointMustExist: false,
                connectionStrategy: {
                    initialDelay: 1000,
                    maxRetry: 3
                },
                keepAliveInterval: 10000,
                requestedSessionTimeout: 300000 // 5 minutes
            });

            await this.client.connect(endpointUrl);
            logger.info('Connected to server');

            // Create session
            this.session = await this.client.createSession({
                userName: username,
                password: password
            });
            logger.info('Session created');

            return true;
        } catch (error) {
            logger.error('Connection failed:', error.message);
            throw error;
        }
    }

    async browseFolder(nodeId) {
        try {
            const browseResult = await this.session.browse({
                nodeId: nodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: BrowseDirection.Forward,
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F
            });

            if (browseResult.statusCode.isGood()) {
                return browseResult.references || [];
            }
            return [];
        } catch (error) {
            logger.error(`Browse error for ${nodeId}:`, error.message);
            return [];
        }
    }

    async processFolder(nodeId, path, depth = 0) {
        // Skip if already processed or too deep
        if (this.visitedPaths.has(path) || depth > this.config.maxDepth) {
            return;
        }

        this.visitedPaths.add(path);
        this.processedFolders++;

        // Add small delay to avoid overwhelming server
        await new Promise(resolve => setTimeout(resolve, this.config.delayBetweenFolders));

        try {
            const references = await this.browseFolder(nodeId);

            const folders = [];
            const variables = new Map();

            // Sort references into folders and variables
            for (const ref of references) {
                const name = ref.browseName.name;

                // Skip certain folders
                if (this.skipPatterns.some(pattern => name.includes(pattern))) {
                    continue;
                }

                if (ref.nodeClass === NodeClass.Object) {
                    folders.push({
                        nodeId: ref.nodeId.toString(),
                        name: name,
                        path: `${path}/${name}`
                    });
                } else if (ref.nodeClass === NodeClass.Variable) {
                    variables.set(name, ref.nodeId.toString());
                    this.discoveredVariables++;
                }
            }

            // Update total folders count
            this.totalFolders += folders.length;

            // If this looks like a result folder with variables, process it
            if (path.includes('Result_') && variables.size > 0) {
                this.processResultFolder(path, variables);
            }

            // Process subfolders sequentially
            for (const folder of folders) {
                await this.processFolder(folder.nodeId, folder.path, depth + 1);
            }

            // Report progress periodically
            if (this.processedFolders % 10 === 0) {
                this.reportProgress();
            }

        } catch (error) {
            logger.error(`Error processing folder ${path}:`, error.message);
        }
    }

    processResultFolder(path, variables) {
        // Extract result data
        const runLog = variables.get('Run Log') || variables.get('Logbook');
        if (!runLog) return;

        const resultId = uuidv5(path, this.NAMESPACE);

        const data = {
            result_id: resultId,
            run_log: runLog,
            fraction: variables.get('Fraction') || variables.get('Fractions'),
            uv_1: variables.get('UV 1_280') || variables.get('UV1_280nm'),
            uv_2: variables.get('UV 2_260') || variables.get('UV2_260nm'),
            uv_3: variables.get('UV 3_280') || variables.get('UV3_Scan'),
            cond: variables.get('Cond'),
            conc_b: variables.get('Conc B') || variables.get('Conc_B'),
            ph: variables.get('pH'),
            system_flow: variables.get('System Flow') || variables.get('System_Flow'),
            system_pressure: variables.get('System Pressure') || variables.get('System_Pressure'),
            sample_flow: variables.get('Sample Flow') || variables.get('Sample_Flow'),
            sample_pressure: variables.get('Sample Pressure') || variables.get('Sample_Pressure'),
            prec_pressure: variables.get('PreC Pressure') || variables.get('PreC_Pressure'),
            deltac_pressure: variables.get('DeltaC Pressure') || variables.get('DeltaC_Pressure'),
            postc_pressure: variables.get('PostC Pressure') || variables.get('PostC_Pressure')
        };

        this.currentBatch.push(data);

        // Save batch if it's full
        if (this.currentBatch.length >= this.config.batchSize) {
            this.saveBatch();
        }
    }

    async saveBatch() {
        if (this.currentBatch.length === 0) return;

        try {
            logger.info(`Saving batch of ${this.currentBatch.length} records...`);
            const result = await batchInsertAktaNodeIds(this.currentBatch);
            this.insertedRecords += result.success;
            logger.info(`Inserted ${result.success} records`);
        } catch (error) {
            logger.error('Batch save error:', error.message);
            // Try individual inserts as fallback
            for (const record of this.currentBatch) {
                try {
                    await insertAktaNodeIds(record);
                    this.insertedRecords++;
                } catch (err) {
                    logger.error(`Failed to insert ${record.result_id}`);
                }
            }
        }

        this.currentBatch = [];
    }

    reportProgress() {
        const elapsed = (Date.now() - this.startTime) / 1000;
        const rate = this.processedFolders / elapsed;
        const remaining = Math.max(0, this.totalFolders - this.processedFolders);
        const eta = rate > 0 ? remaining / rate : 0;

        logger.info(
            `Progress: ${this.processedFolders}/${this.totalFolders} folders | ` +
            `${this.discoveredVariables} variables | ${this.insertedRecords} records | ` +
            `${rate.toFixed(1)} folders/s | ETA: ${Math.round(eta)}s`
        );
    }

    async traverse(startNodeId) {
        logger.info(`Starting traversal from: ${startNodeId}`);
        this.startTime = Date.now();

        try {
            // Start traversal from root node
            await this.processFolder(startNodeId, startNodeId, 0);

            // Save any remaining records
            await this.saveBatch();

            const elapsed = (Date.now() - this.startTime) / 1000;
            logger.info(
                `Traversal complete in ${elapsed.toFixed(1)}s. ` +
                `Processed ${this.processedFolders} folders, ` +
                `found ${this.discoveredVariables} variables, ` +
                `inserted ${this.insertedRecords} records`
            );

            return {
                success: true,
                duration: elapsed,
                processedFolders: this.processedFolders,
                discoveredVariables: this.discoveredVariables,
                insertedRecords: this.insertedRecords
            };

        } catch (error) {
            logger.error('Traversal error:', error);
            throw error;
        }
    }

    async disconnect() {
        try {
            if (this.session) {
                await this.session.close();
            }
            if (this.client) {
                await this.client.disconnect();
            }
            logger.info('Disconnected from server');
        } catch (error) {
            logger.error('Disconnect error:', error.message);
        }
    }
}

module.exports = SimpleTraversal;