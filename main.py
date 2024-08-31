import os
import ast
import flask
import networkx as nx
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

G = None


def network_to_visjs(G):
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
    python_files = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d not in omit_dirs]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def parse_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    return tree


def extract_functions_and_imports(tree):
    functions = {}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = {"calls": [], "line": node.lineno, "file": None}
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
    return functions, imports


def create_graph_with_directory_structure(functions, imports, file_paths):
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

    return G


@app.route("/")
def index():
    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Obsidian-style Graph Visualization</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: #1E1E1E; }
                #mynetwork { width: 100%; height: 100%; }
            </style>
        </head>
        <body>
            <div id="mynetwork"></div>
            <script type="text/javascript">
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
                        var network = new vis.Network(container, data, options);
                    });
            </script>
        </body>
        </html>
        """
    )


@app.route("/graph_data")
def graph_data():
    return jsonify(network_to_visjs(G))


def run_flask_app():
    print("Starting the web server.")
    print(
        "Please open a web browser and go to http://127.0.0.1:5000/ to view the Obsidian-style graph visualization."
    )
    app.run(debug=True)


def create_graph_from_directory(directory_path, omit_dirs):
    global G
    python_files = parse_directory(directory_path, omit_dirs)

    functions = {}
    imports = set()

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
