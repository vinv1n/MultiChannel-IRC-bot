from app import create_api

# crates api and flask app
app = create_api()

def main():
    app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()