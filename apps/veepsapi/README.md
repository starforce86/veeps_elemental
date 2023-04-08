
## Running black for code formatting
**Make sure you're in teh veepsapi directory, or within the docker-compose environment**

1. run `black .`


## Running debug within VSCode 
 ** Todo **

## Running debug within IntelliJ/PyCharm
1. Make sure docker container builds
   1. `docker-compose build backend`
2. Add docker container interpreter to project python interpreter
   1. ... (navigate through menus)
3. Add Django server configuration
   1. Make sure Django support is enabled
      1. Point application root to apps/veepsapi
      2. Load settings.py from config/settings.py
   2. Make sure to set host to 0.0.0.0
   3. Set breakpoints! 

## Container operations
### Run commands within container
`docker-compose run backend bash`

### Installing packages within the container
Within the container run `pipenv install {packagename}` and it will be added to the `Pipfile` and `Pipfile.lock`
However it won't be immediately available due to the fact that the storage within that running container is ephemeral.
To make it permanent, you just need to rebuild the container which will pull from the newly updated `Pipfile` 

To rebuild the container run `docker build backend`

