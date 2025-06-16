// Save as fixCertificate.js
const {
    OPCUAClient,
    OPCUAServer,
    MessageSecurityMode,
    SecurityPolicy,
    makeCertificate
} = require("node-opcua");
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

async function regenerateCertificate() {
    console.log('🔐 Regenerating certificate with correct application URI...\n');

    const applicationUri = "urn:OptimizedOPCUABrowser";
    const applicationName = "Optimized OPCUA Browser";

    // Certificate paths
    const pkiDir = path.join(os.homedir(), 'AppData', 'Roaming', 'node-opcua-default-nodejs', 'Config', 'PKI');
    const certDir = path.join(pkiDir, 'own', 'certs');
    const keyDir = path.join(pkiDir, 'own', 'private');

    const certFile = path.join(certDir, 'MyOpcUaClient.pem');
    const keyFile = path.join(keyDir, 'MyOpcUaClient_key.pem');

    try {
        // Backup existing certificate
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        if (await fs.access(certFile).then(() => true).catch(() => false)) {
            await fs.copyFile(certFile, `${certFile}.backup-${timestamp}`);
            console.log(`✅ Backed up existing certificate`);
        }
        if (await fs.access(keyFile).then(() => true).catch(() => false)) {
            await fs.copyFile(keyFile, `${keyFile}.backup-${timestamp}`);
            console.log(`✅ Backed up existing private key`);
        }

        // Create new certificate
        console.log('\n📝 Creating new certificate...');
        const certificate = await makeCertificate({
            applicationUri: applicationUri,
            dns: [os.hostname()],
            ip: ["127.0.0.1"],
            subject: {
                commonName: applicationName,
                organization: "OptimizedOPCUABrowser",
                organizationalUnit: "Development",
                locality: "Local",
                state: "WA",
                country: "US"
            },
            startDate: new Date(),
            validity: 365 * 10, // 10 years
            outputFile: certFile,
            privateKeyFile: keyFile,
            keySize: 2048
        });

        console.log(`\n✅ Certificate regenerated successfully!`);
        console.log(`   Application URI: ${applicationUri}`);
        console.log(`   Certificate: ${certFile}`);
        console.log(`   Private Key: ${keyFile}`);

        // Verify the certificate
        const certContent = await fs.readFile(certFile, 'utf8');
        console.log(`\n🔍 Certificate details:`);
        console.log(`   Size: ${certContent.length} bytes`);
        console.log(`   Valid for: 10 years`);

    } catch (error) {
        console.error('❌ Failed to regenerate certificate:', error);
        throw error;
    }
}

// Run the regeneration
regenerateCertificate()
    .then(() => {
        console.log('\n✅ Certificate regeneration complete!');
        console.log('You can now run the OPC UA server without certificate warnings.');
    })
    .catch(error => {
        console.error('\n❌ Certificate regeneration failed:', error);
        process.exit(1);
    });