#!/usr/bin/env python3
"""
Test script to diagnose Supabase connection issues
"""

import os
import sys

def test_supabase_connection():
    """Test Supabase connection with detailed error reporting"""
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print(f"🔗 DATABASE_URL found: {DATABASE_URL[:50]}...")
    print(f"🔍 Full URL: {DATABASE_URL}")
    
    # Check if psycopg2 is available
    try:
        import psycopg2
        import psycopg2.extras
        print("✅ psycopg2 modules imported successfully")
    except ImportError as e:
        print(f"❌ psycopg2 import failed: {e}")
        return False
    
    # Test basic connection
    print("\n🧪 Testing basic connection...")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Test query
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print(f"✅ Connection successful! Database version: {version[:100]}...")
        
        # Test table access
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users';")
        table_exists = cursor.fetchone()[0]
        print(f"📊 Users table exists: {'Yes' if table_exists > 0 else 'No'}")
        
        if table_exists > 0:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"👥 User count: {user_count}")
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as op_error:
        print(f"❌ Operational Error: {op_error}")
        print("🔍 This usually indicates network, authentication, or server issues")
        
        # Try with different SSL mode
        print("\n🔄 Trying with SSL mode 'prefer'...")
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            print(f"✅ Alternative connection successful! Database version: {version[:100]}...")
            conn.close()
            return True
        except Exception as e2:
            print(f"❌ Alternative connection also failed: {e2}")
            
    except psycopg2.DatabaseError as db_error:
        print(f"❌ Database Error: {db_error}")
        print("🔍 This usually indicates authentication or permission issues")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
    return False

def analyze_connection_string():
    """Analyze the connection string for common issues"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        return
    
    print("\n🔍 Analyzing connection string...")
    
    # Parse URL components
    from urllib.parse import urlparse
    parsed = urlparse(DATABASE_URL)
    
    print(f"  Scheme: {parsed.scheme}")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path[1:] if parsed.path else 'None'}")
    print(f"  Username: {parsed.username}")
    print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
    
    # Check for common issues
    issues = []
    if parsed.scheme != 'postgresql':
        issues.append(f"⚠️  Scheme should be 'postgresql', found: {parsed.scheme}")
    
    if not parsed.hostname:
        issues.append("⚠️  No hostname found")
    elif not parsed.hostname.endswith('.supabase.co'):
        issues.append(f"⚠️  Hostname doesn't look like Supabase: {parsed.hostname}")
    
    if not parsed.port:
        issues.append("⚠️  No port specified (should be 5432 for Supabase)")
    elif parsed.port != 5432:
        issues.append(f"⚠️  Port should be 5432 for Supabase, found: {parsed.port}")
    
    if not parsed.path or parsed.path == '/':
        issues.append("⚠️  No database name specified")
    
    if issues:
        print("🚨 Potential issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ Connection string format looks correct")

if __name__ == "__main__":
    print("🧪 Supabase Connection Diagnostic Tool")
    print("=" * 50)
    
    analyze_connection_string()
    
    print("\n" + "=" * 50)
    success = test_supabase_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Supabase connection is working!")
        print("The issue might be in the application's connection logic.")
    else:
        print("💥 Supabase connection failed!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your Supabase project is active and running")
        print("2. Verify your DATABASE_URL is correct in Render environment variables")
        print("3. Check if your Supabase project has connection limits reached")
        print("4. Ensure your IP is not blocked (though Render should be whitelisted)")
        print("5. Try regenerating your database password in Supabase dashboard")