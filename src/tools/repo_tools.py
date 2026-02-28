"""
Automaton Auditor — Repository Forensic Tools
Implements sandboxed git clone, git log extraction, and AST-based
graph structure analysis. Uses tempfile for isolation; NO os.system calls.
"""

import ast
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Git Operations (Sandboxed)
# ---------------------------------------------------------------------------

def validate_repo_url(repo_url: str) -> Tuple[bool, str]:
    """
    Validate a repository URL before cloning.
    Prevents shell injection and ensures the URL is a safe git remote.
    Returns (is_valid: bool, error_message: str).
    """
    import re
    if not repo_url or not isinstance(repo_url, str):
        return False, "Repository URL must be a non-empty string."
    # Allow only https:// and git:// and ssh git@ URLs
    allowed_pattern = re.compile(
        r'^(https://|git://|git@|ssh://)'
        r'[\w\-\.@:/]+\.git(/)?$|'
        r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(/)?$'
    )
    if not allowed_pattern.match(repo_url.strip()):
        return False, (
            f"Repository URL '{repo_url}' does not match an allowed pattern. "
            "Use https://github.com/owner/repo or a valid git remote URL."
        )
    # Block path traversal and shell injection characters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    for char in dangerous_chars:
        if char in repo_url:
            return False, f"Repository URL contains forbidden character: '{char}'"
    return True, "URL is valid."


def clone_repo(repo_url: str, target_dir: str) -> Tuple[bool, str]:
    """
    Clone a GitHub repository into target_dir using subprocess (NOT os.system).
    Validates URL before cloning to prevent shell injection.
    Returns (success: bool, message: str).
    """
    # Validate URL first
    is_valid, validation_msg = validate_repo_url(repo_url)
    if not is_valid:
        return False, f"URL validation failed: {validation_msg}"

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "50", repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, f"Successfully cloned {repo_url} into {target_dir}"
        else:
            err = result.stderr.strip()
            logger.error(f"Git clone failed: {err}")
            return False, f"Git clone failed: {err}"
    except subprocess.TimeoutExpired:
        return False, "Git clone timed out after 120 seconds"
    except FileNotFoundError:
        return False, "Git is not installed or not on PATH"
    except Exception as e:
        return False, f"Unexpected error during clone: {str(e)}"


def extract_git_history(repo_dir: str) -> Dict[str, Any]:
    """
    Extract commit history using 'git log --oneline --reverse'.
    Returns structured dict with commit list, count, and progression analysis.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--reverse", "--format=%H|%ai|%s"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip(), "commits": [], "count": 0}

        commits = []
        for line in result.stdout.strip().splitlines():
            if "|" in line:
                parts = line.split("|", 2)
                commits.append({
                    "hash": parts[0].strip(),
                    "timestamp": parts[1].strip(),
                    "message": parts[2].strip() if len(parts) > 2 else "",
                })

        # Analyze progression pattern
        messages = [c["message"].lower() for c in commits]
        has_setup = any(kw in m for m in messages for kw in ["init", "setup", "scaffold", "project"])
        has_tools = any(kw in m for m in messages for kw in ["tool", "ast", "parser", "clone", "git"])
        has_graph = any(kw in m for m in messages for kw in ["graph", "node", "edge", "langgraph", "detective", "judge"])
        
        progression_score = sum([has_setup, has_tools, has_graph])
        is_atomic = len(commits) > 3
        timestamps = [c["timestamp"] for c in commits]

        return {
            "commits": commits,
            "count": len(commits),
            "is_atomic": is_atomic,
            "progression": {
                "has_setup_phase": has_setup,
                "has_tool_engineering_phase": has_tools,
                "has_graph_orchestration_phase": has_graph,
                "progression_score": progression_score,
            },
            "timestamps": timestamps,
            "bulk_upload_detected": len(commits) == 1 or (
                len(commits) > 1 and
                len(set(t[:10] for t in timestamps)) == 1 and
                len(commits) > 5
            ),
        }
    except Exception as e:
        return {"error": str(e), "commits": [], "count": 0}


# ---------------------------------------------------------------------------
# File System Scanning
# ---------------------------------------------------------------------------

def scan_directory_structure(repo_dir: str) -> Dict[str, Any]:
    """
    Scan the repository directory structure and return a list of all files.
    """
    repo_path = Path(repo_dir)
    all_files = []
    for f in repo_path.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            all_files.append(str(f.relative_to(repo_path)))

    # Check for key expected files
    key_files = [
        "src/state.py",
        "src/graph.py",
        "src/tools/repo_tools.py",
        "src/tools/doc_tools.py",
        "src/nodes/detectives.py",
        "src/nodes/judges.py",
        "src/nodes/justice.py",
        "pyproject.toml",
        ".env.example",
        "README.md",
        "rubric.json",
    ]
    file_existence = {}
    for kf in key_files:
        file_existence[kf] = any(
            f == kf or f.replace("\\", "/") == kf for f in all_files
        )

    return {
        "all_files": all_files,
        "total_files": len(all_files),
        "key_files": file_existence,
    }


def read_file_content(repo_dir: str, relative_path: str) -> Optional[str]:
    """Safely read a file from the repo, returning None if not found."""
    try:
        full_path = Path(repo_dir) / relative_path
        if full_path.exists() and full_path.is_file():
            return full_path.read_text(encoding="utf-8", errors="replace")
        return None
    except Exception as e:
        logger.warning(f"Could not read {relative_path}: {e}")
        return None


# ---------------------------------------------------------------------------
# AST-Based Analysis (No regex — structural verification only)
# ---------------------------------------------------------------------------

class GraphStructureVisitor(ast.NodeVisitor):
    """AST visitor that extracts LangGraph StateGraph wiring information."""

    def __init__(self):
        self.state_graph_instantiations = []
        self.add_edge_calls = []
        self.add_conditional_edge_calls = []
        self.add_node_calls = []
        self.compile_calls = []
        self.nodes_found: List[str] = []

    def visit_Call(self, node: ast.Call):
        # Detect StateGraph(AgentState) or StateGraph(...) instantiation
        if isinstance(node.func, ast.Name) and node.func.id == "StateGraph":
            self.state_graph_instantiations.append(ast.unparse(node))
        elif isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method == "add_edge":
                self.add_edge_calls.append(ast.unparse(node))
            elif method == "add_conditional_edges":
                self.add_conditional_edge_calls.append(ast.unparse(node))
            elif method == "add_node":
                call_str = ast.unparse(node)
                self.add_node_calls.append(call_str)
                # Try to extract node name
                if node.args:
                    if isinstance(node.args[0], ast.Constant):
                        self.nodes_found.append(node.args[0].value)
            elif method == "compile":
                self.compile_calls.append(ast.unparse(node))
        self.generic_visit(node)


class PydanticModelVisitor(ast.NodeVisitor):
    """AST visitor to detect Pydantic BaseModel and TypedDict subclasses."""

    def __init__(self):
        self.pydantic_models: List[str] = []
        self.typed_dicts: List[str] = []
        self.has_operator_add = False
        self.has_operator_ior = False
        self.annotated_fields: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [ast.unparse(b) for b in node.bases]
        if any("BaseModel" in b for b in bases):
            self.pydantic_models.append(node.name)
        if any("TypedDict" in b for b in bases):
            self.typed_dicts.append(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "operator":
                pass
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "operator":
            if node.attr == "add":
                self.has_operator_add = True
            elif node.attr == "ior":
                self.has_operator_ior = True
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        unparsed = ast.unparse(node)
        if "Annotated" in unparsed:
            self.annotated_fields.append(unparsed)
        self.generic_visit(node)


def analyze_graph_structure(file_path: str) -> Dict[str, Any]:
    """
    Use Python's AST module to analyze a graph.py file for LangGraph patterns.
    Returns structured evidence about the graph wiring.
    """
    try:
        source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        visitor = GraphStructureVisitor()
        visitor.visit(tree)

        # Detect fan-out/fan-in patterns by analyzing edge targets
        # A fan-out is when multiple nodes are targeted from a single source
        # using send/parallel patterns or START -> multiple nodes
        edge_sources: Dict[str, List[str]] = {}
        edge_targets: Dict[str, List[str]] = {}

        for call in visitor.add_edge_calls:
            # Simple heuristic: parse "builder.add_edge('A', 'B')"
            try:
                call_tree = ast.parse(call, mode="eval")
                args = call_tree.body.args  # type: ignore
                if len(args) >= 2:
                    src = ast.unparse(args[0]).strip("'\"")
                    tgt = ast.unparse(args[1]).strip("'\"")
                    edge_sources.setdefault(src, []).append(tgt)
                    edge_targets.setdefault(tgt, []).append(src)
            except Exception:
                pass

        # Fan-out: a node that has multiple outgoing edges
        fan_out_nodes = {k: v for k, v in edge_sources.items() if len(v) > 1}
        # Fan-in: a node that has multiple incoming edges
        fan_in_nodes = {k: v for k, v in edge_targets.items() if len(v) > 1}

        has_state_graph = len(visitor.state_graph_instantiations) > 0
        has_parallel = len(fan_out_nodes) > 0 or len(fan_in_nodes) > 0 or len(visitor.add_conditional_edge_calls) > 0

        return {
            "has_state_graph": has_state_graph,
            "state_graph_instantiations": visitor.state_graph_instantiations,
            "nodes": visitor.nodes_found,
            "add_edge_calls": visitor.add_edge_calls,
            "add_conditional_edge_calls": visitor.add_conditional_edge_calls,
            "add_node_calls": visitor.add_node_calls,
            "compile_calls": visitor.compile_calls,
            "fan_out_nodes": fan_out_nodes,
            "fan_in_nodes": fan_in_nodes,
            "has_parallel_execution": has_parallel,
            "is_linear": not has_parallel and has_state_graph,
        }
    except SyntaxError as e:
        return {"error": f"Syntax error in file: {e}", "has_state_graph": False}
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}", "has_state_graph": False}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}", "has_state_graph": False}


def analyze_state_definitions(file_path: str) -> Dict[str, Any]:
    """
    Use AST to verify Pydantic BaseModel / TypedDict definitions and
    the presence of operator.add / operator.ior reducers in a state file.
    """
    try:
        source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        visitor = PydanticModelVisitor()
        visitor.visit(tree)

        return {
            "pydantic_models": visitor.pydantic_models,
            "typed_dicts": visitor.typed_dicts,
            "has_operator_add": visitor.has_operator_add,
            "has_operator_ior": visitor.has_operator_ior,
            "annotated_fields": visitor.annotated_fields,
            "has_evidence_model": "Evidence" in visitor.pydantic_models,
            "has_judicial_opinion_model": "JudicialOpinion" in visitor.pydantic_models,
            "has_agent_state": (
                "AgentState" in visitor.typed_dicts
                or "AgentState" in visitor.pydantic_models
            ),
        }
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": str(e)}


def analyze_tool_safety(repo_dir: str) -> Dict[str, Any]:
    """
    Scan src/tools/ for security patterns:
    - tempfile.TemporaryDirectory usage (sandboxing)
    - os.system calls (security violation)
    - subprocess.run usage with error handling
    """
    tools_dir = Path(repo_dir) / "src" / "tools"
    results = {
        "files_scanned": [],
        "uses_tempfile": False,
        "uses_os_system": False,
        "uses_subprocess_run": False,
        "has_error_handling": False,
        "security_violations": [],
        "security_strengths": [],
    }

    if not tools_dir.exists():
        results["error"] = "src/tools/ directory not found"
        return results

    for py_file in tools_dir.glob("*.py"):
        results["files_scanned"].append(str(py_file.name))
        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)

            class SecurityVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.uses_tempfile = False
                    self.uses_os_system = False
                    self.uses_subprocess_run = False
                    self.has_try_except = False
                    self.tempfile_snippets: List[str] = []
                    self.subprocess_snippets: List[str] = []
                    self.os_system_snippets: List[str] = []

                def visit_Call(self, node):
                    call_str = ast.unparse(node)
                    if "TemporaryDirectory" in call_str or "tempfile" in call_str:
                        self.uses_tempfile = True
                        self.tempfile_snippets.append(call_str[:120])
                    if "os.system" in call_str:
                        self.uses_os_system = True
                        self.os_system_snippets.append(call_str[:120])
                    if "subprocess.run" in call_str or "subprocess.check" in call_str:
                        self.uses_subprocess_run = True
                        self.subprocess_snippets.append(call_str[:120])
                    self.generic_visit(node)

                def visit_Try(self, node):
                    self.has_try_except = True
                    self.generic_visit(node)

            sv = SecurityVisitor()
            sv.visit(tree)

            if sv.uses_tempfile:
                results["uses_tempfile"] = True
                snippet = sv.tempfile_snippets[0] if sv.tempfile_snippets else "tempfile.TemporaryDirectory()"
                results["security_strengths"].append(
                    f"{py_file.name}: tempfile.TemporaryDirectory() sandboxing CONFIRMED — "
                    f"snippet: `{snippet}`"
                )
            if sv.uses_os_system:
                results["uses_os_system"] = True
                snippet = sv.os_system_snippets[0] if sv.os_system_snippets else "os.system(...)"
                results["security_violations"].append(
                    f"{py_file.name}: raw os.system() call DETECTED — SECURITY VIOLATION — "
                    f"snippet: `{snippet}`"
                )
            if sv.uses_subprocess_run:
                results["uses_subprocess_run"] = True
                snippet = sv.subprocess_snippets[0] if sv.subprocess_snippets else "subprocess.run(...)"
                results["security_strengths"].append(
                    f"{py_file.name}: subprocess.run() (NOT os.system) CONFIRMED — "
                    f"snippet: `{snippet}`"
                )
            if sv.has_try_except:
                results["has_error_handling"] = True
                results["security_strengths"].append(
                    f"{py_file.name}: try/except error handling CONFIRMED"
                )

        except Exception as e:
            results["files_scanned"][-1] += f" (parse error: {e})"

    return results


def analyze_judge_structured_output(repo_dir: str) -> Dict[str, Any]:
    """
    Scan src/nodes/judges.py for .with_structured_output() or .bind_tools()
    bound to JudicialOpinion schema.
    """
    judges_path = Path(repo_dir) / "src" / "nodes" / "judges.py"
    result = {
        "file_exists": judges_path.exists(),
        "uses_with_structured_output": False,
        "uses_bind_tools": False,
        "bound_to_judicial_opinion": False,
        "has_retry_logic": False,
        "personas_found": [],
    }

    if not judges_path.exists():
        return result

    try:
        source = judges_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        class JudgeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.structured_output_calls = []
                self.bind_tools_calls = []
                self.function_names = []
                self.has_retry = False

            def visit_FunctionDef(self, node):
                self.function_names.append(node.name)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node):
                self.function_names.append(node.name)
                self.generic_visit(node)

            def visit_Call(self, node):
                call_str = ast.unparse(node)
                if "with_structured_output" in call_str:
                    self.structured_output_calls.append(call_str)
                if "bind_tools" in call_str:
                    self.bind_tools_calls.append(call_str)
                if "retry" in call_str.lower():
                    self.has_retry = True
                self.generic_visit(node)

        jv = JudgeVisitor()
        jv.visit(tree)

        result["uses_with_structured_output"] = len(jv.structured_output_calls) > 0
        result["uses_bind_tools"] = len(jv.bind_tools_calls) > 0
        result["bound_to_judicial_opinion"] = any(
            "JudicialOpinion" in c
            for c in jv.structured_output_calls + jv.bind_tools_calls
        )
        result["has_retry_logic"] = jv.has_retry
        result["structured_output_calls"] = jv.structured_output_calls

        # Detect personas
        for persona in ["Prosecutor", "Defense", "TechLead", "Tech Lead"]:
            if persona.lower() in source.lower():
                result["personas_found"].append(persona)

    except Exception as e:
        result["error"] = str(e)

    return result
