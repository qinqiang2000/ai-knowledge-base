#!/usr/bin/env python3
"""Test database connection for operational-analytics skill.

Usage:
    python test_connection.py

This script verifies that:
1. Environment variables are configured correctly
2. Database connection can be established
3. Basic query execution works
"""

import asyncio
import os
import sys


def check_env_vars():
    """Check if required environment variables are set."""
    required_vars = [
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DATABASE',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=<value>")
        return False

    print("✅ All required environment variables are set")
    return True


async def test_connection():
    """Test database connection and basic query."""
    from db_connector import DBConnector

    connector = DBConnector()

    print(f"\nConnecting to: {connector.host}:{connector.port}/{connector.database}")

    try:
        pool = await connector.get_pool()
        print("✅ Connection pool created successfully")

        # Test basic query
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            print(f"✅ Database version: {version[:50]}...")

            # Test allowed tables
            allowed_tables = os.getenv('POSTGRES_ALLOWED_TABLES', '').split(',')
            for table in allowed_tables:
                table = table.strip()
                if table:
                    try:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        print(f"✅ Table {table}: {count} rows")
                    except Exception as e:
                        print(f"❌ Table {table}: {e}")

        await connector.close()
        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False


def main():
    """Run connection tests."""
    print("=" * 50)
    print("Operational Analytics - Connection Test")
    print("=" * 50)

    # Load .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("ℹ️  python-dotenv not installed, using system environment")

    # Check environment variables
    if not check_env_vars():
        sys.exit(1)

    # Test connection
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
