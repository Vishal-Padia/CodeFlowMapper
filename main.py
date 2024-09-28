import os
import ast
import flask
import networkx as nx
from flask import Flask, render_template_string, jsonify, request
from transformers import pipeline

app = Flask(__name__)

G = None
code_contents = {}

# Initialize the code explanation model
explainer = pipeline("text2text-generation", model="facebook/bart-large-cnn")


def network_to_visjs(G: nx.DiGraph):
    """
    Convert a NetworkX graph to a dictionary format that can be used by vis.js.
    """
    nodes = [
        {
            "id": node,
            "label": G.nodes[node].get("label", node),
            "color": G.nodes[node].get("color", "#FFFFFF"),
            "shape": G.nodes[node].get("shape", "dot"),
            "size": G.nodes[node].get("size", 10),
        }
        for node in G.nodes()
    ]
    edges = [
        {"from": source, "to": target, "color": "#FFFFFF"}
        for source, target in G.edges()
    ]
    return {"nodes": nodes, "edges": edges}


def parse_directory(directory_path: str, omit_dirs: list):
    """
    Parse a directory and return a list of Python files in the directory.
    """
    python_files = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d not in omit_dirs]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def parse_file(file_path: str):
    """
    Parse a Python file and return the AST (Abstract Syntax Tree) representation of the code.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        code_contents[file_path] = content
        tree = ast.parse(content)
    return tree


def extract_functions_and_imports(tree: ast.AST):
    """
    Extract function definitions and imports from the AST of a Python file.
    Also track function calls for execution path visualization.
    """
    functions = {}
    imports = set()
    function_stack = []
    current_func = None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            current_func = node.name
            functions[node.name] = {"calls": [], "line": node.lineno, "file": None}
            function_stack.append(current_func)

        elif isinstance(node, ast.Call) and current_func:
            if isinstance(node.func, ast.Name):
                functions[current_func]["calls"].append(node.func.id)

        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.Return):
            if function_stack:
                function_stack.pop()
            current_func = function_stack[-1] if function_stack else None

    return functions, imports


def create_graph_with_directory_structure(
    functions: dict, imports: set, file_paths: list
):
    """
    Create a directed graph representing the directory structure of Python files, function calls, and imports.
    """
    G = nx.DiGraph()

    for file_path in file_paths:
        module_name = os.path.basename(file_path).replace(".py", "")
        G.add_node(file_path, label=module_name, color="#FF6B6B", shape="dot", size=15)

    for module in imports:
        G.add_node(module, label=module, color="#4ECDC4", shape="dot", size=10)

    for func_name, func_data in functions.items():
        G.add_node(func_name, label=func_name, color="#FFFFFF", shape="dot", size=7)
        if func_data["file"]:
            G.add_edge(func_data["file"], func_name)

        for called_func in func_data["calls"]:
            if called_func in functions:
                G.add_edge(func_name, called_func)

    return G


@app.route("/")
def index():
    """
    A web page displaying the graph with search and code execution path visualization.
    """
    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Graph Visualization</title>
            <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: #1E1E1E; color: #FFFFFF; }
                #container { display: flex; width: 100%; height: 100%; }
                #mynetwork { flex: 1; height: 100%; }
                #sidepanel { width: 0; transition: width 0.5s; overflow-y: auto; }
                #code-display, #explanation { padding: 20px; white-space: pre-wrap; font-family: monospace; color: #FFFFFF; }
                #search-container { position: absolute; top: 20px; left: 20px; z-index: 10; }
                #search-input { padding: 8px; }
                #explain-button { padding: 8px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                #close-button { position: absolute; top: 10px; right: 10px; padding: 5px 10px; background-color: #f44336; color: white; border: none; cursor: pointer; }
                .blurred { opacity: 0.3; }
            </style>
        </head>
        <body>
            <div id="search-container">
                <input type="text" id="search-input" placeholder="Search function...">
                <button id="search-button">Search</button>
            </div>
            <div id="container">
                <div id="mynetwork"></div>
                <div id="sidepanel">
                    <button id="close-button">X</button>
                    <pre id="code-display"></pre>
                    <button id="explain-button">Explain with AI</button>
                    <div id="explanation"></div>
                </div>
            </div>
            <script>
                let network;
                let highlightActive = false;
                let selectedNode = null;

                fetch('/graph_data')
                    .then(response => response.json())
                    .then(data => {
                        var container = document.getElementById('mynetwork');
                        var options = {
                            nodes: { font: { color: '#FFFFFF' }, size: 12 },
                            edges: { color: '#FFFFFF', smooth: true },
                            physics: { stabilization: false }
                        };
                        network = new vis.Network(container, data, options);
                        
                        // Search functionality
                        document.getElementById('search-button').addEventListener('click', performSearch);
                        document.getElementById('search-input').addEventListener('keyup', function(event) {
                            if (event.key === 'Enter') {
                                performSearch();
                            }
                        });

                        // Handle node click to show code and highlight execution path
                        network.on("click", function (params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                fetch(`/get_code?node=${nodeId}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        document.getElementById('code-display').textContent = data.code;
                                        document.getElementById('sidepanel').style.width = '40%';
                                        document.getElementById('explanation').textContent = '';
                                        highlightExecutionPath(nodeId);
                                    });
                            }
                        });

                        // AI explanation of code
                        document.getElementById('explain-button').addEventListener('click', function() {
                            const code = document.getElementById('code-display').textContent;
                            fetch('/explain_code', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({code: code}),
                            })
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('explanation').textContent = data.explanation;
                            });
                        });

                        // Close button for sidepanel
                        document.getElementById('close-button').addEventListener('click', function() {
                            document.getElementById('sidepanel').style.width = '0';
                            resetHighlight();
                        });
                    });

                function performSearch() {
                    const searchTerm = document.getElementById('search-input').value;
                    let foundNode = network.body.data.nodes.get().find(node => node.label === searchTerm);
                    if (foundNode) {
                        network.selectNodes([foundNode.id]);
                        network.focus(foundNode.id, { scale: 1.5 });
                    } else {
                        alert('Function not found.');
                    }
                }

                function highlightExecutionPath(nodeId) {
                    resetHighlight();
                    selectedNode = nodeId;
                    
                    const allNodes = network.body.nodes;
                    const allEdges = network.body.edges;
                    
                    // Dim all nodes and edges
                    Object.values(allNodes).forEach(node => {
                        node.options.color.background = '#1E1E1E';
                        node.options.color.border = '#1E1E1E';
                    });
                    Object.values(allEdges).forEach(edge => {
                        edge.options.color.color = '#1E1E1E';
                    });
                    
                    // Highlight the selected node and its connections
                    const connectedNodes = network.getConnectedNodes(nodeId);
                    const connectedEdges = network.getConnectedEdges(nodeId);
                    
                    allNodes[nodeId].options.color.background = '#FF0000';
                    allNodes[nodeId].options.color.border = '#FF0000';
                    
                    connectedNodes.forEach(connectedNodeId => {
                        allNodes[connectedNodeId].options.color.background = '#FFFFFF';
                        allNodes[connectedNodeId].options.color.border = '#FFFFFF';
                    });
                    
                    connectedEdges.forEach(edgeId => {
                        allEdges[edgeId].options.color.color = '#FFFFFF';
                    });
                    
                    highlightActive = true;
                    network.redraw();
                }

                function resetHighlight() {
                    if (highlightActive) {
                        const allNodes = network.body.nodes;
                        const allEdges = network.body.edges;
                        
                        Object.values(allNodes).forEach(node => {
                            node.options.color.background = node.options.color.default;
                            node.options.color.border = node.options.color.default;
                        });
                        Object.values(allEdges).forEach(edge => {
                            edge.options.color.color = edge.options.color.default;
                        });
                        
                        highlightActive = false;
                        selectedNode = null;
                        network.redraw();
                    }
                }
            </script>
        </body>
        </html>
        """
    )


@app.route("/graph_data")
def graph_data():
    """
    Serve the graph data for visualization.
    """
    visjs_data = network_to_visjs(G)
    return jsonify(visjs_data)


@app.route("/get_code")
def get_code():
    """
    Serve the code for a clicked node.
    """
    node = request.args.get("node")
    return jsonify({"code": code_contents.get(node, "Code not found.")})


@app.route("/explain_code", methods=["POST"])
def explain_code():
    """
    Explain the code using AI when the user clicks the 'Explain' button.
    """
    code = request.json.get("code")
    explanation = explainer(code)[0]["summary_text"]
    return jsonify({"explanation": explanation})


if __name__ == "__main__":
    # Sample directory to parse (replace with your directory)
    directory_path = input("Enter the path to the directory to parse: ")
    print(f"Parsing directory: {directory_path}")

    omit_dirs = input("Enter the directories to omit (comma-separated): ").split(",")
    print(f"Omitting directories: {omit_dirs}")

    python_files = parse_directory(directory_path, omit_dirs)

    # Parse files and extract functions and imports
    all_functions = {}
    all_imports = set()
    for file_path in python_files:
        tree = parse_file(file_path)
        functions, imports = extract_functions_and_imports(tree)
        for func_name, func_data in functions.items():
            func_data["file"] = file_path
            all_functions[func_name] = func_data
        all_imports.update(imports)

    # Create the graph
    G = create_graph_with_directory_structure(all_functions, all_imports, python_files)

    # Run the Flask app
    app.run(debug=True)
