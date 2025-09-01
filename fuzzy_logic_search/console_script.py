#!/usr/bin/env python
"""
Command-line interface for fuzzy logic search.

This module provides the fls (fuzzy logic search) command-line tool,
following a similar architecture to jaf but with fuzzy membership degrees.
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from .lazy_fuzzy_streams import fuzzy_stream, FuzzyLazyStream
from .query_parser import parse_fuzzy_query, format_fuzzy_query, validate_query_syntax
from .fuzzy_eval import fuzzy_eval
from . import __version__

logger = logging.getLogger(__name__)


def add_source_arguments(parser):
    """Add common source-related arguments to a parser."""
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories for JSON/JSONL files."
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json*",
        help="File pattern to match when scanning directories (default: *.json*)."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum membership degree threshold (default: 0.0)."
    )


def load_source(source_path: str, recursive: bool = False, pattern: str = "*.json*") -> FuzzyLazyStream:
    """
    Load a data source into a fuzzy lazy stream.
    
    Args:
        source_path: Path to file, directory, or '-' for stdin
        recursive: Whether to scan directories recursively
        pattern: File pattern for directory scanning
        
    Returns:
        FuzzyLazyStream ready for operations
    """
    if source_path == "-":
        # Read from stdin
        data = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    # Treat as plain text
                    data.append({"content": line})
        return fuzzy_stream(data)
    
    path = Path(source_path)
    
    if path.is_file():
        return fuzzy_stream(str(path))
    elif path.is_dir():
        # Collect all matching files
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # Create a combined stream
        all_docs = []
        for file_path in sorted(files):
            if file_path.is_file():
                try:
                    stream = fuzzy_stream(str(file_path))
                    # Collect documents (with default membership 1.0)
                    for doc, _ in stream.evaluate():
                        all_docs.append(doc)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
        
        return fuzzy_stream(all_docs)
    else:
        raise ValueError(f"Invalid source: {source_path}")


def parse_query_arg(query_arg: str) -> List:
    """
    Parse a query argument which can be JSON or Lisp syntax.
    
    Args:
        query_arg: Query string
        
    Returns:
        Parsed AST
    """
    # Try JSON first
    try:
        ast = json.loads(query_arg)
        if isinstance(ast, list):
            return ast
    except json.JSONDecodeError:
        pass
    
    # Try Lisp syntax
    if query_arg.startswith("("):
        return parse_fuzzy_query(query_arg)
    
    # Assume it's a simple field reference
    if query_arg.startswith(":") or query_arg.startswith("@"):
        return ["exists?", query_arg]
    
    raise ValueError(f"Invalid query syntax: {query_arg}")


def output_results(stream: FuzzyLazyStream, output_format: str = "jsonl", 
                  threshold: float = 0.0, show_membership: bool = True):
    """
    Output results from a fuzzy stream.
    
    Args:
        stream: Fuzzy lazy stream to evaluate
        output_format: Output format (jsonl, json, or membership)
        threshold: Minimum membership threshold
        show_membership: Whether to include membership in output
    """
    results = []
    
    for doc, membership in stream.evaluate():
        if membership >= threshold:
            if show_membership:
                # Wrap document with membership info
                result = {
                    "_membership": membership,
                    "_doc": doc
                }
            else:
                result = doc
            
            if output_format == "jsonl":
                print(json.dumps(result))
            else:
                results.append(result)
    
    if output_format == "json":
        print(json.dumps(results, indent=2))
    elif output_format == "membership":
        # Output only membership degrees
        for result in results:
            if show_membership:
                print(f"{result['_membership']:.4f}")


def main():
    """Main entry point for the fls command."""
    parser = argparse.ArgumentParser(
        description="fls: Fuzzy Logic Search - Stream processing with fuzzy membership degrees",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"fls {__version__}"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level."
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Sub-command to execute"
    )
    
    # --- 'filter' subcommand ---
    filter_parser = subparsers.add_parser(
        "filter",
        help="Filter data using a fuzzy query."
    )
    filter_parser.add_argument(
        "source",
        type=str,
        help="Input source (file, directory, or '-' for stdin)."
    )
    filter_parser.add_argument(
        "query",
        type=str,
        help="Fuzzy query (JSON or Lisp syntax)."
    )
    filter_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results (default: output stream descriptor)."
    )
    filter_parser.add_argument(
        "--format",
        type=str,
        default="jsonl",
        choices=["jsonl", "json", "membership"],
        help="Output format (default: jsonl)."
    )
    filter_parser.add_argument(
        "--no-membership",
        action="store_true",
        help="Don't include membership degrees in output."
    )
    add_source_arguments(filter_parser)
    
    # --- 'map' subcommand ---
    map_parser = subparsers.add_parser(
        "map",
        help="Transform values while preserving membership."
    )
    map_parser.add_argument(
        "source",
        type=str,
        help="Input source."
    )
    map_parser.add_argument(
        "expression",
        type=str,
        help="Transformation expression or field path."
    )
    map_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(map_parser)
    
    # --- 'and' subcommand ---
    and_parser = subparsers.add_parser(
        "and",
        help="Fuzzy intersection (minimum membership) of two streams."
    )
    and_parser.add_argument(
        "left",
        type=str,
        help="Left stream source or result."
    )
    and_parser.add_argument(
        "right",
        type=str,
        help="Right stream source or result."
    )
    and_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(and_parser)
    
    # --- 'or' subcommand ---
    or_parser = subparsers.add_parser(
        "or",
        help="Fuzzy union (maximum membership) of two streams."
    )
    or_parser.add_argument(
        "left",
        type=str,
        help="Left stream source or result."
    )
    or_parser.add_argument(
        "right",
        type=str,
        help="Right stream source or result."
    )
    or_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(or_parser)
    
    # --- 'not' subcommand ---
    not_parser = subparsers.add_parser(
        "not",
        help="Fuzzy complement (1 - membership) of a stream."
    )
    not_parser.add_argument(
        "source",
        type=str,
        help="Stream source or result."
    )
    not_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(not_parser)
    
    # --- 'very' subcommand ---
    very_parser = subparsers.add_parser(
        "very",
        help="Apply 'very' modifier (square membership)."
    )
    very_parser.add_argument(
        "source",
        type=str,
        help="Stream source or result."
    )
    very_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(very_parser)
    
    # --- 'somewhat' subcommand ---
    somewhat_parser = subparsers.add_parser(
        "somewhat",
        help="Apply 'somewhat' modifier (square root membership)."
    )
    somewhat_parser.add_argument(
        "source",
        type=str,
        help="Stream source or result."
    )
    somewhat_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(somewhat_parser)
    
    # --- 'top' subcommand ---
    top_parser = subparsers.add_parser(
        "top",
        help="Get top-k items by membership degree."
    )
    top_parser.add_argument(
        "source",
        type=str,
        help="Stream source or result."
    )
    top_parser.add_argument(
        "k",
        type=int,
        help="Number of top items to keep."
    )
    top_parser.add_argument(
        "--eval",
        action="store_true",
        default=True,
        help="Evaluate and output results (default: True)."
    )
    add_source_arguments(top_parser)
    
    # --- 'threshold' subcommand ---
    threshold_parser = subparsers.add_parser(
        "threshold",
        help="Filter by minimum membership degree (alpha-cut)."
    )
    threshold_parser.add_argument(
        "source",
        type=str,
        help="Stream source or result."
    )
    threshold_parser.add_argument(
        "min_membership",
        type=float,
        help="Minimum membership degree."
    )
    threshold_parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate and output results."
    )
    add_source_arguments(threshold_parser)
    
    # --- 'parse' subcommand ---
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse and validate a fuzzy query."
    )
    parse_parser.add_argument(
        "query",
        type=str,
        help="Query to parse (Lisp syntax)."
    )
    parse_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print the result."
    )
    
    # --- 'format' subcommand ---
    format_parser = subparsers.add_parser(
        "format",
        help="Format a JSON AST as Lisp syntax."
    )
    format_parser.add_argument(
        "ast",
        type=str,
        help="JSON AST to format."
    )
    format_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print with indentation."
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Handle commands
        if args.command == "filter":
            stream = load_source(args.source, args.recursive, args.pattern)
            query = parse_query_arg(args.query)
            filtered = stream.fuzzy_filter(query)
            
            if args.threshold > 0:
                filtered = filtered.threshold(args.threshold)
            
            if args.eval:
                output_results(
                    filtered,
                    args.format,
                    args.threshold,
                    not args.no_membership
                )
            else:
                # Output stream descriptor
                print(json.dumps({
                    "type": "fuzzy_filtered_stream",
                    "source": args.source,
                    "query": format_fuzzy_query(query),
                    "threshold": args.threshold
                }))
        
        elif args.command == "map":
            stream = load_source(args.source, args.recursive, args.pattern)
            
            # Parse expression if it looks like a query
            if args.expression.startswith("(") or args.expression.startswith("["):
                expression = parse_query_arg(args.expression)
            else:
                expression = args.expression
            
            mapped = stream.fuzzy_map(expression)
            
            if args.eval:
                output_results(mapped, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_mapped_stream",
                    "source": args.source,
                    "expression": args.expression
                }))
        
        elif args.command == "and":
            left_stream = load_source(args.left, args.recursive, args.pattern)
            right_stream = load_source(args.right, args.recursive, args.pattern)
            result = left_stream.fuzzy_and(right_stream)
            
            if args.eval:
                output_results(result, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_intersection",
                    "left": args.left,
                    "right": args.right
                }))
        
        elif args.command == "or":
            left_stream = load_source(args.left, args.recursive, args.pattern)
            right_stream = load_source(args.right, args.recursive, args.pattern)
            result = left_stream.fuzzy_or(right_stream)
            
            if args.eval:
                output_results(result, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_union",
                    "left": args.left,
                    "right": args.right
                }))
        
        elif args.command == "not":
            stream = load_source(args.source, args.recursive, args.pattern)
            result = stream.not_fuzzy()
            
            if args.eval:
                output_results(result, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_complement",
                    "source": args.source
                }))
        
        elif args.command == "very":
            stream = load_source(args.source, args.recursive, args.pattern)
            result = stream.very()
            
            if args.eval:
                output_results(result, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_very",
                    "source": args.source
                }))
        
        elif args.command == "somewhat":
            stream = load_source(args.source, args.recursive, args.pattern)
            result = stream.somewhat()
            
            if args.eval:
                output_results(result, "jsonl", args.threshold)
            else:
                print(json.dumps({
                    "type": "fuzzy_somewhat",
                    "source": args.source
                }))
        
        elif args.command == "top":
            stream = load_source(args.source, args.recursive, args.pattern)
            result = stream.top_k(args.k)
            output_results(result, "jsonl", 0.0)  # No threshold for top-k
        
        elif args.command == "threshold":
            stream = load_source(args.source, args.recursive, args.pattern)
            result = stream.threshold(args.min_membership)
            
            if args.eval:
                output_results(result, "jsonl", 0.0)  # Already thresholded
            else:
                print(json.dumps({
                    "type": "fuzzy_threshold",
                    "source": args.source,
                    "min_membership": args.min_membership
                }))
        
        elif args.command == "parse":
            query = parse_fuzzy_query(args.query)
            if args.pretty:
                print(json.dumps(query, indent=2))
            else:
                print(json.dumps(query))
        
        elif args.command == "format":
            ast = json.loads(args.ast)
            formatted = format_fuzzy_query(ast, pretty=args.pretty)
            print(formatted)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()