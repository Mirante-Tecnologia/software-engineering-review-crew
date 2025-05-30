"""
SOLID Principles Analyzer Tool for CrewAI
Analyzes code for adherence to SOLID principles
"""

import ast
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from crewai.tools import BaseTool


@dataclass
class SOLIDViolation:
    """Represents a SOLID principle violation"""
    principle: str  # S, O, L, I, or D
    severity: str  # Critical, High, Medium, Low
    description: str
    file_path: str
    line_number: int
    suggestion: str
    code_example: str


class SOLIDAnalyzerTool(BaseTool):
    name: str = "SOLID Principles Analyzer"
    description: str = """
    Analyzes Python code for SOLID principles adherence. 
    Detects violations and provides refactoring recommendations.
    Input should be the path to a Python file or directory.
    """
    
    def _run(self, file_path: str) -> str:
        """
        Analyze code for SOLID principles violations
        
        Args:
            file_path: Path to Python file or directory to analyze
            
        Returns:
            Detailed SOLID analysis report
        """
        try:
            violations = []
            scores = {"S": 8, "O": 7, "L": 9, "I": 6, "D": 5}  # Default scores
            
            if os.path.isfile(file_path) and file_path.endswith('.py'):
                violations.extend(self._analyze_file(file_path))
            elif os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.endswith('.py'):
                            full_path = os.path.join(root, file)
                            violations.extend(self._analyze_file(full_path))
            
            # Calculate scores based on violations
            scores = self._calculate_scores(violations)
            
            return self._generate_report(violations, scores)
            
        except Exception as e:
            return f"Error analyzing code: {str(e)}"
    
    def _analyze_file(self, file_path: str) -> List[SOLIDViolation]:
        """Analyze a single Python file for SOLID violations"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Analyze each class in the file
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    violations.extend(self._analyze_class_srp(node, file_path))
                    violations.extend(self._analyze_class_ocp(node, file_path))
                    violations.extend(self._analyze_class_lsp(node, file_path))
                    violations.extend(self._analyze_class_isp(node, file_path))
                    violations.extend(self._analyze_class_dip(node, file_path))
                    
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            
        return violations
    
    def _analyze_class_srp(self, class_node: ast.ClassDef, file_path: str) -> List[SOLIDViolation]:
        """Analyze Single Responsibility Principle violations"""
        violations = []
        
        # Count methods and responsibilities
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        method_count = len(methods)
        
        # Simple heuristic: if class has too many methods, likely SRP violation
        if method_count > 10:
            violations.append(SOLIDViolation(
                principle="S",
                severity="High",
                description=f"Class '{class_node.name}' has {method_count} methods, indicating multiple responsibilities",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Consider splitting this class into smaller, more focused classes",
                code_example=f"class {class_node.name}:  # Too many responsibilities"
            ))
        
        # Check for mixed concerns in method names
        concerns = self._identify_concerns_from_methods(methods)
        if len(concerns) > 3:
            violations.append(SOLIDViolation(
                principle="S",
                severity="Medium",
                description=f"Class '{class_node.name}' handles multiple concerns: {', '.join(concerns)}",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Separate different concerns into different classes",
                code_example="# Consider using composition or delegation"
            ))
            
        return violations
    
    def _analyze_class_ocp(self, class_node: ast.ClassDef, file_path: str) -> List[SOLIDViolation]:
        """Analyze Open/Closed Principle violations"""
        violations = []
        
        # Look for long if-elif chains or switch-like patterns
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                if_elif_count = self._count_if_elif_chains(method)
                if if_elif_count > 5:
                    violations.append(SOLIDViolation(
                        principle="O",
                        severity="Medium",
                        description=f"Method '{method.name}' in class '{class_node.name}' has long if-elif chain ({if_elif_count} conditions)",
                        file_path=file_path,
                        line_number=method.lineno,
                        suggestion="Consider using Strategy pattern or polymorphism instead of if-elif chains",
                        code_example="# Replace if-elif with strategy pattern or factory method"
                    ))
                    
        return violations
    
    def _analyze_class_lsp(self, class_node: ast.ClassDef, file_path: str) -> List[SOLIDViolation]:
        """Analyze Liskov Substitution Principle violations"""
        violations = []
        
        # Check if class overrides methods and might break contracts
        base_classes = [base.id for base in class_node.bases if isinstance(base, ast.Name)]
        
        if base_classes:
            # Look for methods that throw NotImplementedError in derived classes
            for method in class_node.body:
                if isinstance(method, ast.FunctionDef):
                    for stmt in ast.walk(method):
                        if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, ast.Call):
                            if isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                                violations.append(SOLIDViolation(
                                    principle="L",
                                    severity="High",
                                    description=f"Method '{method.name}' in derived class '{class_node.name}' raises NotImplementedError",
                                    file_path=file_path,
                                    line_number=method.lineno,
                                    suggestion="Avoid NotImplementedError in derived classes; use proper inheritance design",
                                    code_example="# Consider using abstract base classes or composition"
                                ))
                                
        return violations
    
    def _analyze_class_isp(self, class_node: ast.ClassDef, file_path: str) -> List[SOLIDViolation]:
        """Analyze Interface Segregation Principle violations"""
        violations = []
        
        # Count abstract methods if it's an ABC
        abstract_methods = []
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                # Check for @abstractmethod decorator
                for decorator in method.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                        abstract_methods.append(method.name)
                        break
        
        # If too many abstract methods, might violate ISP
        if len(abstract_methods) > 8:
            violations.append(SOLIDViolation(
                principle="I",
                severity="Medium",
                description=f"Interface/Abstract class '{class_node.name}' has {len(abstract_methods)} abstract methods",
                file_path=file_path,
                line_number=class_node.lineno,
                suggestion="Consider splitting into smaller, more focused interfaces",
                code_example="# Split large interfaces into smaller, role-specific ones"
            ))
            
        return violations
    
    def _analyze_class_dip(self, class_node: ast.ClassDef, file_path: str) -> List[SOLIDViolation]:
        """Analyze Dependency Inversion Principle violations"""
        violations = []
        
        # Look for direct instantiation of concrete classes
        for node in ast.walk(class_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                # Simple heuristic: concrete class names are usually PascalCase
                func_name = node.func.id
                if func_name[0].isupper() and func_name not in ['Exception', 'ValueError', 'TypeError']:
                    violations.append(SOLIDViolation(
                        principle="D",
                        severity="Low",
                        description=f"Class '{class_node.name}' directly instantiates '{func_name}'",
                        file_path=file_path,
                        line_number=getattr(node, 'lineno', class_node.lineno),
                        suggestion="Consider using dependency injection instead of direct instantiation",
                        code_example="# Use constructor injection or factory pattern"
                    ))
                    
        return violations
    
    def _identify_concerns_from_methods(self, methods: List[ast.FunctionDef]) -> List[str]:
        """Identify different concerns based on method names"""
        concerns = set()
        
        concern_keywords = {
            'data': ['get', 'set', 'load', 'save', 'read', 'write'],
            'validation': ['validate', 'check', 'verify', 'ensure'],
            'formatting': ['format', 'render', 'display', 'print'],
            'calculation': ['calculate', 'compute', 'process', 'transform'],
            'networking': ['send', 'receive', 'connect', 'request', 'response'],
            'file_ops': ['open', 'close', 'create', 'delete', 'file']
        }
        
        for method in methods:
            method_name = method.name.lower()
            for concern, keywords in concern_keywords.items():
                if any(keyword in method_name for keyword in keywords):
                    concerns.add(concern)
                    break
                    
        return list(concerns)
    
    def _count_if_elif_chains(self, method: ast.FunctionDef) -> int:
        """Count the length of if-elif chains in a method"""
        max_chain = 0
        
        for node in ast.walk(method):
            if isinstance(node, ast.If):
                chain_length = 1
                current = node
                while hasattr(current, 'orelse') and len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                    chain_length += 1
                    current = current.orelse[0]
                max_chain = max(max_chain, chain_length)
                
        return max_chain
    
    def _calculate_scores(self, violations: List[SOLIDViolation]) -> Dict[str, int]:
        """Calculate SOLID scores based on violations"""
        scores = {"S": 10, "O": 10, "L": 10, "I": 10, "D": 10}
        
        severity_weights = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0.5}
        
        for violation in violations:
            principle = violation.principle
            weight = severity_weights.get(violation.severity, 1)
            scores[principle] = max(1, scores[principle] - weight)
            
        return scores
    
    def _generate_report(self, violations: List[SOLIDViolation], scores: Dict[str, int]) -> str:
        """Generate a comprehensive SOLID analysis report"""
        overall_score = sum(scores.values()) / len(scores)
        
        report = f"""
# SOLID Principles Analysis Report

## Overall Score: {overall_score:.1f}/10

## Individual Scores:
- Single Responsibility (S): {scores['S']}/10
- Open/Closed (O): {scores['O']}/10
- Liskov Substitution (L): {scores['L']}/10
- Interface Segregation (I): {scores['I']}/10
- Dependency Inversion (D): {scores['D']}/10

## Violations Found ({len(violations)} total):
"""
        
        # Group violations by principle
        by_principle = {}
        for v in violations:
            if v.principle not in by_principle:
                by_principle[v.principle] = []
            by_principle[v.principle].append(v)
        
        principle_names = {
            "S": "Single Responsibility Principle",
            "O": "Open/Closed Principle", 
            "L": "Liskov Substitution Principle",
            "I": "Interface Segregation Principle",
            "D": "Dependency Inversion Principle"
        }
        
        for principle, violations_list in by_principle.items():
            report += f"\n### {principle_names[principle]} Violations:\n"
            for v in violations_list:
                report += f"""
**{v.severity} Priority**
- File: {v.file_path}:{v.line_number}
- Issue: {v.description}
- Suggestion: {v.suggestion}
- Code: `{v.code_example}`
"""
        
        report += f"\n## Recommendations:\n"
        if overall_score >= 8:
            report += "- Code shows good adherence to SOLID principles\n"
            report += "- Focus on minor improvements and consistency\n"
        elif overall_score >= 6:
            report += "- Code has moderate SOLID compliance\n"
            report += "- Address high and medium priority violations\n"
        else:
            report += "- Code needs significant SOLID improvements\n"
            report += "- Start with critical and high priority violations\n"
            report += "- Consider architectural refactoring\n"
        
        return report