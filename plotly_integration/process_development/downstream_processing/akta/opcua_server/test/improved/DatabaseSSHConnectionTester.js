const mysql = require('mysql2/promise');
const config = require('./opcuaConfig');
const { startTunnel, getTunnelStatus, testTunnel, stopTunnel } = require('./SSHTunnelManager');

async function testConnectionWithTunnel() {
    console.log('🔍 Testing database connection with SSH tunnel...');
    console.log('');
    
    try {
        // Step 1: Start SSH tunnel
        console.log('🔐 Starting SSH tunnel...');
        const tunnelStarted = await startTunnel();
        
        if (!tunnelStarted) {
            console.log('❌ SSH tunnel failed to start');
            console.log('Trying direct connection instead...');
            await testDirectConnection();
            return;
        }
        
        // Wait for tunnel to stabilize
        console.log('⏳ Waiting for tunnel to stabilize...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Step 2: Check tunnel status
        const tunnelStatus = getTunnelStatus();
        console.log(`✅ SSH tunnel status: ${JSON.stringify(tunnelStatus, null, 2)}`);
        
        // Step 3: Test tunnel connectivity
        const tunnelWorking = await testTunnel();
        if (!tunnelWorking) {
            console.log('❌ SSH tunnel connectivity test failed');
            return;
        }
        console.log('✅ SSH tunnel connectivity test passed');
        
        // Step 4: Test database connection through tunnel
        console.log('🔌 Testing database connection through tunnel...');
        await testDatabaseConnection();
        
    } catch (error) {
        console.log('❌ Error during tunnel setup:', error.message);
    } finally {
        // Clean up
        console.log('🧹 Cleaning up...');
        await stopTunnel();
    }
}

async function testDatabaseConnection() {
    try {
        const connection = await mysql.createConnection({
            host: config.database.host,
            port: config.database.port,
            user: config.database.user,
            password: config.database.password,
            database: config.database.database,
            connectTimeout: 10000
        });
        
        const [rows] = await connection.execute('SELECT VERSION() as version, NOW() as current_time');
        console.log('✅ Database connection successful!');
        console.log(`MySQL Version: ${rows[0].version}`);
        console.log(`Server Time: ${rows[0].current_time}`);
        
        // Test if akta_node_ids table exists
        try {
            const [tables] = await connection.execute(
                "SELECT COUNT(*) as count FROM akta_node_ids LIMIT 1"
            );
            console.log('✅ akta_node_ids table found and accessible');
            console.log(`Records in table: ${tables[0].count}`);
        } catch (err) {
            console.log('❌ akta_node_ids table not found or not accessible');
            console.log('You may need to create the table or check permissions');
        }
        
        await connection.end();
        
    } catch (error) {
        console.log('❌ Database connection failed:');
        console.log(`Error Code: ${error.code}`);
        console.log(`Error Message: ${error.message}`);
        console.log('');
        console.log('🔧 Possible solutions:');
        console.log('1. Check SSH tunnel configuration');
        console.log('2. Verify MySQL server is running on remote host');
        console.log('3. Check MySQL credentials');
        console.log('4. Verify firewall settings on remote host');
    }
}

async function testDirectConnection() {
    console.log('🔌 Testing direct database connection...');
    try {
        const connection = await mysql.createConnection({
            host: config.database.host,
            port: config.database.port,
            user: config.database.user,
            password: config.database.password,
            database: config.database.database,
            connectTimeout: 5000
        });
        
        const [rows] = await connection.execute('SELECT VERSION() as version');
        console.log('✅ Direct connection successful!');
        console.log(`MySQL Version: ${rows[0].version}`);
        await connection.end();
        
    } catch (error) {
        console.log('❌ Direct connection also failed:', error.message);
        console.log('ℹ️  The application will run in fallback mode (JSON file storage)');
    }
}

// Run the test
testConnectionWithTunnel();