"""
Vercel build script for Django project
This script runs collectstatic to gather all static files
"""
import os
import subprocess

def main():
    print("Starting Vercel build process...")

    # Run collectstatic
    print("Running collectstatic...")
    result = subprocess.run(
        ['python', 'manage.py', 'collectstatic', '--noinput'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Static files collected successfully")
        print(result.stdout)
    else:
        print("✗ Error collecting static files:")
        print(result.stderr)
        return result.returncode

    print("Build process completed successfully!")
    return 0

if __name__ == '__main__':
    exit(main())
