def main():
    import uvicorn
    # Run the FastAPI app
    # host 0.0.0.0 allows external access (e.g. from Docker)
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
