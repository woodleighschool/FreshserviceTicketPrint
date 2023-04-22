# FreshserviceTicketPrint

This Python script listens for a POST request at the endpoint `/webhook` and then generates a ticket image using data from a Freshservice ticket API. The generated image is printed to a local printer using a separate Flask API.

## Dependencies

-   Python 3.11
-   Flask
-   Requests
-   qrcode
-   Pillow

## Installation

1. Clone the repository.
2. Install the required packages using pip: `pip install -r requirements.txt`
3. Set environment variables `API_TOKEN` and `FRESHSERVICE_API_KEY`.
4. Run the Flask application: `python main.py`

The application should now be listening for POST requests at `http://localhost:5000/webhook`.

## Usage

Make a POST request to the `/webhook` endpoint with the following JSON data:

```
{
    "ticket_number": "123"
}
```

This will generate a ticket image for the ticket with ID `123` and print it to the configured printer. The generated image will also be saved in the `queue` directory.

If the request contains an invalid ticket number or fails to connect to the printer, an appropriate error response will be returned.
