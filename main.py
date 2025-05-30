#!/usr/bin/env python3
"""
Software Engineering Best Practices Review Crew - Main Entry Point

This script initializes and runs the Software Engineering Review Crew
to analyze code for best practices, design patterns, and quality metrics.

Usage:
    python main.py [code_path] [options]
    
Example:
    python main.py ./src --focus=SOLID,patterns
    python main.py single_file.py --verbose
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

from src.code_review_crew.crew import (
    SoftwareEngineeringReviewCrew,
    analyze_code
)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('crew_analysis.log')
        ]
    )


def validate_code_path(code_path: str) -> str:
    """Validate and normalize the code path"""
    path = Path(code_path)
    
    if not path.exists():
        raise ValueError(f"Path does not exist: {code_path}")
    
    if path.is_file() and not path.suffix == '.py':
        raise ValueError(f"File must be a Python file (.py): {code_path}")
    
    if path.is_dir():
        # Check if directory contains Python files
        py_files = list(path.rglob('*.py'))
        if not py_files:
            raise ValueError(f"Directory contains no Python files: {code_path}")
    
    return str(path.absolute())


def parse_focus_areas(focus_str: Optional[str]) -> List[str]:
    """Parse focus areas from command line argument"""
    if not focus_str:
        return ['SOLID', 'patterns', 'quality', 'architecture']
    
    focus_map = {
        'SOLID': 'SOLID principles',
        'solid': 'SOLID principles', 
        'patterns': 'Design patterns',
        'quality': 'Code quality',
        'architecture': 'Architecture',
        'arch': 'Architecture'
    }
    
    areas = [area.strip() for area in focus_str.split(',')]
    return [focus_map.get(area, area) for area in areas]


def main() -> int:
    """Main entry point for the Software Engineering Review Crew"""
    parser = argparse.ArgumentParser(
        description='Analyze code for software engineering best practices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./src                    # Analyze entire src directory
  %(prog)s file.py                  # Analyze single file
  %(prog)s ./src --focus=SOLID      # Focus only on SOLID principles
  %(prog)s ./src --verbose          # Enable verbose output
        """
    )
    
    parser.add_argument(
        'code_path',
        nargs='?',
        default='./src',
        help='Path to Python file or directory to analyze (default: ./src)'
    )
    
    parser.add_argument(
        '--focus',
        type=str,
        help='Comma-separated focus areas: SOLID,patterns,quality,architecture'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output and detailed logging'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='software_engineering_review_report.md',
        help='Output file for the analysis report'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration file'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        required_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.error("Please set them in your .env file or environment")
            return 1
        
        # Validate code path
        try:
            code_path = validate_code_path(args.code_path)
            logger.info(f"Analyzing code at: {code_path}")
        except ValueError as e:
            logger.error(f"Invalid code path: {e}")
            return 1
        
        # Parse focus areas
        focus_areas = parse_focus_areas(args.focus)
        logger.info(f"Focus areas: {', '.join(focus_areas)}")
        
        # Create crew configuration
        crew_config = {
            'scope': 'full',
            'focus_areas': focus_areas,
            'output_file': args.output,
            'verbose': args.verbose
        }
        
        if args.config:
            crew_config['config_file'] = args.config
        
        logger.info("Starting Software Engineering Review Crew analysis...")
        
        # Run the analysis
        try:
            result = analyze_code(code_path, **crew_config)
            
            if result['success']:
                logger.info("Analysis completed successfully!")
                logger.info(f"Report saved to: {result['report_path']}")
                
                # Print summary
                print("\n" + "="*80)
                print("SOFTWARE ENGINEERING REVIEW COMPLETED")
                print("="*80)
                print(f"Analyzed: {result['analysis_path']}")
                print(f"Report: {result['report_path']}")
                print(f"Focus Areas: {', '.join(focus_areas)}")
                print("="*80)
                
                return 0
            else:
                logger.error("Analysis failed")
                return 1
                
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            if args.verbose:
                logger.exception("Full traceback:")
            return 1
    
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        return 1


def run_crew() -> None:
    """
    Alternative entry point for direct crew execution (used by crewai run)
    """
    # Load environment variables
    load_dotenv()
    
    # Get code path from environment or use default
    code_path = os.getenv('CODE_ANALYSIS_PATH', './src')
    
    # Create and run the crew
    try:
        crew_instance = SoftwareEngineeringReviewCrew()
        
        inputs = {
            'code_path': code_path,
            'analysis_scope': 'full',
            'focus_areas': [
                'SOLID principles',
                'Design patterns',
                'Code quality', 
                'Architecture'
            ]
        }
        
        result = crew_instance.crew().kickoff(inputs=inputs)
        print(f"Analysis completed. Report: software_engineering_review_report.md")
        
    except Exception as e:
        print(f"Error running crew: {e}")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())