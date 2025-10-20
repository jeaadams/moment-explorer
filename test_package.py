#!/usr/bin/env python3
"""
Simple test script to verify the moment-explorer package works.
"""
import sys
import os

# Add src to path for development testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from moment_explorer import MomentMapExplorer, MomentMapUI, create_interactive_explorer
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_explorer_init():
    """Test MomentMapExplorer initialization."""
    print("\nTesting MomentMapExplorer initialization...")
    try:
        from moment_explorer import MomentMapExplorer
        explorer = MomentMapExplorer()
        assert explorer.data is None
        assert explorer.velax is None
        assert explorer.use_prefix_sums is False
        print("✓ MomentMapExplorer initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False

def test_methods_exist():
    """Test that all expected methods exist."""
    print("\nTesting API methods...")
    try:
        from moment_explorer import MomentMapExplorer
        explorer = MomentMapExplorer()

        methods = [
            'load_cube',
            'generate',
            'save',
            'enable_prefix_sums',
            'get_wcs_extent'
        ]

        for method in methods:
            assert hasattr(explorer, method), f"Missing method: {method}"

        print(f"✓ All {len(methods)} API methods present")
        return True
    except Exception as e:
        print(f"✗ Method check failed: {e}")
        return False

def test_with_dummy_data():
    """Test with synthetic data (no FITS files required)."""
    print("\nTesting with dummy data...")
    try:
        import numpy as np
        from moment_explorer import MomentMapExplorer

        explorer = MomentMapExplorer()

        # Manually set dummy data
        explorer.data = np.random.randn(100, 64, 64) * 0.01
        explorer.velax = np.linspace(-5, 5, 100)
        explorer.mask = np.ones_like(explorer.data)
        explorer.rms = 0.01

        # Test prefix sum toggle
        explorer.enable_prefix_sums(True)
        assert explorer.use_prefix_sums is True

        explorer.enable_prefix_sums(False)
        assert explorer.use_prefix_sums is False

        print("✓ Dummy data tests passed")
        return True
    except Exception as e:
        print(f"✗ Dummy data test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Moment Explorer Package Test Suite")
    print("=" * 60)

    tests = [
        test_imports,
        test_explorer_init,
        test_methods_exist,
        test_with_dummy_data
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All tests passed! Package is ready to use.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
