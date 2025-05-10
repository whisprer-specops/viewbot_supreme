1. Create a Virtual Environment:
e.g. (mine is called `myenv`)
`python -m venv myenv`


2. i.  to Activate the Virtual Environment: in windows
`thesea\Scripts\activate`

2. ii. to Deactivate the Virtual Environment:
`deactivate`

3. i. Installing Packages:

`pip install package_name package_name package_name`

3. ii. Listing Installed Packages:
`pip list`


**fren can ou show me what format the contents of a venv requirements.txt should be in?**

**chatGPT** _said:_
ertainly! The requirements.txt file in a Python virtual environment (venv) is used to list all the dependencies that your project needs. The format is quite simple: each line in the file specifies a package that your project depends on, and optionally, the version of the package.

- Basic Format

package_name==version_number

- Example of a requirements.txt File

requests==2.25.1
aiohttp==3.7.4.post0
selenium==3.141.0
Flask==1.1.2
numpy==1.19.5
Format Variations


- Specific Version: If you want to pin a package to a specific version:

requests==2.25.1

- Version Range: If you want a range of versions:

requests>=2.24.0,<3.0.0

- Latest Version: If you want to install the latest version of a package, you can just list the package name:

requests

- Comments: You can add comments to your requirements.txt file by starting a line with a #:

# This is a comment
requests==2.25.1

- Editable Install: If you’re working on a package locally and want to install it in an editable mode (useful for development), you can specify the local path:

-e .
 
- Automatically Generating requirements.txt
If you want to generate a requirements.txt file from the current environment, you can use the following command:

pip freeze > requirements.txt

- This will output the installed packages and their versions in the current virtual environment to requirements.txt.

[Example Generated File]
Here’s what a generated requirements.txt might look like:

aiohttp==3.7.4.post0
async-timeout==3.0.1
attrs==20.3.0
chardet==3.0.4
idna==2.10
multidict==5.1.0
requests==2.25.1
selenium==3.141.0
urllib3==1.26.4
yarl==1.6.3

- This format is what pip expects when you run:

```bash
pip install -r requirements.txt
```

- This command will install all the packages listed in the file with the specified versions.
