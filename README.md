# CodeFlowMapper

CodeFlowMapper is an open-source tool that generates 3D visualizations of Python codebases, helping developers quickly understand and navigate complex projects.

## How does it look?
![CodeFlowMapper](CodeFlowMapper.mp4)

## Features

- **3D Visualization**: Generate interactive 3D maps of your Python codebase.
- **File and Function Mapping**: View files as parent nodes and functions as child nodes.
- **Customizable Omissions**: Exclude specific directories from visualization.
- **Obsidian-like Interface**: Familiar and intuitive visualization style.

## Quick Start
To run CodeFlowMapper, you can use the following command-line interface:
1. Clone the repository and navigate to the project directory:
```bash
$ git clone https://github.com/Vishal-Padia/CodeFlowMapper
$ cd CodeFlowMapper
```
2. Create a virtual environment using the following command:
```bash
$ python3 -m venv venv
``` 
3. Activate the virtual environment:
```bash
$ source venv/bin/activate
```
4. Install the required dependencies:
```bash
$ pip install -r requirements.txt
```
5. Run the CodeFlowMapper script:
```bash
$ python main.py
```
6. Follow the prompts to input your project path and exclude directories.

7. Access the visualization at `http://localhost:5000`.

 **It takes some time to generate the visualization, so please be patient.**
HAPPY VISUALIZING! 


## Usage

After launching, CodeFlowMapper will:
- Download necessary models (first-time only).
- Prompt for the path to your Python file or directory.
- Ask for directories to exclude from the visualization.
- Start a Flask server and generate the 3D visualization.

## Current Limitations

- Python files and directories only
- Basic Python feature support (no decorators or lambdas)
- Static analysis only

## Roadmap
- [ ] Add support for more programming languages
- [ ] Enhance visualization with more features
- [ ] Complex Python feature support
- [x] AI-Powered Code Analysis

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