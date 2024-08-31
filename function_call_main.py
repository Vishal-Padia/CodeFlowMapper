import os
import ast
import flask
import networkx as nx
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

G = None


def network_to_visjs(G):
    nodes = [
        {"id": node, "label": G.nodes[node].get("label", node)} for node in G.nodes()
    ]
    edges = [{"from": source, "to": target} for source, target in G.edges()]
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
                imports.add(alias.name.split(".")[0])  # Add imported module names
    return functions, imports


def analyze_function_calls(tree, functions):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            caller = None
            for parent in ast.walk(tree):
                if isinstance(parent, ast.FunctionDef) and node in ast.walk(parent):
                    caller = parent.name
                    break
            if caller and caller in functions:
                if isinstance(node.func, ast.Name):
                    called_func = node.func.id
                    functions[caller]["calls"].append(called_func)
                elif isinstance(node.func, ast.Attribute):
                    called_func = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        object_name = node.func.value.id
                        functions[caller]["calls"].append(
                            f"{object_name}.{called_func}"
                        )
                    else:
                        functions[caller]["calls"].append(called_func)
                else:
                    if hasattr(node.func, "id"):
                        functions[caller]["calls"].append(node.func.id)
                    elif hasattr(node.func, "attr"):
                        functions[caller]["calls"].append(node.func.attr)


def create_graph_with_directory_structure(functions, imports, file_paths):
    G = nx.DiGraph()

    directory_nodes = {}

    for file_path in file_paths:
        directory = os.path.dirname(file_path)
        module_name = os.path.basename(file_path).replace(".py", "")

        # Add directory node
        if directory not in directory_nodes:
            G.add_node(directory, label=directory, shape="box", color="lightblue")
            directory_nodes[directory] = True

        # Add file node
        G.add_node(file_path, label=module_name, shape="ellipse", color="lightgreen")
        G.add_edge(directory, file_path)

        for func, data in functions.items():
            if data["file"] == file_path:
                G.add_node(func, module=module_name)
                G.add_edge(file_path, func)
                for call in data["calls"]:
                    if call in functions:
                        G.add_edge(func, call)

    for module in imports:
        G.add_node(module, module="import")

    return G


@app.route("/")
def index():
    return render_template_string(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Function Call Graph</title>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {
                width: 100%;
                height: 600px;
                border: 1px solid lightgray;
            }
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
                            shape: 'dot',
                            size: 10,
                            font: {
                                size: 12,
                                color: '#000000'
                            },
                            borderWidth: 2,
                            color: {
                                background: '#87CEEB',
                                border: '#000000',
                                borderWidth: 2
                            }
                        },
                        edges: {
                            width: 1,
                            arrows: {
                                to: { enabled: true, scaleFactor: 0.5 }
                            }
                        },
                        physics: {
                            forceAtlas2Based: {
                                gravitationalConstant: -26,
                                centralGravity: 0.005,
                                springLength: 230,
                                springConstant: 0.18
                            },
                            maxVelocity: 146,
                            solver: 'forceAtlas2Based',
                            timestep: 0.35,
                            stabilization: { iterations: 150 }    

                        }
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
        "Please open a web browser and go to http://127.0.0.1:5000/ to view the graph."
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
        analyze_function_calls(tree, functions)

        G = create_graph_with_directory_structure(
            functions, imports, python_files[: i + 1]
        )

        print(
            f"Processing file {i+1}/{len(python_files)}: {os.path.basename(file_path)}"
        )

    print("Graph creation completed.")


def main():
    directory_path = input("Enter the path to the directory: ")
    print(f"The input directory is: {directory_path}")
    omit_dirs = input("Enter the directories to omit (comma-separated): ").split(",")
    omit_list = [func.strip() for func in omit_dirs]
    create_graph_from_directory(directory_path, omit_list)
    run_flask_app()


if __name__ == "__main__":
    main()
