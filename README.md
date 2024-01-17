# FreshserviceTicketPrint

This Python script listens for a POST request at the endpoint `/webhook` and then generates a ticket/label image using data from the Freshservice API. The generated image is send to [woodleighschool/PrintService](https://github.com/woodleighschool/PrintService), which prints the sticker out.

![Example Label](https://raw.githubusercontent.com/woodleighschool/FreshserviceTicketPrint/main/example.png)

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
This will generate a ticket image for the ticket with ID `123` and print it out.

If the request contains an invalid ticket number or fails to connect to the printer, the error will be posted back, as `{'status': 'Failed', 'reason': <reason>}`, else you will get `{'status': 'Success'}`.

You can also put this application behind cloudflared, then use Freshservice's webhooks to sent tickets to be printed automatically.
