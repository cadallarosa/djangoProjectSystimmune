const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    BrowseDirection,
    NodeClassMask,
    NodeClass,
    makeBrowsePath,
    StatusCodes
} = require("node-opcua-client");
const winston = require('winston');
const path = require('path');
const LRU = require('lru-cache');
const pLimit = require('p-limit');
const { insertAktaNodeIds, batchInsertAktaNodeIds } = require('./DatabaseManagerWithTunnel');
const { triggerDjangoImport } = require('./djangoIntegration');
const { getCertificatePaths } = require('./CertificateManager');

// Enhanced logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
            const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
            return `${timestamp} [${level}]: ${message}${metaStr}`;
        })
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({
            filename: path.join(__dirname, 'logs', 'traversal.log'),
            maxsize: 10485760, // 10MB
            maxFiles: 5
        })
    ]
});

class OptimizedTraversal {
    constructor() {
        this.config = {
            maxConcurrentBrowse: 3,         // Reduced for stability
            batchSize: 50,                  // Database batch size
            cacheSize: 5000,               // LRU cache size
            browseTimeout: 30000,          // Browse operation timeout
            sessionPoolSize: 2,            // Number of concurrent sessions
            checkpointInterval: 5000,      // Progress checkpoint interval
            maxRetries: 3,                 // Max retries per operation
            retryDelay: 2000,             // Base retry delay
            maxDepth: 100,                // Max traversal depth
            progressReportInterval: 2000,  // Progress report interval
            sessionTimeout: 60000,         // Session timeout
            requestTimeout: 30000,         // Individual request timeout
            parallelTraversals: 1          // Number of parallel traversals (configurable)
        };

        this.cache = new LRU({ max: this.config.cacheSize });
        this.sessionPool = [];
        this.browseLimit = pLimit(this.config.maxConcurrentBrowse);

        this.state = {
            processedNodes: new Set(),
            discoveredVariables: 0,
            insertedRecords: 0,
            errors: 0,
            folderQueue: [],
            pendingBatches: [],
            checkpointFile: path.join(__dirname, 'logs', 'traversal_checkpoint.json'),
            totalFolders: 0,
            processedFolders: 0,
            resultGroups: new Map(),
            skippedBranches: 0,
            startTime: Date.now()
        };

        this.client = null;
        this.progressTimer = null;
        this.batchTimer = null;
    }

    async initialize(endpointUrl, username, password) {
        try {
            logger.info('Initializing OPC UA client...');

            const certificatePaths = await getCertificatePaths();

            this.client = OPCUAClient.create({
                applicationName: "Optimized OPCUA Browser",
                applicationUri: `urn:OptimizedOPCUABrowser`,
                securityMode: MessageSecurityMode.SignAndEncrypt,
                securityPolicy: SecurityPolicy.Basic256Sha256,
                certificateFile: certificatePaths.cert,
                privateKeyFile: certificatePaths.key,
                endpointMustExist: false,
                connectionStrategy: {
                    initialDelay: 2000,
                    maxRetry: 10,
                    maxDelay: 30000
                },
                keepAliveInterval: 10000,
                requestedSessionTimeout: 600000,  // 10 minutes
                timeout: 60000,
                defaultSecureTokenLifetime: 600000
            });

            // Connect to server
            await this.client.connect(endpointUrl);
            logger.info('Connected to OPC UA server');

            // Create session pool
            for (let i = 0; i < this.config.sessionPoolSize; i++) {
                const session = await this.client.createSession({
                    userName: username,
                    password: password
                });
                this.sessionPool.push(session);
            }
            logger.info(`Created ${this.sessionPool.length} sessions in pool`);

            // Start batch processing timer
            this.batchTimer = setInterval(() => this.processBatch(), 10000);

            // Start progress reporting
            this.progressTimer = setInterval(() => this.reportProgress(), this.config.progressReportInterval);

        } catch (error) {
            logger.error('Failed to initialize:', error);
            throw error;
        }
    }

    getAvailableSession() {
        // Round-robin session selection
        const session = this.sessionPool.shift();
        this.sessionPool.push(session);
        return session;
    }

    async browseNode(session, nodeId, retryCount = 0) {
        const nodeIdStr = nodeId.toString();

        try {
            // Create browse description
            const browseDescription = {
                nodeId: nodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: BrowseDirection.Forward,
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F,
                requestedMaxReferencesPerNode: 1000
            };

            const browseResult = await session.browse(browseDescription);

            if (!browseResult || !browseResult.statusCode || !browseResult.statusCode.isGood()) {
                const statusCode = browseResult?.statusCode?.toString() || 'Unknown error';
                throw new Error(`Browse failed: ${statusCode}`);
            }

            return browseResult.references || [];
        } catch (error) {
            if (retryCount < this.config.maxRetries) {
                const delay = this.config.retryDelay * Math.pow(2, retryCount);
                logger.warn(`Browse retry ${retryCount + 1} for ${nodeIdStr} after ${delay}ms`);
                await new Promise(resolve => setTimeout(resolve, delay));

                // Check if session is still valid
                if (session.isReconnecting || !session.isChannelValid()) {
                    logger.warn('Session invalid, getting new session...');
                    session = this.getAvailableSession();
                }

                return this.browseNode(session, nodeId, retryCount + 1);
            }
            logger.error(`Browse failed after ${retryCount} retries for ${nodeIdStr}:`, error.message);
            return [];
        }
    }

    async readNodeAttributes(session, nodeId) {
        const cacheKey = `attrs_${nodeId}`;
        const cached = this.cache.get(cacheKey);
        if (cached) return cached;

        try {
            const nodesToRead = [
                { nodeId, attributeId: AttributeIds.BrowseName },
                { nodeId, attributeId: AttributeIds.DisplayName },
                { nodeId, attributeId: AttributeIds.NodeClass }
            ];

            const results = await session.read(nodesToRead);
            const attributes = {
                browseName: results[0].value?.value?.name || '',
                displayName: results[1].value?.value?.text || '',
                nodeClass: results[2].value?.value || NodeClass.Unspecified
            };

            this.cache.set(cacheKey, attributes);
            return attributes;
        } catch (error) {
            logger.error(`Failed to read attributes for ${nodeId}:`, error.message);
            return { browseName: '', displayName: '', nodeClass: NodeClass.Unspecified };
        }
    }

    isResultFolder(path) {
        return /Result_\d{3}$/.test(path);
    }

    extractResultData(resultPath, variables) {
        const match = resultPath.match(/Result_(\d{3})$/);
        if (!match) return null;

        const resultNumber = match[1];
        const resultId = `${resultPath}_${resultNumber}`;

        // Map variable names to database fields
        const fieldMapping = {
            'UV1_280nm': 'uv_1',
            'UV2_260nm': 'uv_2',
            'UV3_Scan': 'uv_3',
            'Cond': 'cond',
            'Conc_B': 'conc_b',
            'pH': 'ph',
            'System_Flow': 'system_flow',
            'System_Pressure': 'system_pressure',
            'Sample_Flow': 'sample_flow',
            'Sample_Pressure': 'sample_pressure',
            'PreC_Pressure': 'prec_pressure',
            'DeltaC_Pressure': 'deltac_pressure',
            'PostC_Pressure': 'postc_pressure',
            'Logbook': 'run_log',
            'Fractions': 'fraction'
        };

        const data = {
            result_id: resultId,
            run_log: null,
            fraction: null,
            uv_1: null,
            uv_2: null,
            uv_3: null,
            cond: null,
            conc_b: null,
            ph: null,
            system_flow: null,
            system_pressure: null,
            sample_flow: null,
            sample_pressure: null,
            prec_pressure: null,
            deltac_pressure: null,
            postc_pressure: null
        };

        for (const [varName, nodeId] of variables) {
            const dbField = fieldMapping[varName];
            if (dbField) {
                data[dbField] = nodeId;
            }
        }

        return data;
    }

    async processFolder(folderInfo) {
        const { nodeId, path: folderPath, depth } = folderInfo;
        const session = this.getAvailableSession();

        try {
            const references = await this.browseNode(session, nodeId);

            if (!references || references.length === 0) {
                logger.debug(`Empty folder: ${folderPath}`);
                return;
            }

            const subFolders = [];
            const variables = [];

            // Process references
            await Promise.all(references.map(async (ref) => {
                try {
                    const childNodeId = ref.nodeId;
                    const attrs = await this.readNodeAttributes(session, childNodeId);
                    const childPath = `${folderPath}/${attrs.browseName}`;

                    if (attrs.nodeClass === NodeClass.Object) {
                        // It's a folder
                        if (depth < this.config.maxDepth) {
                            subFolders.push({
                                nodeId: childNodeId,
                                path: childPath,
                                depth: depth + 1
                            });
                        }
                    } else if (attrs.nodeClass === NodeClass.Variable) {
                        // It's a variable
                        variables.push([attrs.browseName, childNodeId.toString()]);
                        this.state.discoveredVariables++;
                    }
                } catch (error) {
                    logger.error(`Error processing reference in ${folderPath}:`, error.message);
                }
            }));

            // Add subfolders to queue
            this.state.folderQueue.push(...subFolders);
            this.state.totalFolders += subFolders.length;

            // If this is a result folder with variables, collect them
            if (this.isResultFolder(folderPath) && variables.length > 0) {
                this.state.resultGroups.set(folderPath, variables);

                // Process batch if it's getting large
                if (this.state.resultGroups.size >= this.config.batchSize) {
                    await this.processBatch();
                }
            }

        } catch (error) {
            logger.error(`Error processing folder ${folderPath}:`, error);
            this.state.errors++;
        }
    }

    async processBatch() {
        const batchData = [];

        for (const [resultPath, variables] of this.state.resultGroups) {
            const data = this.extractResultData(resultPath, variables);
            if (data) {
                batchData.push(data);
            }
        }

        if (batchData.length > 0) {
            try {
                logger.info(`Processing batch of ${batchData.length} records...`);

                // Process in smaller chunks if batch is large
                const chunkSize = 50;
                for (let i = 0; i < batchData.length; i += chunkSize) {
                    const chunk = batchData.slice(i, i + chunkSize);

                    try {
                        const result = await batchInsertAktaNodeIds(chunk);
                        this.state.insertedRecords += result.success;
                        logger.info(`Batch inserted ${result.success}/${chunk.length} records`);
                    } catch (error) {
                        logger.error(`Batch insert error for chunk ${i/chunkSize + 1}:`, error);
                        // Try individual inserts as fallback
                        for (const record of chunk) {
                            try {
                                await insertAktaNodeIds(record);
                                this.state.insertedRecords++;
                            } catch (insertError) {
                                logger.error(`Failed to insert record ${record.result_id}:`, insertError.message);
                            }
                        }
                    }
                }
            } catch (error) {
                logger.error('Batch processing error:', error);
                this.state.pendingBatches.push(batchData);
            }
        }

        this.state.resultGroups.clear();
    }

    reportProgress() {
        const elapsed = (Date.now() - this.state.startTime) / 1000;
        const rate = this.state.processedFolders / elapsed;
        const remaining = this.state.totalFolders - this.state.processedFolders;
        const eta = rate > 0 ? remaining / rate : 0;

        logger.info(`Progress: ${this.state.processedFolders}/${this.state.totalFolders} folders | ` +
                   `${this.state.discoveredVariables} variables | ` +
                   `${this.state.insertedRecords} records | ` +
                   `Rate: ${rate.toFixed(1)} folders/s | ` +
                   `ETA: ${Math.round(eta)}s`);
    }

    async traverseFromNode(startNodeId, parallelId = 0) {
        logger.info(`[Traversal ${parallelId}] Starting from: ${startNodeId}`);

        // Initialize with starting node
        this.state.folderQueue = [{
            nodeId: startNodeId,
            path: startNodeId.toString(),
            depth: 0
        }];
        this.state.totalFolders = 1;

        // Process folders with concurrency limit
        while (this.state.folderQueue.length > 0) {
            const batch = this.state.folderQueue.splice(0, this.config.maxConcurrentBrowse);

            await Promise.all(
                batch.map(folderInfo =>
                    this.browseLimit(async () => {
                        if (!this.state.processedNodes.has(folderInfo.nodeId.toString())) {
                            this.state.processedNodes.add(folderInfo.nodeId.toString());
                            await this.processFolder(folderInfo);
                            this.state.processedFolders++;
                        }
                    })
                )
            );
        }

        // Process any remaining batches
        await this.processBatch();

        logger.info(`[Traversal ${parallelId}] Completed`);
    }

    async runParallelTraversals(startPaths) {
        const parallelCount = Math.min(startPaths.length, this.config.parallelTraversals);
        logger.info(`Starting ${parallelCount} parallel traversals...`);

        const traversalPromises = [];
        for (let i = 0; i < parallelCount; i++) {
            if (i < startPaths.length) {
                traversalPromises.push(this.traverseFromNode(startPaths[i], i));
            }
        }

        await Promise.all(traversalPromises);
    }

    async cleanup() {
        // Clear timers
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
        }
        if (this.batchTimer) {
            clearInterval(this.batchTimer);
        }

        // Process final batch
        await this.processBatch();

        // Close sessions
        for (const session of this.sessionPool) {
            try {
                await session.close();
            } catch (error) {
                logger.error('Error closing session:', error.message);
            }
        }

        // Disconnect client
        if (this.client) {
            await this.client.disconnect();
        }

        logger.info('Cleanup completed');
    }

    getStatistics() {
        const elapsed = (Date.now() - this.state.startTime) / 1000;
        return {
            processedFolders: this.state.processedFolders,
            discoveredVariables: this.state.discoveredVariables,
            insertedRecords: this.state.insertedRecords,
            errors: this.state.errors,
            skippedBranches: this.state.skippedBranches,
            duration: elapsed.toFixed(2)
        };
    }
}

// Main traversal function
async function runOptimizedTraversal(config) {
    const traversal = new OptimizedTraversal();

    // Override config if provided
    if (config.parallelTraversals) {
        traversal.config.parallelTraversals = config.parallelTraversals;
    }

    try {
        await traversal.initialize(config.endpoint, config.username, config.password);

        // For now, single traversal (can be extended to multiple start points)
        const startNodeId = config.startNodeId || "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods";
        await traversal.traverseFromNode(startNodeId);

        const stats = traversal.getStatistics();
        logger.info(`Traversal completed in ${stats.duration}s. ` +
                   `Processed ${stats.processedFolders} folders, ` +
                   `found ${stats.discoveredVariables} variables, ` +
                   `inserted ${stats.insertedRecords} records`);

        // Trigger Django import
        try {
            await triggerDjangoImport();
        } catch (error) {
            logger.error('Failed to trigger Django import:', error.message);
        }

        return stats;
    } catch (error) {
        logger.error('Traversal failed:', error);
        throw error;
    } finally {
        await traversal.cleanup();
    }
}

module.exports = { runOptimizedTraversal };