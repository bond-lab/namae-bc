if [ -d "./venv" ]
then
    source ./venv/bin/activate
    pip install -r requirements.txt
else
    python3.9 -m venv "./venv"
    source ./venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run doctest on all Python files in the web directory
for file in web/*.py; do
    echo "Running doctest on $file"
    PYTHONPATH=. python -m doctest "$file"
done

