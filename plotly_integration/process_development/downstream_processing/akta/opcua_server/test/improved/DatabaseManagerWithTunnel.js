const mysql = require('mysql2/promise');
const winston = require('winston');
const fs = require('fs');
const path = require('path');
const config = require('./opcuaConfig');
const { startTunnel, getTunnelStatus, testTunnel } = require('./SSHTunnelManager');

// Setup logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'db_errors.log', level: 'error' }),
        new winston.transports.File({ filename: 'db_combined.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

class DatabaseManagerWithTunnel {
    constructor() {
        this.pool = null;
        this.poolReady = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 2000;
        this.fallbackMode = false;
        this.fallbackFile = 'akta_results_fallback.json';
        this.fallbackData = [];
        this.tunnelRequired = true; // Set to false if SSH tunnel is not needed
    }

    async initialize() {
        try {
            // First, establish SSH tunnel if required
            if (this.tunnelRequired) {
                logger.info('🔐 Starting SSH tunnel...');
                const tunnelStarted = await startTunnel();
                
                if (!tunnelStarted) {
                    logger.warn('⚠️ SSH tunnel failed to start, trying direct connection...');
                    this.tunnelRequired = false;
                }
                
                // Wait a moment for tunnel to stabilize
                await this.delay(2000);
            }
            
            await this.createPool();
        } catch (error) {
            logger.warn('⚠️ Database connection failed, enabling fallback mode');
            this.enableFallbackMode();
        }
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    enableFallbackMode() {
        this.fallbackMode = true;
        this.poolReady = false;
        
        // Load existing fallback data if file exists
        if (fs.existsSync(this.fallbackFile)) {
            try {
                const data = fs.readFileSync(this.fallbackFile, 'utf8');
                this.fallbackData = JSON.parse(data);
                logger.info(`📄 Loaded ${this.fallbackData.length} records from fallback file`);
            } catch (error) {
                logger.warn('⚠️ Failed to load fallback file, starting fresh');
                this.fallbackData = [];
            }
        }
        
        logger.info('📄 Database fallback mode enabled - data will be saved to JSON file');
    }

    async createPool() {
        try {
            if (this.pool) {
                await this.pool.end();
            }
            
            // Check tunnel status if required
            if (this.tunnelRequired) {
                const tunnelStatus = getTunnelStatus();
                logger.info(`🔗 Tunnel status: ${JSON.stringify(tunnelStatus)}`);
                
                if (!tunnelStatus.connected) {
                    logger.warn('⚠️ SSH tunnel not connected, attempting to start...');
                    const started = await startTunnel();
                    if (!started) {
                        throw new Error('SSH tunnel failed to start');
                    }
                    await this.delay(2000); // Wait for tunnel to stabilize
                }
                
                // Test tunnel connectivity
                const tunnelWorking = await testTunnel();
                if (!tunnelWorking) {
                    throw new Error('SSH tunnel test failed');
                }
                
                logger.info('✅ SSH tunnel is working properly');
            }
            
            this.pool = mysql.createPool(config.database);

            // Test connection with timeout
            const testConnection = await Promise.race([
                this.pool.getConnection(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Connection timeout')), 10000)
                )
            ]);
            
            await testConnection.ping();
            testConnection.release();
            
            logger.info('✅ MySQL pool created and tested successfully');
            this.poolReady = true;
            this.fallbackMode = false;
            this.reconnectAttempts = 0;
            
            // If we have fallback data, try to sync it
            if (this.fallbackData.length > 0) {
                await this.syncFallbackData();
            }
            
        } catch (err) {
            this.poolReady = false;
            this.reconnectAttempts++;
            logger.error(`❌ Failed to create MySQL pool (attempt ${this.reconnectAttempts}):`, err.message);
            
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const delay = this.reconnectDelay * this.reconnectAttempts;
                logger.info(`⏳ Retrying in ${delay}ms...`);
                setTimeout(() => this.createPool(), delay);
            } else {
                throw new Error(`Max reconnection attempts reached: ${err.message}`);
            }
        }
    }

    async syncFallbackData() {
        if (!this.poolReady || this.fallbackData.length === 0) return;
        
        logger.info(`🔄 Syncing ${this.fallbackData.length} fallback records to database`);
        
        try {
            const result = await this.batchInsertAktaNodeIds(this.fallbackData);
            if (result.success > 0) {
                // Clear fallback data after successful sync
                this.fallbackData = [];
                this.saveFallbackData();
                logger.info(`✅ Successfully synced ${result.success} records to database`);
            }
        } catch (error) {
            logger.error('❌ Failed to sync fallback data:', error.message);
        }
    }

    saveFallbackData() {
        try {
            fs.writeFileSync(this.fallbackFile, JSON.stringify(this.fallbackData, null, 2));
        } catch (error) {
            logger.error('❌ Failed to save fallback data:', error.message);
        }
    }

    async executeQuery(query, values = []) {
        if (this.fallbackMode) {
            throw new Error('Database not available - fallback mode active');
        }
        
        if (!this.poolReady) {
            await this.createPool();
        }
        
        const maxRetries = 3;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const [rows, fields] = await this.pool.execute(query, values);
                return { rows, fields };
            } catch (err) {
                logger.warn(`Query attempt ${attempt}/${maxRetries} failed:`, err.message);
                
                if (this.isConnectionError(err)) {
                    this.poolReady = false;
                    if (attempt === maxRetries) {
                        this.enableFallbackMode();
                        throw err;
                    }
                    await this.createPool();
                } else {
                    throw err;
                }
            }
        }
    }

    isConnectionError(error) {
        const connectionErrors = [
            'ECONNREFUSED',
            'PROTOCOL_CONNECTION_LOST',
            'ENOTFOUND',
            'ETIMEDOUT',
            'ECONNRESET',
            'Connection timeout'
        ];
        return connectionErrors.some(errType => 
            error.code === errType || error.message.includes(errType)
        );
    }

    async insertAktaNodeIds(data) {
        if (this.fallbackMode) {
            // Add to fallback data
            const record = {
                ...data,
                timestamp_collected: new Date().toISOString(),
                imported: false
            };
            this.fallbackData.push(record);
            this.saveFallbackData();
            logger.info(`📄 FB: Added result_id ${data.result_id} to fallback file`);
            return true;
        }

        const query = `
            INSERT IGNORE INTO akta_node_ids (
                result_id, run_log, fraction, uv_1, uv_2, uv_3, cond,
                conc_b, ph, system_flow, system_pressure, sample_flow,
                sample_pressure, prec_pressure, deltac_pressure, postc_pressure,
                imported, timestamp_collected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
        `;

        const values = [
            data.result_id,
            data.run_log,
            data.fraction,
            data.uv_1,
            data.uv_2,
            data.uv_3,
            data.cond,
            data.conc_b,
            data.ph,
            data.system_flow,
            data.system_pressure,
            data.sample_flow,
            data.sample_pressure,
            data.prec_pressure,
            data.deltac_pressure,
            data.postc_pressure,
            false
        ];

        try {
            await this.executeQuery(query, values);
            logger.info(`✅ DB: Inserted result_id ${data.result_id}`);
            return true;
        } catch (err) {
            logger.error(`❌ DB insert failed for result_id ${data.result_id}:`, err.message);
            
            // Fallback to file storage
            if (this.isConnectionError(err)) {
                return await this.insertAktaNodeIds(data); // Will use fallback mode
            }
            return false;
        }
    }

    async resultIdExists(resultId) {
        if (this.fallbackMode) {
            return this.fallbackData.some(record => record.result_id === resultId);
        }

        try {
            const query = `SELECT 1 FROM akta_node_ids WHERE result_id = ? LIMIT 1`;
            const { rows } = await this.executeQuery(query, [resultId]);
            return rows.length > 0;
        } catch (err) {
            logger.error(`❌ Failed to check if result_id exists: ${resultId}`, err.message);
            return false;
        }
    }

    async batchInsertAktaNodeIds(dataArray) {
        if (!dataArray || dataArray.length === 0) {
            return { success: 0, failed: 0 };
        }

        if (this.fallbackMode) {
            // Add all to fallback data
            for (const data of dataArray) {
                const record = {
                    ...data,
                    timestamp_collected: new Date().toISOString(),
                    imported: false
                };
                this.fallbackData.push(record);
            }
            this.saveFallbackData();
            logger.info(`📄 FB: Added ${dataArray.length} records to fallback file`);
            return { success: dataArray.length, failed: 0 };
        }

        const query = `
            INSERT IGNORE INTO akta_node_ids (
                result_id, run_log, fraction, uv_1, uv_2, uv_3, cond,
                conc_b, ph, system_flow, system_pressure, sample_flow,
                sample_pressure, prec_pressure, deltac_pressure, postc_pressure,
                imported, timestamp_collected
            ) VALUES ?
        `;

        const values = dataArray.map(data => [
            data.result_id,
            data.run_log,
            data.fraction,
            data.uv_1,
            data.uv_2,
            data.uv_3,
            data.cond,
            data.conc_b,
            data.ph,
            data.system_flow,
            data.system_pressure,
            data.sample_flow,
            data.sample_pressure,
            data.prec_pressure,
            data.deltac_pressure,
            data.postc_pressure,
            false,
            new Date()
        ]);

        try {
            const { rows } = await this.executeQuery(query, [values]);
            logger.info(`✅ Batch inserted ${rows.affectedRows} records`);
            return { success: rows.affectedRows, failed: 0 };
        } catch (err) {
            logger.error(`❌ Batch insert failed:`, err.message);
            
            // Fallback to file storage
            if (this.isConnectionError(err)) {
                return await this.batchInsertAktaNodeIds(dataArray); // Will use fallback mode
            }
            return { success: 0, failed: dataArray.length };
        }
    }

    getStatus() {
        return {
            poolReady: this.poolReady,
            fallbackMode: this.fallbackMode,
            fallbackRecords: this.fallbackData.length,
            reconnectAttempts: this.reconnectAttempts,
            tunnel: getTunnelStatus()
        };
    }

    async close() {
        if (this.pool) {
            await this.pool.end();
            this.poolReady = false;
            logger.info('🔌 Database pool closed');
        }
        
        if (this.fallbackData.length > 0) {
            this.saveFallbackData();
            logger.info(`📄 Saved ${this.fallbackData.length} records to fallback file`);
        }
    }
}

// Create singleton instance
const dbManager = new DatabaseManagerWithTunnel();

// Initialize on module load
dbManager.initialize().catch(err => {
    logger.error('Failed to initialize database manager:', err);
});

module.exports = {
    insertAktaNodeIds: (data) => dbManager.insertAktaNodeIds(data),
    resultIdExists: (resultId) => dbManager.resultIdExists(resultId),
    batchInsertAktaNodeIds: (dataArray) => dbManager.batchInsertAktaNodeIds(dataArray),
    getStatus: () => dbManager.getStatus(),
    close: () => dbManager.close(),
    dbManager
};