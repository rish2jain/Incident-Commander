"""
Test patches for external services.
"""

from .external_service_patches import patch_all_external_services, apply_test_patches

__all__ = ['patch_all_external_services', 'apply_test_patches']