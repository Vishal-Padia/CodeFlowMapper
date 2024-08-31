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

    Parameters:
        G: NetworkX graph object

    Returns:
        Dictionary containing nodes and edges data in a format that can be used by vis.js.
    """
    # Create a list of nodes and edges in the graph with specifc color, shape, and size attributes
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

    Parameters:
        directory_path (str): Path to the directory to parse.
        omit_dirs (list): List of directories to omit from parsing.

    Returns:
        List of Python files in the directory.
    """
    python_files = []
    # Walk through the directory and add Python files to the list
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d not in omit_dirs]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def parse_file(file_path: str):
    """
    Parse a Python file and return the AST (Abstract Syntax Tree) representation of the code.

    Parameters:
        file_path (str): Path to the Python file to parse.

    Returns:
        AST representation of the code.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        code_contents[file_path] = content
        # parse the code content into an AST
        tree = ast.parse(content)
    return tree


def extract_functions_and_imports(tree: ast.AST):
    """
    Extract function definitions and imports from the AST of a Python file.

    Parameters:
        tree: AST representation of the code.

    Returns:
        A tuple containing a dictionary of function definitions and a set of imported modules.
    """
    functions = {}
    imports = set()
    # Walk through the AST and extract function definitions and imports
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = {"calls": [], "line": node.lineno, "file": None}
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
    return functions, imports


def create_graph_with_directory_structure(
    functions: dict, imports: set, file_paths: list
):
    """
    Create a directed graph representing the directory structure of Python files, function calls, and imports.

    Parameters:
        functions (dict): Dictionary of function definitions.
        imports (set): Set of imported modules.
        file_paths (list): List of file paths for the Python files.

    Returns:
        NetworkX DiGraph object representing the directory structure
    """
    # Initialize a directed graph
    G = nx.DiGraph()

    # Add nodes for files, modules, and functions
    for file_path in file_paths:
        module_name = os.path.basename(file_path).replace(".py", "")
        G.add_node(file_path, label=module_name, color="#FF6B6B", shape="dot", size=15)

    for module in imports:
        G.add_node(module, label=module, color="#4ECDC4", shape="dot", size=10)

    for func_name, func_data in functions.items():
        G.add_node(func_name, label=func_name, color="#FFFFFF", shape="dot", size=7)
        if func_data["file"]:
            G.add_edge(func_data["file"], func_name)

    return G


@app.route("/")
def index():
    """
    A simple web page that displays an Obsidian-style graph with code display and AI explanation.
    """
    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Obsidian-style Graph with Code Display</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: #1E1E1E; color: #FFFFFF; font-family: Arial, sans-serif; }
                #container { display: flex; width: 100%; height: 100%; }
                #mynetwork { flex: 1; height: 100%; }
                #sidepanel { width: 0; height: 100%; overflow-y: auto; background-color: #2C2C2C; transition: width 0.5s; }
                #code-display { padding: 20px; white-space: pre-wrap; font-family: monospace; }
                #explain-button { margin: 20px; padding: 10px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
                #explanation { padding: 20px; background-color: #3C3C3C; margin-top: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div id="container">
                <div id="mynetwork"></div>
                <div id="sidepanel">
                    <pre id="code-display"></pre>
                    <button id="explain-button">Explain with AI</button>
                    <div id="explanation"></div>
                </div>
            </div>
            <script type="text/javascript">
                let network;
                fetch('/graph_data')
                    .then(response => response.json())
                    .then(data => {
                        var container = document.getElementById('mynetwork');
                        var options = {
                            nodes: {
                                font: { color: '#FFFFFF', size: 12 },
                                borderWidth: 2,
                                borderWidthSelected: 4,
                            },
                            edges: {
                                width: 1,
                                color: { color: '#FFFFFF', opacity: 0.3 },
                                smooth: { type: 'continuous' }
                            },
                            physics: {
                                forceAtlas2Based: {
                                    gravitationalConstant: -50,
                                    centralGravity: 0.01,
                                    springLength: 100,
                                    springConstant: 0.08
                                },
                                maxVelocity: 50,
                                solver: 'forceAtlas2Based',
                                timestep: 0.35,
                                stabilization: { iterations: 150 }
                            },
                            interaction: { hover: true }
                        };
                        network = new vis.Network(container, data, options);
                        
                        network.on("click", function (params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                fetch(`/get_code?node=${nodeId}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        document.getElementById('code-display').textContent = data.code;
                                        document.getElementById('sidepanel').style.width = '40%';
                                        document.getElementById('explanation').textContent = '';
                                    });
                            }
                        });
                        
                        # document.getElementById('explain-button').addEventListener('click', function() {
                        #     const code = document.getElementById('code-display').textContent;
                        #     fetch('/explain_code', {
                        #         method: 'POST',
                        #         headers: {
                        #             'Content-Type': 'application/json',
                        #         },
                        #         body: JSON.stringify({code: code}),
                        #     })
                        #     .then(response => response.json())
                        #     .then(data => {
                        #         document.getElementById('explanation').textContent = data.explanation;
                        #     });
                        # });
                    });
            </script>
        </body>
        </html>
        """
    )


@app.route("/graph_data")
def graph_data():
    """
    Jsonify the graph data for the web page to consume.

    Returns:
        JSON data containing the graph nodes and edges.
    """
    return jsonify(network_to_visjs(G))


@app.route("/get_code")
def get_code():
    """
    Get the code contents for a given node in the graph.

    Returns:
        JSON data containing the code contents.
    """
    node = request.args.get("node")
    code = code_contents.get(node, f"No code available for {node}")
    return jsonify({"code": code})


@app.route("/explain_code", methods=["POST"])
def explain_code():
    """
    Explain the code using the AI model.

    Returns:
        JSON data containing the explanation of the code.
    """
    code = request.json["code"]
    explanation = explainer(
        f"Explain this code:\n{code}", max_length=500, min_length=100, do_sample=False
    )[0]["generated_text"]
    return jsonify({"explanation": explanation})


def run_flask_app():
    """
    Run the Flask web application.
    """
    print("Starting the web server.")
    print(
        "Please open a web browser and go to http://127.0.0.1:5000/ to view the Obsidian-style graph visualization with code display and AI explanation."
    )
    app.run(debug=True)


def create_graph_from_directory(directory_path: str, omit_dirs: list):
    """
    Create a graph from the Python files in a directory.

    Parameters:
        directory_path (str): Path to the directory.
        omit_dirs (list): List of directories to omit.

    Returns:
        None
    """
    global G
    python_files = parse_directory(directory_path, omit_dirs)

    functions = {}
    imports = set()

    # Parse each Python file, extract functions and imports, and create a graph
    for i, file_path in enumerate(python_files):
        tree = parse_file(file_path)
        file_functions, file_imports = extract_functions_and_imports(tree)

        for func_name, func_data in file_functions.items():
            func_data["file"] = file_path

        functions.update(file_functions)
        imports.update(file_imports)

        print(
            f"Processing file {i+1}/{len(python_files)}: {os.path.basename(file_path)}"
        )

    # Create the graph with the directory structure
    G = create_graph_with_directory_structure(functions, imports, python_files)
    print("Graph creation completed.")


def main():
    directory_path = input("Enter the path to the directory: ")
    print(f"The input directory is: {directory_path}")
    omit_dirs = input("Enter the directories to omit (comma-separated): ").split(",")
    omit_list = [dir.strip() for dir in omit_dirs]
    create_graph_from_directory(directory_path, omit_list)
    run_flask_app()


if __name__ == "__main__":
    main()
