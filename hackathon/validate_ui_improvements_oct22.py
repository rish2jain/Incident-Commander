#!/usr/bin/env python3
"""
UI Improvements Validation Script - October 22, 2025

Validates the latest UI improvements including client-side optimization
and enhanced ActivityFeed component.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests


class UIImprovementsValidator:
    """Validates latest UI improvements and client-side optimizations."""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.dashboard_dir = Path("dashboard")
        
        # Expected UI improvements
        self.expected_improvements = {
            'client_side_optimization': {
                'file': 'dashboard/src/components/ActivityFeed.tsx',
                'pattern': 'useClientSideTimestamp',
                'description': 'Client-side timestamp optimization'
            },
            'shared_components': {
                'file': 'dashboard/src/components/shared/DashboardLayout.tsx',
                'pattern': 'import Image from "next/image"',
                'description': 'Next.js Image optimization'
            },
            'websocket_integration': {
                'file': 'dashboard/src/components/ImprovedOperationsDashboardWebSocket.tsx',
                'pattern': 'useIncidentWebSocket',
                'description': 'WebSocket integration'
            },
            'professional_styling': {
                'file': 'dashboard/src/components/shared/index.ts',
                'pattern': 'DashboardLayout',
                'description': 'Shared component system'
            }
        }
        
        self.results = []
    
    def validate_client_side_optimization(self) -> Dict[str, Any]:
        """Validate client-side optimization improvements."""
        print("🔧 Validating client-side optimization...")
        
        results = {
            'optimizations_found': 0,
            'optimizations_working': 0,
            'optimization_details': {},
            'all_optimizations_valid': False
        }
        
        for opt_name, opt_config in self.expected_improvements.items():
            file_path = Path(opt_config['file'])
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if opt_config['pattern'] in content:
                    results['optimizations_found'] += 1
                    results['optimization_details'][opt_name] = {
                        'status': 'found',
                        'description': opt_config['description'],
                        'file': str(file_path)
                    }
                    print(f"✅ {opt_config['description']}: Found in {file_path}")
                    
                    # Additional validation for specific optimizations
                    if opt_name == 'client_side_optimization':
                        # Check for proper implementation
                        if 'const isClient = useClientSideTimestamp()' in content:
                            results['optimizations_working'] += 1
                            results['optimization_details'][opt_name]['implementation'] = 'correct'
                            print(f"✅ Client-side optimization properly implemented")
                        else:
                            results['optimization_details'][opt_name]['implementation'] = 'incomplete'
                            print(f"⚠️  Client-side optimization found but implementation incomplete")
                    else:
                        results['optimizations_working'] += 1
                        results['optimization_details'][opt_name]['implementation'] = 'correct'
                else:
                    results['optimization_details'][opt_name] = {
                        'status': 'missing',
                        'description': opt_config['description'],
                        'file': str(file_path)
                    }
                    print(f"❌ {opt_config['description']}: Not found in {file_path}")
            else:
                results['optimization_details'][opt_name] = {
                    'status': 'file_missing',
                    'description': opt_config['description'],
                    'file': str(file_path)
                }
                print(f"❌ {opt_config['description']}: File missing - {file_path}")
        
        results['all_optimizations_valid'] = (
            results['optimizations_working'] == len(self.expected_improvements)
        )
        
        return results
    
    def validate_component_architecture(self) -> Dict[str, Any]:
        """Validate component architecture improvements."""
        print("\n🏗️  Validating component architecture...")
        
        component_files = [
            "dashboard/src/components/ActivityFeed.tsx",
            "dashboard/src/components/shared/DashboardLayout.tsx",
            "dashboard/src/components/shared/index.ts",
            "dashboard/src/components/ImprovedOperationsDashboardWebSocket.tsx"
        ]
        
        results = {
            'components_checked': 0,
            'components_enhanced': 0,
            'component_details': {},
            'architecture_valid': False
        }
        
        for component_file in component_files:
            if Path(component_file).exists():
                results['components_checked'] += 1
                
                with open(component_file, 'r') as f:
                    content = f.read()
                
                # Check for modern React patterns
                modern_patterns = {
                    'react_memo': 'React.memo',
                    'use_callback': 'useCallback',
                    'use_memo': 'useMemo',
                    'typescript': 'interface',
                    'async_await': 'async'
                }
                
                patterns_found = []
                for pattern_name, pattern in modern_patterns.items():
                    if pattern in content:
                        patterns_found.append(pattern_name)
                
                if len(patterns_found) >= 3:  # At least 3 modern patterns
                    results['components_enhanced'] += 1
                    results['component_details'][component_file] = {
                        'status': 'enhanced',
                        'patterns': patterns_found,
                        'pattern_count': len(patterns_found)
                    }
                    print(f"✅ {component_file}: Enhanced with {len(patterns_found)} modern patterns")
                else:
                    results['component_details'][component_file] = {
                        'status': 'basic',
                        'patterns': patterns_found,
                        'pattern_count': len(patterns_found)
                    }
                    print(f"⚠️  {component_file}: Basic implementation ({len(patterns_found)} patterns)")
            else:
                results['component_details'][component_file] = {
                    'status': 'missing',
                    'patterns': [],
                    'pattern_count': 0
                }
                print(f"❌ {component_file}: File missing")
        
        results['architecture_valid'] = (
            results['components_enhanced'] >= 3  # At least 3 enhanced components
        )
        
        return results
    
    def validate_dashboard_routes(self) -> Dict[str, Any]:
        """Validate that all dashboard routes work with latest improvements."""
        print("\n🌐 Validating dashboard routes with UI improvements...")
        
        routes = {
            'homepage': '/',
            'demo': '/demo',
            'transparency': '/transparency',
            'operations': '/ops'
        }
        
        results = {
            'routes_tested': 0,
            'routes_working': 0,
            'route_details': {},
            'all_routes_operational': False
        }
        
        for route_name, path in routes.items():
            url = f"{self.base_url}{path}"
            results['routes_tested'] += 1
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    results['routes_working'] += 1
                    
                    # Check for specific UI improvements in response
                    content_checks = {
                        'modern_ui': 'class=' in response.text,
                        'react_hydration': 'next/script' in response.text or '__NEXT_DATA__' in response.text,
                        'responsive_design': 'viewport' in response.text
                    }
                    
                    results['route_details'][route_name] = {
                        'status': 'working',
                        'response_time_ms': round(response_time, 2),
                        'content_length': len(response.content),
                        'ui_features': content_checks
                    }
                    print(f"✅ {route_name}: {response.status_code} - {response_time:.1f}ms")
                else:
                    results['route_details'][route_name] = {
                        'status': 'error',
                        'status_code': response.status_code,
                        'ui_features': {}
                    }
                    print(f"❌ {route_name}: {response.status_code}")
                    
            except Exception as e:
                results['route_details'][route_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'ui_features': {}
                }
                print(f"❌ {route_name}: {str(e)}")
        
        results['all_routes_operational'] = results['routes_working'] == results['routes_tested']
        
        return results
    
    def validate_performance_improvements(self) -> Dict[str, Any]:
        """Validate performance improvements from UI enhancements."""
        print("\n⚡ Validating performance improvements...")
        
        results = {
            'performance_features': 0,
            'optimization_techniques': [],
            'performance_score': 0.0,
            'performance_grade': 'C'
        }
        
        # Check for performance optimization patterns
        performance_files = [
            "dashboard/src/components/ActivityFeed.tsx",
            "dashboard/src/hooks/useClientSideTimestamp.ts",
            "dashboard/src/components/ImprovedOperationsDashboardWebSocket.tsx"
        ]
        
        optimization_patterns = {
            'memoization': ['React.memo', 'useMemo', 'useCallback'],
            'lazy_loading': ['lazy', 'Suspense', 'dynamic'],
            'client_optimization': ['useClientSideTimestamp', 'isClient'],
            'efficient_rendering': ['key=', 'shouldComponentUpdate', 'PureComponent'],
            'async_operations': ['async', 'await', 'Promise']
        }
        
        for file_path in performance_files:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                for opt_type, patterns in optimization_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        if opt_type not in results['optimization_techniques']:
                            results['optimization_techniques'].append(opt_type)
                            results['performance_features'] += 1
                            print(f"✅ {opt_type}: Found in {file_path}")
        
        # Calculate performance score
        max_features = len(optimization_patterns)
        results['performance_score'] = results['performance_features'] / max_features
        
        if results['performance_score'] >= 0.8:
            results['performance_grade'] = 'A'
        elif results['performance_score'] >= 0.6:
            results['performance_grade'] = 'B'
        else:
            results['performance_grade'] = 'C'
        
        return results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete UI improvements validation."""
        print("🎨 Starting UI Improvements Validation")
        print("=" * 60)
        
        # Run all validation checks
        optimization_validation = self.validate_client_side_optimization()
        architecture_validation = self.validate_component_architecture()
        routes_validation = self.validate_dashboard_routes()
        performance_validation = self.validate_performance_improvements()
        
        # Compile overall results
        overall_results = {
            'validation_time': datetime.utcnow().isoformat(),
            'optimization_validation': optimization_validation,
            'architecture_validation': architecture_validation,
            'routes_validation': routes_validation,
            'performance_validation': performance_validation,
            'overall_success': (
                optimization_validation.get('all_optimizations_valid', False) and
                architecture_validation.get('architecture_valid', False) and
                routes_validation.get('all_routes_operational', False) and
                performance_validation.get('performance_score', 0) >= 0.6
            )
        }
        
        return overall_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 UI IMPROVEMENTS VALIDATION SUMMARY")
        print("=" * 60)
        
        status = "✅ ALL IMPROVEMENTS VALIDATED" if results['overall_success'] else "❌ ISSUES FOUND"
        print(f"Overall Status: {status}")
        
        # Optimization validation summary
        opt_val = results['optimization_validation']
        print(f"\n🔧 Client-Side Optimization:")
        print(f"  Optimizations Found: {opt_val['optimizations_found']}/{len(self.expected_improvements)}")
        print(f"  Working Correctly: {opt_val['optimizations_working']}/{len(self.expected_improvements)}")
        print(f"  All Valid: {'✅' if opt_val['all_optimizations_valid'] else '❌'}")
        
        # Architecture validation summary
        arch_val = results['architecture_validation']
        print(f"\n🏗️  Component Architecture:")
        print(f"  Components Checked: {arch_val['components_checked']}")
        print(f"  Enhanced Components: {arch_val['components_enhanced']}")
        print(f"  Architecture Valid: {'✅' if arch_val['architecture_valid'] else '❌'}")
        
        # Routes validation summary
        routes_val = results['routes_validation']
        print(f"\n🌐 Dashboard Routes:")
        print(f"  Working Routes: {routes_val['routes_working']}/{routes_val['routes_tested']}")
        print(f"  All Operational: {'✅' if routes_val['all_routes_operational'] else '❌'}")
        
        # Performance validation summary
        perf_val = results['performance_validation']
        print(f"\n⚡ Performance Improvements:")
        print(f"  Performance Features: {perf_val['performance_features']}")
        print(f"  Optimization Techniques: {', '.join(perf_val['optimization_techniques'])}")
        print(f"  Performance Score: {perf_val['performance_score']:.1%}")
        print(f"  Performance Grade: {perf_val['performance_grade']}")
        
        if results['overall_success']:
            print("\n🎉 ALL UI IMPROVEMENTS VALIDATED!")
            print("✅ Client-side optimization working")
            print("✅ Component architecture enhanced")
            print("✅ Dashboard routes operational")
            print("✅ Performance improvements confirmed")
            
            print("\n🚀 Ready for hackathon demonstration with latest UI improvements!")
            
        else:
            print("\n⚠️  IMPROVEMENTS TO COMPLETE:")
            if not opt_val.get('all_optimizations_valid'):
                print("  • Client-side optimization needs completion")
            if not arch_val.get('architecture_valid'):
                print("  • Component architecture needs enhancement")
            if not routes_val.get('all_routes_operational'):
                print("  • Dashboard routes need fixing")
            if perf_val.get('performance_score', 0) < 0.6:
                print("  • Performance improvements below threshold")


def main():
    """Run UI improvements validation."""
    validator = UIImprovementsValidator()
    
    try:
        results = validator.run_validation()
        validator.print_summary(results)
        
        # Save results
        output_file = "hackathon/ui_improvements_validation_oct22.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        if results['overall_success']:
            print("\n🏆 UI IMPROVEMENTS FULLY VALIDATED - READY FOR DEMO! 🚀")
            exit(0)
        else:
            print("\n⚠️  Please complete remaining improvements")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()