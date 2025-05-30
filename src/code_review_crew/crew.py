"""
Software Engineering Best Practices Review Crew
A specialized CrewAI implementation for automated code review focusing on 
software engineering principles and best practices.
"""

import os
from typing import Optional, Dict, Any
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, DirectoryReadTool

from .tools import (
    SOLIDAnalyzerTool,
    DesignPatternsAnalyzerTool,
    CodeQualityAnalyzerTool
)


@CrewBase
class SoftwareEngineeringReviewCrew:
    """Software Engineering Best Practices Review Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self) -> None:
        """Initialize the crew with custom tools"""
        # Initialize custom analysis tools
        self.solid_analyzer = SOLIDAnalyzerTool()
        self.patterns_analyzer = DesignPatternsAnalyzerTool()
        self.quality_analyzer = CodeQualityAnalyzerTool()
        
        # Standard file tools
        self.file_read_tool = FileReadTool()
        self.directory_read_tool = DirectoryReadTool()
    
    @agent
    def solid_principles_reviewer(self) -> Agent:
        """
        SOLID Principles Specialist focused on object-oriented design principles
        """
        return Agent(
            config=self.agents_config['solid_principles_reviewer'],
            tools=[
                self.solid_analyzer,
                self.file_read_tool,
                self.directory_read_tool
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=True
        )
    
    @agent 
    def design_patterns_analyzer(self) -> Agent:
        """
        Design Patterns Expert for identifying patterns and anti-patterns
        """
        return Agent(
            config=self.agents_config['design_patterns_analyzer'],
            tools=[
                self.patterns_analyzer,
                self.file_read_tool,
                self.directory_read_tool
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=True
        )
    
    @agent
    def code_quality_auditor(self) -> Agent:
        """
        Code Quality Engineer focused on Clean Code principles and metrics
        """
        return Agent(
            config=self.agents_config['code_quality_auditor'],
            tools=[
                self.quality_analyzer,
                self.file_read_tool,
                self.directory_read_tool
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=True
        )
    
    @agent
    def architecture_reviewer(self) -> Agent:
        """
        Software Architect for system design and architectural analysis
        """
        return Agent(
            config=self.agents_config['architecture_reviewer'],
            tools=[
                self.directory_read_tool,
                self.file_read_tool,
                # Architecture reviewer uses insights from other specialized tools
                self.solid_analyzer,
                self.patterns_analyzer,
                self.quality_analyzer
            ],
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=True
        )
    
    @task
    def solid_principles_analysis(self) -> Task:
        """
        Task for analyzing SOLID principles compliance
        """
        return Task(
            config=self.tasks_config['solid_principles_analysis'],
            agent=self.solid_principles_reviewer(),
            tools=[self.solid_analyzer, self.file_read_tool, self.directory_read_tool]
        )
    
    @task
    def design_patterns_review(self) -> Task:
        """
        Task for analyzing design patterns and anti-patterns
        """
        return Task(
            config=self.tasks_config['design_patterns_review'],
            agent=self.design_patterns_analyzer(),
            tools=[self.patterns_analyzer, self.file_read_tool, self.directory_read_tool]
        )
    
    @task
    def code_quality_assessment(self) -> Task:
        """
        Task for comprehensive code quality analysis
        """
        return Task(
            config=self.tasks_config['code_quality_assessment'],
            agent=self.code_quality_auditor(),
            tools=[self.quality_analyzer, self.file_read_tool, self.directory_read_tool]
        )
    
    @task
    def architectural_analysis(self) -> Task:
        """
        Task for architectural review and system design analysis
        """
        return Task(
            config=self.tasks_config['architectural_analysis'],
            agent=self.architecture_reviewer(),
            tools=[
                self.directory_read_tool, 
                self.file_read_tool,
                self.solid_analyzer,
                self.patterns_analyzer,
                self.quality_analyzer
            ]
        )
    
    @task
    def consolidate_review_findings(self) -> Task:
        """
        Task for consolidating all review findings into comprehensive report
        """
        return Task(
            config=self.tasks_config['consolidate_review_findings'],
            agent=self.architecture_reviewer(),
            context=[
                self.solid_principles_analysis(),
                self.design_patterns_review(),
                self.code_quality_assessment(),
                self.architectural_analysis()
            ],
            output_file='software_engineering_review_report.md'
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Creates the Software Engineering Review Crew
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            # Enable planning for better task coordination
            planning=True,
            # Maximum number of iterations for complex analysis
            max_iter=5,
            # Use embeddings for better context understanding
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            }
        )


def create_crew(code_path: str, **kwargs) -> SoftwareEngineeringReviewCrew:
    """
    Factory function to create a configured crew for code analysis
    
    Args:
        code_path: Path to the code directory or file to analyze
        **kwargs: Additional configuration options
        
    Returns:
        Configured SoftwareEngineeringReviewCrew instance
    """
    if not os.path.exists(code_path):
        raise ValueError(f"Code path does not exist: {code_path}")
    
    crew_instance = SoftwareEngineeringReviewCrew()
    
    # Store the code path for use by agents
    os.environ['CODE_ANALYSIS_PATH'] = os.path.abspath(code_path)
    
    return crew_instance


def analyze_code(code_path: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to analyze code and return results
    
    Args:
        code_path: Path to code to analyze
        **kwargs: Additional options
        
    Returns:
        Analysis results dictionary
    """
    crew_instance = create_crew(code_path, **kwargs)
    
    # Prepare inputs for the crew
    inputs = {
        'code_path': code_path,
        'analysis_scope': kwargs.get('scope', 'full'),
        'focus_areas': kwargs.get('focus_areas', [
            'SOLID principles',
            'Design patterns', 
            'Code quality',
            'Architecture'
        ])
    }
    
    # Execute the crew
    result = crew_instance.crew().kickoff(inputs=inputs)
    
    return {
        'success': True,
        'report_path': 'software_engineering_review_report.md',
        'summary': result,
        'analysis_path': code_path
    }