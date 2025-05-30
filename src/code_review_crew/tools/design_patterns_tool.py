"""
Design Patterns Analyzer Tool for CrewAI
Detects design patterns, anti-patterns, and suggests improvements
"""

import ast
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from crewai.tools import BaseTool


@dataclass
class PatternDetection:
    """Represents a detected design pattern or anti-pattern"""
    pattern_type: str  # "pattern" or "anti-pattern"
    name: str
    confidence: float  # 0.0 to 1.0
    description: str
    file_path: str
    line_number: int
    suggestion: str
    code_example: str


class DesignPatternsAnalyzerTool(BaseTool):
    name: str = "Design Patterns Analyzer"
    description: str = """
    Analyzes Python code to detect design patterns and anti-patterns.
    Identifies GoF patterns, architectural patterns, and common anti-patterns.
    Input should be the path to a Python file or directory.
    """
    
    def _run(self, file_path: str) -> str:
        """
        Analyze code for design patterns and anti-patterns
        
        Args:
            file_path: Path to Python file or directory to analyze
            
        Returns:
            Detailed design patterns analysis report
        """
        try:
            detections = []
            
            if os.path.isfile(file_path) and file_path.endswith('.py'):
                detections.extend(self._analyze_file(file_path))
            elif os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.endswith('.py'):
                            full_path = os.path.join(root, file)
                            detections.extend(self._analyze_file(full_path))
            
            return self._generate_report(detections)
            
        except Exception as e:
            return f"Error analyzing design patterns: {str(e)}"
    
    def _analyze_file(self, file_path: str) -> List[PatternDetection]:
        """Analyze a single Python file for design patterns"""
        detections = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Detect various patterns
            detections.extend(self._detect_creational_patterns(tree, file_path))
            detections.extend(self._detect_structural_patterns(tree, file_path))
            detections.extend(self._detect_behavioral_patterns(tree, file_path))
            detections.extend(self._detect_anti_patterns(tree, file_path, content))
                    
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            
        return detections
    
    def _detect_creational_patterns(self, tree: ast.AST, file_path: str) -> List[PatternDetection]:
        """Detect creational design patterns"""
        detections = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Singleton Pattern Detection
                detections.extend(self._detect_singleton(node, file_path))
                
                # Factory Pattern Detection
                detections.extend(self._detect_factory(node, file_path))
                
                # Builder Pattern Detection
                detections.extend(self._detect_builder(node, file_path))
                
        return detections
    
    def _detect_singleton(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Singleton pattern"""
        detections = []
        
        # Look for __new__ method with instance checking
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef) and method.name == "__new__":
                # Check if it has singleton-like behavior
                has_instance_check = False
                for node in ast.walk(method):
                    if isinstance(node, ast.Attribute) and node.attr == "_instance":
                        has_instance_check = True
                        break
                
                if has_instance_check:
                    detections.append(PatternDetection(
                        pattern_type="pattern",
                        name="Singleton",
                        confidence=0.8,
                        description=f"Class '{class_node.name}' implements Singleton pattern",
                        file_path=file_path,
                        line_number=class_node.lineno,
                        suggestion="Consider using dependency injection instead of Singleton for better testability",
                        code_example="# Singleton implementation detected"
                    ))
                    
        return detections
    
    def _detect_factory(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Factory pattern"""
        detections = []
        
        # Look for factory-like method names
        factory_keywords = ['create', 'make', 'build', 'get_instance', 'factory']
        
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                method_name_lower = method.name.lower()
                
                # Check if method name suggests factory pattern
                if any(keyword in method_name_lower for keyword in factory_keywords):
                    # Check if method returns different types based on parameters
                    return_statements = []
                    for node in ast.walk(method):
                        if isinstance(node, ast.Return) and node.value:
                            return_statements.append(node)
                    
                    if len(return_statements) > 1:
                        detections.append(PatternDetection(
                            pattern_type="pattern",
                            name="Factory Method",
                            confidence=0.7,
                            description=f"Method '{method.name}' in class '{class_node.name}' appears to implement Factory pattern",
                            file_path=file_path,
                            line_number=method.lineno,
                            suggestion="Good use of Factory pattern for object creation",
                            code_example=f"def {method.name}(...)  # Factory method"
                        ))
                        
        return detections
    
    def _detect_builder(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Builder pattern"""
        detections = []
        
        # Look for builder characteristics: method chaining, build method
        has_build_method = False
        chainable_methods = 0
        
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                if method.name == "build":
                    has_build_method = True
                
                # Check for method chaining (returns self)
                for node in ast.walk(method):
                    if isinstance(node, ast.Return):
                        if isinstance(node.value, ast.Name) and node.value.id == "self":
                            chainable_methods += 1
                            break
        
        if has_build_method and chainable_methods > 2:
            detections.append(PatternDetection(
                pattern_type="pattern",
                name="Builder",
                confidence=0.9,
                description=f"Class '{class_node.name}' implements Builder pattern",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Well-implemented Builder pattern for complex object construction",
                code_example="# Builder pattern with method chaining"
            ))
            
        return detections
    
    def _detect_structural_patterns(self, tree: ast.AST, file_path: str) -> List[PatternDetection]:
        """Detect structural design patterns"""
        detections = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Decorator Pattern Detection
                detections.extend(self._detect_decorator(node, file_path))
                
                # Adapter Pattern Detection
                detections.extend(self._detect_adapter(node, file_path))
                
                # Facade Pattern Detection
                detections.extend(self._detect_facade(node, file_path))
                
        return detections
    
    def _detect_decorator(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Decorator pattern"""
        detections = []
        
        # Look for classes that wrap other objects and delegate calls
        has_wrapped_object = False
        delegates_calls = False
        
        for node in ast.walk(class_node):
            # Check for wrapped object in __init__
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and hasattr(target.value, 'id'):
                                if "component" in target.attr.lower() or "wrapped" in target.attr.lower():
                                    has_wrapped_object = True
            
            # Check for delegation
            if isinstance(node, ast.Attribute) and hasattr(node.value, 'attr'):
                if "component" in node.value.attr.lower() or "wrapped" in node.value.attr.lower():
                    delegates_calls = True
        
        if has_wrapped_object and delegates_calls:
            detections.append(PatternDetection(
                pattern_type="pattern",
                name="Decorator",
                confidence=0.7,
                description=f"Class '{class_node.name}' appears to implement Decorator pattern",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Good use of Decorator pattern for extending functionality",
                code_example="# Decorator pattern with delegation"
            ))
            
        return detections
    
    def _detect_adapter(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Adapter pattern"""
        detections = []
        
        # Look for adapter-like naming and structure
        if "adapter" in class_node.name.lower():
            detections.append(PatternDetection(
                pattern_type="pattern",
                name="Adapter",
                confidence=0.6,
                description=f"Class '{class_node.name}' suggests Adapter pattern by naming",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Ensure adapter properly translates interface between incompatible classes",
                code_example=f"class {class_node.name}  # Adapter pattern"
            ))
            
        return detections
    
    def _detect_facade(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Facade pattern"""
        detections = []
        
        # Look for facade characteristics: simple interface to complex subsystem
        if "facade" in class_node.name.lower() or "manager" in class_node.name.lower():
            method_count = len([n for n in class_node.body if isinstance(n, ast.FunctionDef)])
            
            if method_count > 3:  # Simple interface with several methods
                detections.append(PatternDetection(
                    pattern_type="pattern",
                    name="Facade",
                    confidence=0.6,
                    description=f"Class '{class_node.name}' appears to implement Facade pattern",
                    file_path=file_path,
                    line_number=class_node.lineno,
                    suggestion="Good use of Facade pattern to simplify complex subsystem",
                    code_example=f"class {class_node.name}  # Facade pattern"
                ))
                
        return detections
    
    def _detect_behavioral_patterns(self, tree: ast.AST, file_path: str) -> List[PatternDetection]:
        """Detect behavioral design patterns"""
        detections = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Strategy Pattern Detection
                detections.extend(self._detect_strategy(node, file_path))
                
                # Observer Pattern Detection
                detections.extend(self._detect_observer(node, file_path))
                
        return detections
    
    def _detect_strategy(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Strategy pattern"""
        detections = []
        
        # Look for strategy-like naming or structure
        if "strategy" in class_node.name.lower():
            detections.append(PatternDetection(
                pattern_type="pattern",
                name="Strategy",
                confidence=0.7,
                description=f"Class '{class_node.name}' suggests Strategy pattern",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Good use of Strategy pattern for algorithm variation",
                code_example=f"class {class_node.name}  # Strategy pattern"
            ))
            
        return detections
    
    def _detect_observer(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Observer pattern"""
        detections = []
        
        # Look for observer-like methods
        observer_methods = ["notify", "update", "subscribe", "unsubscribe", "add_observer"]
        
        class_methods = [n.name for n in class_node.body if isinstance(n, ast.FunctionDef)]
        found_observer_methods = [m for m in class_methods if any(obs in m.lower() for obs in observer_methods)]
        
        if len(found_observer_methods) >= 2:
            detections.append(PatternDetection(
                pattern_type="pattern",
                name="Observer",
                confidence=0.8,
                description=f"Class '{class_node.name}' implements Observer pattern",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Good use of Observer pattern for event handling",
                code_example=f"# Observer methods: {', '.join(found_observer_methods)}"
            ))
            
        return detections
    
    def _detect_anti_patterns(self, tree: ast.AST, file_path: str, content: str) -> List[PatternDetection]:
        """Detect common anti-patterns"""
        detections = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # God Object
                detections.extend(self._detect_god_object(node, file_path))
                
                # Data Class without behavior
                detections.extend(self._detect_anemic_domain_model(node, file_path))
                
        # Spaghetti Code (function-level)
        detections.extend(self._detect_spaghetti_code(tree, file_path))
        
        # Copy-Paste Programming
        detections.extend(self._detect_copy_paste_programming(content, file_path))
        
        return detections
    
    def _detect_god_object(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect God Object anti-pattern"""
        detections = []
        
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        attributes = [n for n in class_node.body if isinstance(n, ast.Assign)]
        
        total_lines = 0
        for method in methods:
            total_lines += getattr(method, 'end_lineno', method.lineno) - method.lineno
        
        # God object heuristics
        if len(methods) > 20 or total_lines > 500:
            detections.append(PatternDetection(
                pattern_type="anti-pattern",
                name="God Object",
                confidence=0.8,
                description=f"Class '{class_node.name}' is too large ({len(methods)} methods, ~{total_lines} lines)",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Split this large class into smaller, more focused classes",
                code_example=f"class {class_node.name}:  # God Object with {len(methods)} methods"
            ))
            
        return detections
    
    def _detect_anemic_domain_model(self, class_node: ast.ClassDef, file_path: str) -> List[PatternDetection]:
        """Detect Anemic Domain Model anti-pattern"""
        detections = []
        
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('__')]
        properties = 0
        
        # Count getter/setter-like methods
        for method in methods:
            if method.name.startswith(('get_', 'set_')) or method.name in ['getter', 'setter']:
                properties += 1
        
        # If most methods are getters/setters, it might be anemic
        if len(methods) > 0 and properties / len(methods) > 0.7:
            detections.append(PatternDetection(
                pattern_type="anti-pattern",
                name="Anemic Domain Model",
                confidence=0.6,
                description=f"Class '{class_node.name}' contains mostly getters/setters with little business logic",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Add business logic methods to make the class more than a data container",
                code_example=f"class {class_node.name}:  # Mostly getters/setters"
            ))
            
        return detections
    
    def _detect_spaghetti_code(self, tree: ast.AST, file_path: str) -> List[PatternDetection]:
        """Detect Spaghetti Code anti-pattern"""
        detections = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count nested levels and complexity
                max_depth = self._calculate_nesting_depth(node)
                
                if max_depth > 6:
                    detections.append(PatternDetection(
                        pattern_type="anti-pattern",
                        name="Spaghetti Code",
                        confidence=0.7,
                        description=f"Function '{node.name}' has excessive nesting depth ({max_depth} levels)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Refactor deeply nested code using early returns or extract methods",
                        code_example=f"def {node.name}():  # Too deeply nested"
                    ))
                    
        return detections
    
    def _detect_copy_paste_programming(self, content: str, file_path: str) -> List[PatternDetection]:
        """Detect Copy-Paste Programming anti-pattern"""
        detections = []
        
        lines = content.split('\n')
        duplicates = {}
        
        # Simple duplicate detection
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#'):  # Ignore short lines and comments
                if stripped in duplicates:
                    duplicates[stripped].append(i + 1)
                else:
                    duplicates[stripped] = [i + 1]
        
        # Find significant duplicates
        for line_content, line_numbers in duplicates.items():
            if len(line_numbers) > 2:  # Appears more than twice
                detections.append(PatternDetection(
                    pattern_type="anti-pattern",
                    name="Copy-Paste Programming",
                    confidence=0.6,
                    description=f"Duplicated code found on lines {line_numbers}",
                    file_path=file_path,
                    line_number=line_numbers[0],
                    suggestion="Extract duplicated code into a reusable function",
                    code_example=f"# Duplicated: {line_content[:50]}..."
                ))
                
        return detections
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a function"""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
                    
            return max_depth
        
        return get_depth(node)
    
    def _generate_report(self, detections: List[PatternDetection]) -> str:
        """Generate a comprehensive design patterns analysis report"""
        patterns = [d for d in detections if d.pattern_type == "pattern"]
        anti_patterns = [d for d in detections if d.pattern_type == "anti-pattern"]
        
        report = f"""
# Design Patterns Analysis Report

## Summary:
- **Design Patterns Found**: {len(patterns)}
- **Anti-Patterns Detected**: {len(anti_patterns)}
- **Total Issues**: {len(detections)}

## Design Patterns Detected:
"""
        
        if patterns:
            for pattern in sorted(patterns, key=lambda x: x.confidence, reverse=True):
                report += f"""
### {pattern.name} Pattern
- **Confidence**: {pattern.confidence:.1%}
- **Location**: {pattern.file_path}:{pattern.line_number}
- **Description**: {pattern.description}
- **Assessment**: {pattern.suggestion}
"""
        else:
            report += "\nNo design patterns detected in the analyzed code.\n"
        
        report += f"\n## Anti-Patterns Found:\n"
        
        if anti_patterns:
            for anti_pattern in sorted(anti_patterns, key=lambda x: x.confidence, reverse=True):
                report += f"""
### {anti_pattern.name} Anti-Pattern
- **Confidence**: {anti_pattern.confidence:.1%}
- **Location**: {anti_pattern.file_path}:{anti_pattern.line_number}
- **Issue**: {anti_pattern.description}
- **Recommendation**: {anti_pattern.suggestion}
"""
        else:
            report += "\nNo anti-patterns detected in the analyzed code.\n"
        
        # Recommendations section
        report += f"\n## Recommendations:\n"
        
        if len(anti_patterns) > len(patterns):
            report += "- Focus on addressing anti-patterns before implementing new patterns\n"
            report += "- Prioritize refactoring God Objects and reducing code duplication\n"
        
        if len(patterns) > 0:
            report += "- Good use of design patterns detected\n"
            report += "- Consider documenting pattern usage for team knowledge\n"
        
        if len(patterns) == 0 and len(anti_patterns) == 0:
            report += "- Consider applying appropriate design patterns for better code organization\n"
            report += "- Look for opportunities to use Strategy, Factory, or Observer patterns\n"
        
        report += f"\n## Pattern Opportunities:\n"
        report += "- **Strategy Pattern**: For algorithm variations or complex if-elif chains\n"
        report += "- **Factory Pattern**: For object creation based on conditions\n"
        report += "- **Observer Pattern**: For event handling and notifications\n"
        report += "- **Decorator Pattern**: For extending functionality without inheritance\n"
        
        return report