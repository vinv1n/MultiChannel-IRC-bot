from app import create_api

# crates api and flask app
app = create_api()

def main():
    app.run(host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()