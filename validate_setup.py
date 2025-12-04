#!/usr/bin/env python3
"""Validate SEO Gap Analysis Agent setup."""
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_dependencies():
    """Check required dependencies."""
    required = [
        ('aiohttp', 'aiohttp'),
        ('yaml', 'pyyaml'),
        ('bs4', 'beautifulsoup4'),
        ('openai', 'openai'),
        ('numpy', 'numpy'),
        ('sklearn', 'scikit-learn'),
        ('tiktoken', 'tiktoken'),
        ('pydantic', 'pydantic')
    ]
    
    missing = []
    for import_name, package_name in required:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - not installed")
            missing.append(package_name)
    
    if missing:
        print(f"\nInstall missing packages: pip install -r requirements.txt")
        return False
    return True


def check_configuration():
    """Check configuration files."""
    config_files = [
        'config/settings.yaml',
        'config/competitors.yaml',
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} - not found")
            all_exist = False
    
    return all_exist


def check_env_file():
    """Check for .env file."""
    if Path('.env').exists():
        print("✅ .env file exists")
        
        # Check if it has API key (without revealing it)
        with open('.env', 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content and 'your_openai_api_key_here' not in content:
                print("✅ OPENAI_API_KEY appears to be set")
                return True
            else:
                print("⚠️  OPENAI_API_KEY not configured in .env")
                return False
    else:
        print("⚠️  .env file not found")
        print("   Copy .env.example to .env and add your API key")
        return False


def check_directories():
    """Check required directories."""
    dirs = [
        'data/raw_html',
        'data/cleaned_text',
        'data/embeddings',
        'data/logs',
        'reports'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}")
    
    return True


def check_modules():
    """Check that Python modules can be imported."""
    try:
        from app.utils.config import load_config
        from app.utils.logger import setup_logger
        from app.sitemap.fetcher import fetch_sitemap
        from app.crawler.extractor import extract_metadata
        from app.embeddings.generator import generate_embedding
        print("✅ All app modules can be imported")
        return True
    except ImportError as e:
        print(f"❌ Module import error: {e}")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("SEO Gap Analysis Agent - Setup Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration Files", check_configuration),
        ("Environment Variables", check_env_file),
        ("Directories", check_directories),
        ("Python Modules", check_modules)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All checks passed! You're ready to run the agent.")
        print("\nNext steps:")
        print("  1. Review config/settings.yaml")
        print("  2. Add competitors to config/competitors.yaml")
        print("  3. Run: python main.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Copy .env.example to .env and add your OpenAI API key")
        print("  - Ensure config files exist in config/ directory")
    print("=" * 60)


if __name__ == "__main__":
    main()
