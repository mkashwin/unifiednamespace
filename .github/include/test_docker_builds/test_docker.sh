#!/bin/bash
SHA_TAG=839890c2748df3d11c63c1469d189f1a2289e1a7
image_name=uns/test_image
echo "Check for [tool.poetry.scripts]"
if ! grep -q "^\[tool.poetry.scripts\]" ./pyproject.toml; then
  echo "Error: [tool.poetry.scripts] section not found in pyproject.toml"
  exit 1
fi
echo "Validating Docker Entrypoint prior to build"
# Extract the entrypoint from Dockerfile
# trunk-ignore(shellcheck/SC2312)
# trunk-ignore(shellcheck/SC2002)
entry_point=$(cat ./Dockerfile | grep "^ENTRYPOINT")
if [[ ! "${entry_point}" =~ ^ENTRYPOINT\ \[\"poetry\",\ \"run\",\ \".+\"\]$ ]]; then
    echo "Error: Entrypoint should be in the format [\"poetry\", \"run\", \"<command>\"]"
    exit 1
fi
echo "Entrypoint for Docker is: ${entry_point}"
# Extract the command/script name to be run
# trunk-ignore(shellcheck/SC2312)
command="$(echo "${entry_point}" | awk '{print $4}' | tr -d '",]')"
# check in pyproject if it is a script.
script_name=$( grep "^${command} =" ./pyproject.toml)
if [[  ! ${script_name} == *':main"' ]]; then
  # the script is not referencing a main function, must be a module
  echo "Validating if ${command} is a valid module command"
  # Check if command exists in the project
  if [[ -z ${script_name} ]]; then
    echo "Error: Command ${command} not found in the project. Should have had a dependency  entry in pyproject.toml" 
    exit 1
  fi
  main_entry=$(echo "${entry_point}" | awk '{print $5}' | tr -d '",]')
  python_module=${main_entry%:*}
  function=${main_entry##*:}
  class=${function%.*}
else    
  # command was found in pyproject.toml   
  main_entry=$(grep "^${command} =" ./pyproject.toml | awk '{print $3}' | tr -d '"')
  echo "Validate if ${main_entry} points to a valid python function"
  python_module=${main_entry%:*}
  function=${main_entry##*:}
  if [[ -z ${main_entry} ]]; then
    echo "Error: Script entry for ${command} not found in [tool.poetry.scripts] section of pyproject.toml "
    exit 1
  fi          
fi
echo "Static Validation successful!"
echo "Creating Docker: ${image_name}:${SHA_TAG}"
docker build -t "${image_name}:${SHA_TAG}" --build-arg GIT_HASH="${SHA_TAG::7}" -f ./Dockerfile ..
# Run the Docker tests
echo "Running tests for Docker image: ${image_name}:${SHA_TAG}"
docker run --entrypoint "sh" -e python_module="${python_module}" -e function="${function}" -e class="${class}" "${image_name}:${SHA_TAG}" -c '
  if [ ! -d "/02_mqtt-cluster" ]; then
    echo "Error: Folder /02_mqtt-cluster not found in Docker image"
    exit 1
  else
    echo "Success:  Folder /02_mqtt-cluster is present"
  fi
  if [ ! "$(ls -AR /app/src | grep -E ".py$" | wc -l)" -gt "0" ]; then
    echo "Error: No .py files found in folder /app/src"
    exit 1
  else
    echo "Success:  Python Files are present"
  fi
  if [ ! -f "/app/pyproject.toml" ]; then
    echo "Error: pyproject.toml file not found in folder /app"
    exit 1
  else
    echo "Success:  pyproject.toml file found"
  fi
  if [ -d "/app/test" ]; then
    echo "Error: test folder not found in folder /app"
    exit 1
  else
    echo "Success:  test folder was not copied to the Docker"
  fi
  
  poetry run python -m compileall -q /app || (echo "Error: compileall failed" && exit 1)
  if [[ -z $class  ]];then  
    # function is not null, check if the entry in pyproject.toml scripts is valid
    entry_valid=$(poetry run python -c "import ${python_module} as module;print( '\''${function}'\''  in dir(module))")
  elif poetry run python -c "from ${python_module} import ${class};  x=${function};" &> /dev/null; then
    entry_valid=True
  fi
  if [ ! "$entry_valid" == "True" ];then
    echo "Error: Invalid entry ${python_module}:${function}"
    exit 1
  fi
  echo "Docker image tests passed successfully"
'