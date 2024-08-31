# CodeFlowMapper

## What is CodeFlowMapper?

CodeFlowMapper is an open-source tool designed to help developers quickly understand and visualize Python codebases. It generates a 3D visualization of all the files in the codebase, and for every file(parent node) you can see all the functions(child nodes) inside that file. This visualization can help developers quickly understand the structure of a codebase, and identify relationships between different files and functions.

## How to run CodeFlowMapper?
To run CodeFlowMapper, you can use the following command-line interface:
1. Create a virtual environment using the following command:
```bash
$ python3 -m venv venv
``` 
2. Activate the virtual environment:
```bash
$ source venv/bin/activate
```
3. Install the required dependencies:
```bash
$ pip install -r requirements.txt
```
4. Run the CodeFlowMapper script:
```bash
$ python main.py
```
After running the script, the model will be downloaded and after that you will be prompted to enter the path of the file or directory you want to visualize. 

Also you'll be prompted to enter directories you want to omit from the visualization (for example: `tests` , `__pycache__`, etc).

Then flask server will be started and you can access the visualization at http://localhost:5000.

HAPPY VISUALIZING! 

## Features

- Analyze single Python files or entire directories.
- Obsidian like visualization.
- Move around the 3D space and checks all the functions inside a specific file.
- Support for Python projects (currently limited to Python files).

## Current Limitations

- Only supports Python files and directories
- Does not yet handle complex Python features like decorators or lambda functions
- Limited to static analysis; dynamic code generation or evaluation is not supported

## Future Plans

- Extend support to other programming languages (C, C++, JavaScript, Go, Rust, etc.)
- Improve visualization options and interactivity.
- Add support for more complex Python language features.
- Explain with AI model.

## Contributing
We welcome contributions to CodeFlowMapper! If you have suggestions for improvements or bug fixes, please feel free to:

- Fork the repository
- Create a new branch `(git checkout -b feature/AmazingFeature)`
- Commit your changes `(git commit -m 'Add some AmazingFeature')`
- Push to the branch `(git push origin feature/AmazingFeature)`
- Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
Vishal Padia - vishalpadi9@gmail.com

Project Link: https://github.com/Vishal-Padia/CodeFlowMapper