"""
Code Quality Analyzer Tool for CrewAI
Analyzes code quality using Clean Code principles and metrics
"""

import ast
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from crewai.tools import BaseTool


@dataclass
class CodeSmell:
    """Represents a code smell or quality issue"""
    name: str
    severity: str  # Critical, High, Medium, Low
    description: str
    file_path: str
    line_number: int
    suggestion: str
    code_example: str
    metric_value: Optional[float] = None


@dataclass
class QualityMetrics:
    """Code quality metrics"""
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    code_duplication: float = 0.0
    test_coverage: float = 0.0


class CodeQualityAnalyzerTool(BaseTool):
    name: str = "Code Quality Analyzer"
    description: str = """
    Analyzes Python code quality using Clean Code principles and software metrics.
    Detects code smells, calculates complexity metrics, and provides improvement suggestions.
    Input should be the path to a Python file or directory.
    """
    
    def _run(self, file_path: str) -> str:
        """
        Analyze code quality and detect code smells
        
        Args:
            file_path: Path to Python file or directory to analyze
            
        Returns:
            Detailed code quality analysis report
        """
        try:
            code_smells = []
            metrics = QualityMetrics()
            
            if os.path.isfile(file_path) and file_path.endswith('.py'):
                file_smells, file_metrics = self._analyze_file(file_path)
                code_smells.extend(file_smells)
                self._merge_metrics(metrics, file_metrics)
            elif os.path.isdir(file_path):
                total_files = 0
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.endswith('.py'):
                            full_path = os.path.join(root, file)
                            file_smells, file_metrics = self._analyze_file(full_path)
                            code_smells.extend(file_smells)
                            self._merge_metrics(metrics, file_metrics)
                            total_files += 1
                
                # Average metrics across files
                if total_files > 0:
                    metrics.cyclomatic_complexity /= total_files
                    metrics.cognitive_complexity /= total_files
                    metrics.maintainability_index /= total_files
            
            quality_score = self._calculate_quality_score(code_smells, metrics)
            
            return self._generate_report(code_smells, metrics, quality_score)
            
        except Exception as e:
            return f"Error analyzing code quality: {str(e)}"
    
    def _analyze_file(self, file_path: str) -> Tuple[List[CodeSmell], QualityMetrics]:
        """Analyze a single Python file for code quality issues"""
        code_smells = []
        metrics = QualityMetrics()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            metrics.lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Analyze code smells
            code_smells.extend(self._detect_naming_issues(tree, file_path))
            code_smells.extend(self._detect_function_issues(tree, file_path))
            code_smells.extend(self._detect_class_issues(tree, file_path))
            code_smells.extend(self._detect_complexity_issues(tree, file_path))
            code_smells.extend(self._detect_duplication_issues(content, file_path))
            code_smells.extend(self._detect_comment_issues(content, file_path))
            
            # Calculate metrics
            metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
            metrics.cognitive_complexity = self._calculate_cognitive_complexity(tree)
            metrics.maintainability_index = self._calculate_maintainability_index(tree, content)
            metrics.code_duplication = self._calculate_duplication_percentage(content)
                    
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            
        return code_smells, metrics
    
    def _detect_naming_issues(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect naming convention violations"""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Function naming conventions
                if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                    smells.append(CodeSmell(
                        name="Poor Function Naming",
                        severity="Medium",
                        description=f"Function '{node.name}' doesn't follow snake_case convention",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Use snake_case for function names (e.g., calculate_total)",
                        code_example=f"def {node.name}():  # Should be snake_case"
                    ))
                
                # Too short names
                if len(node.name) < 3 and node.name not in ['do', 'go', 'is', 'at', 'to']:
                    smells.append(CodeSmell(
                        name="Unclear Function Name",
                        severity="Low",
                        description=f"Function name '{node.name}' is too short and unclear",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Use descriptive names that clearly indicate the function's purpose",
                        code_example=f"def {node.name}():  # Name too short"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                # Class naming conventions
                if not self._is_pascal_case(node.name):
                    smells.append(CodeSmell(
                        name="Poor Class Naming",
                        severity="Medium",
                        description=f"Class '{node.name}' doesn't follow PascalCase convention",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Use PascalCase for class names (e.g., UserManager)",
                        code_example=f"class {node.name}:  # Should be PascalCase"
                    ))
            
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                # Variable naming (basic check for single letters in inappropriate contexts)
                if len(node.id) == 1 and node.id not in ['i', 'j', 'k', 'x', 'y', 'z']:
                    # Check if it's not in a loop context
                    parent = getattr(node, 'parent', None)
                    if not isinstance(parent, (ast.For, ast.comprehension)):
                        smells.append(CodeSmell(
                            name="Unclear Variable Name",
                            severity="Low",
                            description=f"Single-letter variable name '{node.id}' outside loop context",
                            file_path=file_path,
                            line_number=getattr(node, 'lineno', 0),
                            suggestion="Use descriptive variable names that explain the purpose",
                            code_example=f"{node.id} = ...  # Use descriptive name"
                        ))
        
        return smells
    
    def _detect_function_issues(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect function-level code smells"""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Long Method
                function_length = getattr(node, 'end_lineno', node.lineno) - node.lineno
                if function_length > 20:
                    smells.append(CodeSmell(
                        name="Long Method",
                        severity="High" if function_length > 50 else "Medium",
                        description=f"Function '{node.name}' is too long ({function_length} lines)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Break down into smaller, more focused functions",
                        code_example=f"def {node.name}():  # {function_length} lines",
                        metric_value=function_length
                    ))
                
                # Too Many Parameters
                param_count = len(node.args.args)
                if param_count > 5:
                    smells.append(CodeSmell(
                        name="Long Parameter List",
                        severity="Medium",
                        description=f"Function '{node.name}' has too many parameters ({param_count})",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider using a configuration object or splitting the function",
                        code_example=f"def {node.name}(...):  # {param_count} parameters",
                        metric_value=param_count
                    ))
                
                # Empty Function (except pass)
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    smells.append(CodeSmell(
                        name="Empty Function",
                        severity="Medium",
                        description=f"Function '{node.name}' is empty",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Implement the function or remove if not needed",
                        code_example=f"def {node.name}(): pass  # Empty function"
                    ))
                
                # Deep Nesting
                max_depth = self._calculate_nesting_depth(node)
                if max_depth > 4:
                    smells.append(CodeSmell(
                        name="Deep Nesting",
                        severity="High",
                        description=f"Function '{node.name}' has deep nesting ({max_depth} levels)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Use early returns or extract nested logic into separate functions",
                        code_example=f"def {node.name}():  # {max_depth} nesting levels",
                        metric_value=max_depth
                    ))
        
        return smells
    
    def _detect_class_issues(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect class-level code smells"""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                attributes = [n for n in node.body if isinstance(n, ast.Assign)]
                
                # Large Class
                total_lines = 0
                for method in methods:
                    total_lines += getattr(method, 'end_lineno', method.lineno) - method.lineno
                
                if len(methods) > 15 or total_lines > 200:
                    smells.append(CodeSmell(
                        name="Large Class",
                        severity="High",
                        description=f"Class '{node.name}' is too large ({len(methods)} methods, ~{total_lines} lines)",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Split into smaller, more focused classes",
                        code_example=f"class {node.name}:  # {len(methods)} methods",
                        metric_value=len(methods)
                    ))
                
                # Data Class (many attributes, few methods)
                if len(attributes) > 5 and len(methods) < 3:
                    smells.append(CodeSmell(
                        name="Data Class",
                        severity="Medium",
                        description=f"Class '{node.name}' has many attributes but few methods",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider adding behavior or using dataclasses/namedtuples",
                        code_example=f"class {node.name}:  # Data class pattern"
                    ))
                
                # Lazy Class (too few methods)
                if len(methods) <= 2 and len(attributes) <= 1:
                    smells.append(CodeSmell(
                        name="Lazy Class",
                        severity="Low",
                        description=f"Class '{node.name}' does very little",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Consider merging with another class or removing if unnecessary",
                        code_example=f"class {node.name}:  # Lazy class"
                    ))
        
        return smells
    
    def _detect_complexity_issues(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect complexity-related issues"""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                
                if complexity > 10:
                    smells.append(CodeSmell(
                        name="High Cyclomatic Complexity",
                        severity="High" if complexity > 15 else "Medium",
                        description=f"Function '{node.name}' has high complexity ({complexity})",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Simplify by extracting conditions into separate functions",
                        code_example=f"def {node.name}():  # Complexity: {complexity}",
                        metric_value=complexity
                    ))
        
        return smells
    
    def _detect_duplication_issues(self, content: str, file_path: str) -> List[CodeSmell]:
        """Detect code duplication issues"""
        smells = []
        
        lines = content.split('\n')
        line_counts = {}
        
        # Count duplicate lines
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 15 and not stripped.startswith('#'):  # Ignore short lines and comments
                if stripped in line_counts:
                    line_counts[stripped].append(i + 1)
                else:
                    line_counts[stripped] = [i + 1]
        
        # Find significant duplications
        for line_content, line_numbers in line_counts.items():
            if len(line_numbers) > 2:  # Appears more than twice
                smells.append(CodeSmell(
                    name="Code Duplication",
                    severity="Medium",
                    description=f"Duplicated code on lines {line_numbers}",
                    file_path=file_path,
                    line_number=line_numbers[0],
                    suggestion="Extract duplicated code into a reusable function",
                    code_example=f"# Duplicated: {line_content[:50]}...",
                    metric_value=len(line_numbers)
                ))
        
        return smells
    
    def _detect_comment_issues(self, content: str, file_path: str) -> List[CodeSmell]:
        """Detect comment-related issues"""
        smells = []
        
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        # Too few comments
        if total_lines > 50 and comment_lines / total_lines < 0.1:
            smells.append(CodeSmell(
                name="Insufficient Comments",
                severity="Low",
                description=f"File has very few comments ({comment_lines}/{total_lines} lines)",
                file_path=file_path,
                line_number=1,
                suggestion="Add comments to explain complex logic and public interfaces",
                code_example="# Add explanatory comments"
            ))
        
        # Too many comments (might indicate complex code)
        if total_lines > 0 and comment_lines / total_lines > 0.3:
            smells.append(CodeSmell(
                name="Excessive Comments",
                severity="Low",
                description=f"File has many comments ({comment_lines}/{total_lines} lines)",
                file_path=file_path,
                line_number=1,
                suggestion="Consider simplifying code to reduce need for extensive comments",
                code_example="# Code might be too complex"
            ))
        
        return smells
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention"""
        return re.match(r'^[a-z][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth"""
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
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calculate average cyclomatic complexity"""
        total_complexity = 0
        function_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_complexity += self._calculate_function_complexity(node)
                function_count += 1
        
        return total_complexity / function_count if function_count > 0 else 0
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate cognitive complexity (simplified)"""
        # Simplified cognitive complexity calculation
        return self._calculate_cyclomatic_complexity(tree) * 1.2
    
    def _calculate_maintainability_index(self, tree: ast.AST, content: str) -> float:
        """Calculate maintainability index (simplified)"""
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        complexity = self._calculate_cyclomatic_complexity(tree)
        
        if lines_of_code == 0:
            return 100
        
        # Simplified maintainability index
        mi = max(0, (171 - 5.2 * (complexity or 1) - 0.23 * lines_of_code) * 100 / 171)
        return min(100, mi)
    
    def _calculate_duplication_percentage(self, content: str) -> float:
        """Calculate code duplication percentage"""
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        if not lines:
            return 0
        
        unique_lines = len(set(lines))
        return max(0, (len(lines) - unique_lines) / len(lines) * 100)
    
    def _merge_metrics(self, target: QualityMetrics, source: QualityMetrics) -> None:
        """Merge metrics from source into target"""
        target.cyclomatic_complexity += source.cyclomatic_complexity
        target.cognitive_complexity += source.cognitive_complexity
        target.maintainability_index += source.maintainability_index
        target.lines_of_code += source.lines_of_code
        target.code_duplication = max(target.code_duplication, source.code_duplication)
    
    def _calculate_quality_score(self, code_smells: List[CodeSmell], metrics: QualityMetrics) -> float:
        """Calculate overall quality score"""
        base_score = 100
        
        # Deduct for code smells
        severity_weights = {"Critical": 10, "High": 5, "Medium": 2, "Low": 1}
        for smell in code_smells:
            base_score -= severity_weights.get(smell.severity, 1)
        
        # Adjust for metrics
        if metrics.cyclomatic_complexity > 10:
            base_score -= (metrics.cyclomatic_complexity - 10) * 2
        
        if metrics.maintainability_index < 70:
            base_score -= (70 - metrics.maintainability_index) * 0.3
        
        if metrics.code_duplication > 10:
            base_score -= metrics.code_duplication * 0.5
        
        return max(0, min(100, base_score))
    
    def _generate_report(self, code_smells: List[CodeSmell], metrics: QualityMetrics, quality_score: float) -> str:
        """Generate comprehensive code quality report"""
        critical_smells = [s for s in code_smells if s.severity == "Critical"]
        high_smells = [s for s in code_smells if s.severity == "High"]
        medium_smells = [s for s in code_smells if s.severity == "Medium"]
        low_smells = [s for s in code_smells if s.severity == "Low"]
        
        report = f"""
# Code Quality Analysis Report

## Overall Quality Score: {quality_score:.1f}/100

## Quality Metrics:
- **Lines of Code**: {metrics.lines_of_code}
- **Average Cyclomatic Complexity**: {metrics.cyclomatic_complexity:.1f}
- **Average Cognitive Complexity**: {metrics.cognitive_complexity:.1f}
- **Maintainability Index**: {metrics.maintainability_index:.1f}/100
- **Code Duplication**: {metrics.code_duplication:.1f}%

## Code Smells Summary:
- **Critical Issues**: {len(critical_smells)}
- **High Priority**: {len(high_smells)}
- **Medium Priority**: {len(medium_smells)}
- **Low Priority**: {len(low_smells)}
- **Total Issues**: {len(code_smells)}

"""
        
        # Group smells by type
        smell_types = {}
        for smell in code_smells:
            if smell.name not in smell_types:
                smell_types[smell.name] = []
            smell_types[smell.name].append(smell)
        
        report += "## Detailed Code Smells:\n"
        
        for severity in ["Critical", "High", "Medium", "Low"]:
            severity_smells = [s for s in code_smells if s.severity == severity]
            if severity_smells:
                report += f"\n### {severity} Priority Issues:\n"
                
                for smell in severity_smells:
                    metric_info = f" (Value: {smell.metric_value})" if smell.metric_value else ""
                    report += f"""
**{smell.name}**{metric_info}
- Location: {smell.file_path}:{smell.line_number}
- Issue: {smell.description}
- Suggestion: {smell.suggestion}
- Code: `{smell.code_example}`
"""
        
        # Quality assessment
        report += f"\n## Quality Assessment:\n"
        
        if quality_score >= 90:
            report += "- **Excellent**: Code quality is very high with minimal issues\n"
        elif quality_score >= 80:
            report += "- **Good**: Code quality is good with some minor improvements needed\n"
        elif quality_score >= 70:
            report += "- **Fair**: Code quality is acceptable but needs attention to several issues\n"
        elif quality_score >= 60:
            report += "- **Poor**: Code quality needs significant improvement\n"
        else:
            report += "- **Critical**: Code quality is poor and requires immediate attention\n"
        
        report += f"\n## Improvement Recommendations:\n"
        
        # Prioritized recommendations based on most common issues
        if len(high_smells) > 0:
            report += "1. **Address High Priority Issues First**\n"
            report += "   - Focus on Large Classes and Long Methods\n"
            report += "   - Reduce cyclomatic complexity\n"
            report += "   - Fix deep nesting issues\n\n"
        
        if metrics.code_duplication > 10:
            report += "2. **Reduce Code Duplication**\n"
            report += "   - Extract common code into reusable functions\n"
            report += "   - Use inheritance or composition where appropriate\n\n"
        
        if metrics.cyclomatic_complexity > 8:
            report += "3. **Simplify Complex Functions**\n"
            report += "   - Break down complex functions into smaller ones\n"
            report += "   - Use early returns to reduce nesting\n"
            report += "   - Consider using design patterns for complex logic\n\n"
        
        if len(medium_smells) > 5:
            report += "4. **Improve Code Organization**\n"
            report += "   - Follow naming conventions consistently\n"
            report += "   - Organize code into logical modules\n"
            report += "   - Add appropriate documentation\n\n"
        
        # Success metrics
        report += f"\n## Success Metrics:\n"
        report += f"- Target Quality Score: 85+\n"
        report += f"- Max Cyclomatic Complexity: 8 per function\n"
        report += f"- Max Function Length: 20 lines\n"
        report += f"- Max Class Methods: 15\n"
        report += f"- Code Duplication: < 5%\n"
        
        return report