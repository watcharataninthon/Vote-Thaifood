import { Router } from 'express';
import db from '../db.js';
import redis from '../redis.js';

const router = Router();
const LEADERBOARD_KEY = 'food:votes';
const CACHE_TTL = 10; // seconds

// GET /rankings — Top N or all, sorted by votes
router.get('/rankings', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit) || 20, 20);

  const cached = await redis.get(`rankings:${limit}`);
  if (cached) return res.json(JSON.parse(cached));

  const { rows } = await db.query(
    `SELECT menu_id, vote_count
     FROM menu_votes
     ORDER BY vote_count DESC, menu_id ASC
     LIMIT $1`,
    [limit]
  );

  await redis.setEx(`rankings:${limit}`, CACHE_TTL, JSON.stringify(rows));
  res.json(rows);
});

// POST /vote/:menuId — cast a vote
router.post('/vote/:menuId', async (req, res) => {
  const menuId = parseInt(req.params.menuId);
  const sessionId = req.headers['x-session-id'];

  if (!sessionId) return res.status(400).json({ error: 'x-session-id header required' });
  if (menuId < 1 || menuId > 20) return res.status(400).json({ error: 'invalid menu_id' });

  const client = await db.connect();
  try {
    await client.query('BEGIN');

    // Check for duplicate vote
    const check = await client.query(
      'SELECT 1 FROM user_votes WHERE session_id=$1 AND menu_id=$2',
      [sessionId, menuId]
    );
    if (check.rowCount > 0) {
      await client.query('ROLLBACK');
      return res.status(409).json({ error: 'already_voted' });
    }

    await client.query(
      'INSERT INTO user_votes (session_id, menu_id) VALUES ($1, $2)',
      [sessionId, menuId]
    );
    const { rows } = await client.query(
      `UPDATE menu_votes SET vote_count = vote_count + 1, updated_at = NOW()
       WHERE menu_id = $1 RETURNING vote_count`,
      [menuId]
    );
    await client.query('COMMIT');

    // Sync to Redis sorted set
    await redis.zAdd(LEADERBOARD_KEY, { score: rows[0].vote_count, value: String(menuId) });
    await redis.del(`rankings:${20}`, `rankings:10`, `rankings:5`);

    res.json({ menu_id: menuId, vote_count: rows[0].vote_count });
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
});

// DELETE /vote/:menuId — remove a vote
router.delete('/vote/:menuId', async (req, res) => {
  const menuId = parseInt(req.params.menuId);
  const sessionId = req.headers['x-session-id'];

  if (!sessionId) return res.status(400).json({ error: 'x-session-id header required' });

  const client = await db.connect();
  try {
    await client.query('BEGIN');

    const del = await client.query(
      'DELETE FROM user_votes WHERE session_id=$1 AND menu_id=$2',
      [sessionId, menuId]
    );
    if (del.rowCount === 0) {
      await client.query('ROLLBACK');
      return res.status(404).json({ error: 'not_voted' });
    }

    const { rows } = await client.query(
      `UPDATE menu_votes SET vote_count = GREATEST(vote_count - 1, 0), updated_at = NOW()
       WHERE menu_id = $1 RETURNING vote_count`,
      [menuId]
    );
    await client.query('COMMIT');

    await redis.zAdd(LEADERBOARD_KEY, { score: rows[0].vote_count, value: String(menuId) });
    await redis.del(`rankings:${20}`, `rankings:10`, `rankings:5`);

    res.json({ menu_id: menuId, vote_count: rows[0].vote_count });
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
});

// GET /votes/mine — which menus this session has voted for
router.get('/votes/mine', async (req, res) => {
  const sessionId = req.headers['x-session-id'];
  if (!sessionId) return res.status(400).json({ error: 'x-session-id header required' });

  const { rows } = await db.query(
    'SELECT menu_id FROM user_votes WHERE session_id=$1',
    [sessionId]
  );
  res.json(rows.map(r => r.menu_id));
});

export default router;
