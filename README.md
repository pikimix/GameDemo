# Running
Clone the repo, cd into folder, create python virtual environment, install requirements, run main with required args

```
git clone
cd GameDemo
python3 -m venv .venv
pip3 install -r requirements.txt
python3 main.py -u $URL -p $PORT -n $PLAYER_NAME
```

# Update
cd into folder, git pull, activate venv, install requirements in case changed, run main with required args
```
cd GameDemo
git pull
source .venv/bin/activate
pip3 install -r requirements.txt
python3 main.py -u $URL -p $PORT -n $PLAYER_NAME
```

# Run
cd into folder, activate venv, run main with required args
```
cd GameDemo
source .venv/bin/activate
python3 main.py -u $URL -p $PORT -n $PLAYER_NAME
```
