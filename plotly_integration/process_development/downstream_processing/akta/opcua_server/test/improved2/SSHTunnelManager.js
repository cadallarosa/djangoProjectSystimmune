
const { Client } = require('ssh2');
const net = require('net');
const winston = require('winston');

// Setup logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'ssh_tunnel.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

class SSHTunnelManager {
    constructor() {
        this.client = null;
        this.server = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.config = {
            ssh: {
                host: '10.0.0.235',
                port: 22,
                username: 'cdallarosa',
                password: 'cdallarosa'  // Consider using SSH keys for security
            },
            tunnel: {
                localPort: 3306,
                remoteHost: '127.0.0.1',
                remotePort: 3306
            }
        };
    }

    async start() {
        if (this.isConnected) {
            logger.info('🔗 SSH tunnel already active');
            return true;
        }

        try {
            await this.createTunnel();
            return true;
        } catch (error) {
            logger.error('❌ Failed to create SSH tunnel:', error);
            return false;
        }
    }

    async createTunnel() {
        return new Promise((resolve, reject) => {
            this.client = new Client();

            this.client.on('ready', () => {
                logger.info('✅ SSH connection established');
                
                // Create the local server that will forward connections
                this.server = net.createServer((localSocket) => {
                    this.client.forwardOut(
                        '127.0.0.1', // source host (local)
                        0,           // source port (let system choose)
                        this.config.tunnel.remoteHost, // destination host on remote server
                        this.config.tunnel.remotePort, // destination port on remote server
                        (err, remoteSocket) => {
                            if (err) {
                                logger.error('❌ SSH forward error:', err);
                                localSocket.end();
                                return;
                            }

                            // Pipe data between local and remote sockets
                            localSocket.pipe(remoteSocket);
                            remoteSocket.pipe(localSocket);

                            localSocket.on('error', (err) => {
                                logger.warn('⚠️ Local socket error:', err.message);
                                remoteSocket.end();
                            });

                            remoteSocket.on('error', (err) => {
                                logger.warn('⚠️ Remote socket error:', err.message);
                                localSocket.end();
                            });
                        }
                    );
                });

                this.server.listen(this.config.tunnel.localPort, '127.0.0.1', () => {
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    logger.info(`🚇 SSH Tunnel active: 127.0.0.1:${this.config.tunnel.localPort} → ${this.config.tunnel.remoteHost}:${this.config.tunnel.remotePort}`);
                    resolve();
                });

                this.server.on('error', (err) => {
                    logger.error('❌ Tunnel server error:', err);
                    reject(err);
                });
            });

            this.client.on('error', (err) => {
                logger.error('❌ SSH client error:', err);
                this.isConnected = false;
                
                // Auto-reconnect logic
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = this.reconnectDelay * this.reconnectAttempts;
                    logger.info(`⏳ Reconnecting SSH tunnel in ${delay}ms (attempt ${this.reconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.createTunnel().catch((reconnectErr) => {
                            logger.error('❌ SSH reconnection failed:', reconnectErr);
                        });
                    }, delay);
                } else {
                    logger.error('❌ Max SSH reconnection attempts reached');
                    reject(err);
                }
            });

            this.client.on('end', () => {
                logger.warn('⚠️ SSH connection ended');
                this.isConnected = false;
            });

            this.client.on('close', () => {
                logger.warn('⚠️ SSH connection closed');
                this.isConnected = false;
            });

            // Connect to SSH server
            logger.info(`🔐 Connecting to SSH server ${this.config.ssh.host}:${this.config.ssh.port}`);
            this.client.connect(this.config.ssh);
        });
    }

    async stop() {
        logger.info('🛑 Stopping SSH tunnel...');
        
        if (this.server) {
            this.server.close();
            this.server = null;
        }

        if (this.client) {
            this.client.end();
            this.client = null;
        }

        this.isConnected = false;
        logger.info('✅ SSH tunnel stopped');
    }

    getStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            config: {
                sshHost: this.config.ssh.host,
                localPort: this.config.tunnel.localPort,
                remotePort: this.config.tunnel.remotePort
            }
        };
    }

    // Test if the tunnel is working
    async testTunnel() {
        if (!this.isConnected) {
            return false;
        }

        return new Promise((resolve) => {
            const socket = net.createConnection(this.config.tunnel.localPort, '127.0.0.1');
            
            socket.on('connect', () => {
                socket.end();
                resolve(true);
            });
            
            socket.on('error', () => {
                resolve(false);
            });
            
            socket.setTimeout(5000, () => {
                socket.destroy();
                resolve(false);
            });
        });
    }
}

// Create singleton instance
const sshTunnel = new SSHTunnelManager();

// Graceful shutdown
process.on('SIGINT', async () => {
    await sshTunnel.stop();
});

process.on('SIGTERM', async () => {
    await sshTunnel.stop();
});

module.exports = {
    sshTunnel,
    startTunnel: () => sshTunnel.start(),
    stopTunnel: () => sshTunnel.stop(),
    getTunnelStatus: () => sshTunnel.getStatus(),
    testTunnel: () => sshTunnel.testTunnel()
};