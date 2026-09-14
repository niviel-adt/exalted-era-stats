import os
from typing import Optional

import aiosqlite
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.sqlite_path = os.getenv("SQLITE_PATH", "exalted_stats.db")
        self.pool = None

        self.backend_name = (
            "PostgreSQL"
            if self.database_url.startswith(("postgres://", "postgresql://"))
            else f"SQLite ({self.sqlite_path})"
        )

    @property
    def is_postgres(self):
        return self.database_url.startswith(("postgres://", "postgresql://"))

    async def initialize(self):
        schema = """
        CREATE TABLE IF NOT EXISTS player_snapshots (
            id {id_type},
            guild_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            username TEXT NOT NULL,
            display_name TEXT NOT NULL,

            kills INTEGER,
            acs DOUBLE PRECISION,
            headshot_percentage DOUBLE PRECISION,
            total_matches INTEGER,
            kd_ratio DOUBLE PRECISION,
            first_bloods INTEGER,

            head_count INTEGER,
            head_percentage DOUBLE PRECISION,
            torso_count INTEGER,
            torso_percentage DOUBLE PRECISION,
            leg_count INTEGER,
            leg_percentage DOUBLE PRECISION,

            rating_score DOUBLE PRECISION NOT NULL,
            rating_grade TEXT NOT NULL,

            archive_channel_id BIGINT,
            archive_message_id BIGINT,
            image_url TEXT,

            created_at {time_type} NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """

        if self.is_postgres:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)
            async with self.pool.acquire() as conn:
                await conn.execute(schema.format(id_type="BIGSERIAL PRIMARY KEY", time_type="TIMESTAMPTZ"))
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_snapshots_player_time
                    ON player_snapshots (guild_id, user_id, created_at DESC, id DESC)
                    """
                )
        else:
            sqlite_schema = schema.format(
                id_type="INTEGER PRIMARY KEY AUTOINCREMENT",
                time_type="TEXT",
            ).replace("DOUBLE PRECISION", "REAL")

            async with aiosqlite.connect(self.sqlite_path) as conn:
                await conn.execute(sqlite_schema)
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_snapshots_player_time
                    ON player_snapshots (guild_id, user_id, created_at DESC, id DESC)
                    """
                )
                await conn.commit()

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    @staticmethod
    def flat_stats(stats):
        dist = stats.get("hit_distribution") or {}
        head = dist.get("head") or {}
        torso = dist.get("torso") or {}
        leg = dist.get("leg") or {}

        return {
            "kills": stats.get("kills"),
            "acs": stats.get("acs"),
            "headshot_percentage": stats.get("headshot_percentage"),
            "total_matches": stats.get("total_matches"),
            "kd_ratio": stats.get("kd_ratio"),
            "first_bloods": stats.get("first_bloods"),
            "head_count": head.get("count"),
            "head_percentage": head.get("percentage"),
            "torso_count": torso.get("count"),
            "torso_percentage": torso.get("percentage"),
            "leg_count": leg.get("count"),
            "leg_percentage": leg.get("percentage"),
        }

    async def add_snapshot(
        self,
        *,
        guild_id: int,
        user_id: int,
        username: str,
        display_name: str,
        stats: dict,
        rating_score: float,
        rating_grade: str,
        archive_channel_id: Optional[int],
        archive_message_id: Optional[int],
        image_url: Optional[str],
    ):
        s = self.flat_stats(stats)
        values = (
            guild_id, user_id, username, display_name,
            s["kills"], s["acs"], s["headshot_percentage"], s["total_matches"],
            s["kd_ratio"], s["first_bloods"],
            s["head_count"], s["head_percentage"],
            s["torso_count"], s["torso_percentage"],
            s["leg_count"], s["leg_percentage"],
            rating_score, rating_grade,
            archive_channel_id, archive_message_id, image_url,
        )

        columns = """
            guild_id, user_id, username, display_name,
            kills, acs, headshot_percentage, total_matches,
            kd_ratio, first_bloods,
            head_count, head_percentage,
            torso_count, torso_percentage,
            leg_count, leg_percentage,
            rating_score, rating_grade,
            archive_channel_id, archive_message_id, image_url
        """

        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO player_snapshots ({columns})
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
                    RETURNING id
                    """,
                    *values,
                )
                return int(row["id"])

        async with aiosqlite.connect(self.sqlite_path) as conn:
            cursor = await conn.execute(
                f"""
                INSERT INTO player_snapshots ({columns})
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
            await conn.commit()
            return int(cursor.lastrowid)

    async def get_latest_snapshots(self, guild_id: int, user_id: int, limit: int = 2):
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT *
                    FROM player_snapshots
                    WHERE guild_id=$1 AND user_id=$2
                    ORDER BY created_at DESC, id DESC
                    LIMIT $3
                    """,
                    guild_id, user_id, limit,
                )
                return [dict(row) for row in rows]

        async with aiosqlite.connect(self.sqlite_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT *
                FROM player_snapshots
                WHERE guild_id=? AND user_id=?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (guild_id, user_id, limit),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_latest_snapshot(self, guild_id: int, user_id: int):
        rows = await self.get_latest_snapshots(guild_id, user_id, 1)
        return rows[0] if rows else None

    async def count_snapshots(self, guild_id: int, user_id: int):
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                value = await conn.fetchval(
                    "SELECT COUNT(*) FROM player_snapshots WHERE guild_id=$1 AND user_id=$2",
                    guild_id, user_id,
                )
                return int(value or 0)

        async with aiosqlite.connect(self.sqlite_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM player_snapshots WHERE guild_id=? AND user_id=?",
                (guild_id, user_id),
            )
            row = await cursor.fetchone()
            return int(row[0] if row else 0)

    async def get_leaderboard(self, guild_id: int, limit: int = 10):
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = [
                    dict(row)
                    for row in await conn.fetch(
                        "SELECT * FROM player_snapshots WHERE guild_id=$1 ORDER BY created_at DESC, id DESC",
                        guild_id,
                    )
                ]
        else:
            async with aiosqlite.connect(self.sqlite_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    "SELECT * FROM player_snapshots WHERE guild_id=? ORDER BY created_at DESC, id DESC",
                    (guild_id,),
                )
                rows = [dict(row) for row in await cursor.fetchall()]

        latest = {}
        for row in rows:
            latest.setdefault(row["user_id"], row)

        return sorted(
            latest.values(),
            key=lambda row: row.get("rating_score") or 0,
            reverse=True,
        )[:limit]
