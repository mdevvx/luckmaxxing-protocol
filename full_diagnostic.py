import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_environment():
    """Check environment variables"""
    print("\n" + "=" * 70)
    print("1️⃣ CHECKING ENVIRONMENT VARIABLES")
    print("=" * 70)

    issues = []

    # Discord Token
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if not discord_token:
        print("❌ DISCORD_BOT_TOKEN: Missing")
        issues.append("DISCORD_BOT_TOKEN missing")
    else:
        print(f"✅ DISCORD_BOT_TOKEN: {discord_token[:20]}...")

    # Supabase URL
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        print("❌ SUPABASE_URL: Missing")
        issues.append("SUPABASE_URL missing")
    else:
        print(f"✅ SUPABASE_URL: {supabase_url}")
        if "/rest/v1" in supabase_url:
            print("   ⚠️  WARNING: URL should NOT contain '/rest/v1'")
            issues.append("SUPABASE_URL contains /rest/v1 (should be removed)")

    # Supabase Key
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_key:
        print("❌ SUPABASE_KEY: Missing")
        issues.append("SUPABASE_KEY missing")
    else:
        # Check key length and type
        key_start = supabase_key[:20]
        key_end = supabase_key[-20:]
        print(f"✅ SUPABASE_KEY: {key_start}...{key_end}")
        print(f"   Length: {len(supabase_key)} characters")

        # Try to detect if it's anon or service_role
        if len(supabase_key) < 100:
            print("   ⚠️  WARNING: Key seems too short for service_role key")
            issues.append("SUPABASE_KEY might be wrong (too short)")

        # Service role keys usually start with eyJ and are very long
        if not supabase_key.startswith("eyJ"):
            print("   ⚠️  WARNING: Key doesn't look like a JWT token")
            issues.append("SUPABASE_KEY doesn't look like a valid JWT")

    return issues


def check_packages():
    """Check if required packages are installed"""
    print("\n" + "=" * 70)
    print("2️⃣ CHECKING PYTHON PACKAGES")
    print("=" * 70)

    issues = []
    required = {
        "discord": "discord.py",
        "dotenv": "python-dotenv",
        "supabase": "supabase",
    }

    for package, pip_name in required.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✅ {pip_name}")
        except ImportError:
            print(f"❌ {pip_name} - NOT INSTALLED")
            issues.append(f"{pip_name} not installed")

    return issues


def check_supabase_connection():
    """Check Supabase connection in detail"""
    print("\n" + "=" * 70)
    print("3️⃣ TESTING SUPABASE CONNECTION")
    print("=" * 70)

    issues = []

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Skipping - credentials missing")
        return ["Supabase credentials missing"]

    try:
        print("   Step 1: Importing supabase library...")
        from supabase import create_client, Client

        print("   ✅ Import successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        issues.append(f"Cannot import supabase: {e}")
        return issues

    try:
        print("   Step 2: Creating client...")
        client = create_client(supabase_url, supabase_key)
        print("   ✅ Client created")
    except Exception as e:
        print(f"   ❌ Client creation failed: {e}")
        issues.append(f"Supabase client creation failed: {e}")
        return issues

    try:
        print("   Step 3: Testing database query...")
        response = client.table("enrollments").select("*").limit(1).execute()
        print("   ✅ Query successful")
        print(f"   Response: {len(response.data) if response.data else 0} rows")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        error_str = str(e)

        if "relation" in error_str and "does not exist" in error_str:
            issues.append("Tables don't exist - need to run supabase_schema.sql")
            print("\n   💡 FIX: Run the schema file in Supabase SQL Editor")
        elif "JWT" in error_str or "401" in error_str:
            issues.append("Wrong API key - using anon instead of service_role?")
            print("\n   💡 FIX: Use the service_role key from Supabase Settings → API")
        else:
            issues.append(f"Database query failed: {e}")

    return issues


def check_database_initialization():
    """Check if database initializes properly in the code"""
    print("\n" + "=" * 70)
    print("4️⃣ TESTING DATABASE INITIALIZATION IN CODE")
    print("=" * 70)

    issues = []

    try:
        print("   Step 1: Importing database module...")
        from database import get_database

        print("   ✅ Import successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        issues.append(f"Cannot import database: {e}")
        return issues

    try:
        print("   Step 2: Getting database instance...")
        db = get_database()
        print("   ✅ Got database instance")
        print(f"   Type: {type(db).__name__}")
        print(f"   Client: {type(db.client) if hasattr(db, 'client') else 'N/A'}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        issues.append(f"get_database() failed: {e}")
        return issues

    try:
        print("   Step 3: Initializing database...")
        import asyncio

        asyncio.run(db.initialize())
        print("   ✅ Database initialized")

        # Check if client is actually set
        if db.client is None:
            print("   ❌ Client is None after initialization!")
            issues.append("Database client is None after initialization")
        else:
            print(f"   ✅ Client type: {type(db.client).__name__}")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        issues.append(f"Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return issues

    try:
        print("   Step 4: Testing a database operation...")
        result = asyncio.run(db.get_guild_settings(1234567890))
        print(f"   ✅ Operation successful: {result}")
    except Exception as e:
        print(f"   ❌ Operation failed: {e}")
        issues.append(f"Database operation failed: {e}")

    return issues


def check_file_structure():
    """Check if all required files exist"""
    print("\n" + "=" * 70)
    print("5️⃣ CHECKING FILE STRUCTURE")
    print("=" * 70)

    issues = []
    required_files = {
        "database/__init__.py": "Database package init",
        "database/base.py": "Database base class",
        "database/supabase_db.py": "Supabase implementation",
    }

    for filepath, description in required_files.items():
        if os.path.exists(filepath):
            print(f"✅ {description}: {filepath}")
        else:
            print(f"❌ {description}: {filepath} - MISSING")
            issues.append(f"Missing file: {filepath}")

    return issues


def main():
    print("\n" + "=" * 70)
    print("🔍 LUCKMAXXING BOT - COMPREHENSIVE DIAGNOSTIC")
    print("=" * 70)
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")

    all_issues = []

    # Run all checks
    all_issues.extend(check_environment())
    all_issues.extend(check_packages())
    all_issues.extend(check_file_structure())
    all_issues.extend(check_supabase_connection())
    all_issues.extend(check_database_initialization())

    # Summary
    print("\n" + "=" * 70)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 70)

    if not all_issues:
        print("✅ NO ISSUES FOUND!")
        print("\nYour bot should be working. If you're still getting errors,")
        print("please share the FULL error message and this diagnostic output.")
    else:
        print(f"❌ FOUND {len(all_issues)} ISSUE(S):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")

        print("\n" + "=" * 70)
        print("💡 RECOMMENDED FIXES")
        print("=" * 70)

        # Provide specific fixes
        if any(
            "service_role" in issue.lower()
            or "anon" in issue.lower()
            or "wrong api key" in issue.lower()
            for issue in all_issues
        ):
            print("\n🔑 API KEY ISSUE:")
            print("1. Go to: https://app.supabase.com")
            print("2. Select your project")
            print("3. Settings → API")
            print("4. Find 'service_role' key (NOT 'anon' key)")
            print("5. Copy it and update SUPABASE_KEY in .env")

        if any(
            "schema" in issue.lower() or "does not exist" in issue.lower()
            for issue in all_issues
        ):
            print("\n📊 DATABASE SCHEMA ISSUE:")
            print("1. Go to Supabase dashboard")
            print("2. Click 'SQL Editor'")
            print("3. Copy contents of supabase_schema.sql")
            print("4. Paste and click 'Run'")

        if any("missing" in issue.lower() for issue in all_issues):
            print("\n📦 MISSING DEPENDENCIES:")
            print("Run: pip install -r requirements.txt")

    print("\n" + "=" * 70)
    print("💬 COPY AND SHARE THIS ENTIRE OUTPUT")
    print("=" * 70)
    print("If issues persist, copy this entire diagnostic output")
    print("and share it so we can see exactly what's wrong.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Diagnostic script crashed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
