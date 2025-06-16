const mysql = require('mysql2/promise');

let pool;
let poolReady = false;

async function createPool() {
  try {
    pool = mysql.createPool({
      host: '127.0.0.1',
      port: 3306,
      user: 'cdallarosa',
      password: '$ystImmun3!2022',
      database: 'djangoP1_db',
      waitForConnections: true,
      connectionLimit: 10
    });

    await pool.query('SELECT 1');
    console.log('✅ MySQL pool created and tested successfully');
    poolReady = true;
  } catch (err) {
    poolReady = false;
    console.error('❌ Failed to create MySQL pool:', err.message);
  }
}

// Retry-safe execution wrapper
async function executeQuery(query, values = []) {
  if (!poolReady) await createPool();
  try {
    return await pool.execute(query, values);
  } catch (err) {
    if (err.code === 'ECONNREFUSED') {
      console.warn('⚠️ Connection refused, retrying MySQL pool...');
      poolReady = false;
      await createPool();
      return await pool.execute(query, values);  // Retry once
    } else {
      throw err;
    }
  }
}

async function insertAktaNodeIds(data) {
  const query = `
    INSERT IGNORE akta_node_ids (
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
    await executeQuery(query, values);
    console.log(`✅ DB: Inserted result_id ${data.result_id}`);
  } catch (err) {
    console.error(`❌ DB insert failed for result_id ${data.result_id}:`, err.message);
  }
}

async function resultIdExists(resultId) {
  const query = `SELECT 1 FROM akta_node_ids WHERE result_id = ? LIMIT 1`;
  const [rows] = await executeQuery(query, [resultId]);
  return rows.length > 0;
}

// Initial pool creation
createPool();

module.exports = {
  insertAktaNodeIds,
  resultIdExists
};
