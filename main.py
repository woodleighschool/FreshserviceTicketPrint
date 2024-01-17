import os
from flask import Flask, request, jsonify
import requests
import qrcode
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    api_token = os.getenv('API_TOKEN')
    api_key = request.headers.get('Authorization')
    if api_key == f'Bearer {api_token}':
        data = request.get_json()
        ticket_number = data.get('ticket_number')
        if ticket_number:
            try:
                run(ticket_number)
                os.remove(f'queue/ticket_{ticket_number}.png')
                return jsonify({'status': 'Success'})
            except ValueError as e:
                return jsonify({'status': 'Failed', 'reason': str(e)}), 400
        else:
            return jsonify({'status': 'Failed', 'reason': 'No ticket number provided'}), 400
    else:
        return jsonify({'status': 'Unauthorized'}), 401

def get_ticket_value(ticket_data, keys, default=None):
    data = ticket_data.get('ticket', {})
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

# main run block
def run(ticket_number):
    # Freshservice API Key
    freshservice_api_key = os.getenv('FRESHSERVICE_API_KEY')

    # Make the API request to get the ticket details
    url = f'https://woodleigh.freshservice.com/api/v2/tickets/{ticket_number}?include=requester'
    headers = {'Content-Type': 'application/json'}
    auth = (f'{freshservice_api_key}', 'X')
    response = requests.get(url, headers=headers, auth=auth, timeout=10)

    # Check the response status code
    if response.status_code != 200:
        raise ValueError(f"Invalid Ticket: {ticket_number}")

    # Generate required data to paste in the output
    response_data = response.json()

    # make sure queue path exists
    if not os.path.exists("queue"):
        os.makedirs("queue")

    # Generate the image to print
    generate_ticket(ticket_number, response_data)

    # Print the generated image
    print_ticket(ticket_number)


# generate_ticket function
def generate_ticket(ticket_number, response_data):

    # define variables
    ticket_url = f'https://servicedesk.woodleigh.vic.edu.au/a/tickets/{ticket_number}'
    requester_name = get_ticket_value(response_data, ['requester', 'name'])
    requester_name = "Awesome IT (Requester Name)"
    compnow_id = get_ticket_value(
        response_data, ['custom_fields', 'compnow_ticket_no'])
    subject = get_ticket_value(
        response_data, ['subject'])
    global_x = 566
    global_buffer = 10  # space between lines
    current_y = 170  # initial y px to start the lines
    ticket_type = ''

    # Create a QR code for the ticket URL
    qr = qrcode.QRCode(version=1, box_size=16, border=0)
    qr.add_data(ticket_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Load the template image, Paste QR Code
    template_img = Image.open('assets/template.png')
    template_img.paste(qr_img, (19, 19))
    draw = ImageDraw.Draw(template_img)

    # Add Requesters name (auto size to fit sticker width)
    max_width = 596
    font_size = 50
    font = ImageFont.truetype('assets/Arial Bold.ttf', size=font_size)
    # Get width of the text
    text_width = draw.textlength(requester_name, font=font)
    while text_width > max_width:
        font_size -= 1
        font = ImageFont.truetype('assets/Arial Bold.ttf', size=font_size)
        text_width = draw.textlength(requester_name, font=font)
    draw.text((global_x, current_y), requester_name, font=font, fill='black')

    font = ImageFont.truetype('assets/Arial.ttf', size=48)
    # Try sus what type of ticket this is from the title
    if 'REPAIR' in subject:
        ticket_type = "Repair"
    elif 'Year 12 Wipe' in subject:
        ticket_type = "Year 12 Wipe"
    elif 'Machine returned' in subject:
        ticket_type = "Return"
    current_y = current_y + 48 + global_buffer
    # Add the ticket type if found
    if ticket_type != '':
        draw.text(
            (global_x, current_y), f'Type: {ticket_type}', font=font, fill='black')
        current_y = current_y + 48 + global_buffer
    # Add the helpdesk ID
    draw.text(
        (global_x, current_y), f'HelpDesk #: {ticket_number}', font=font, fill='black')
    # Add compnow ID if set
    if compnow_id is not None and compnow_id != '':
        current_y = current_y + 48 + global_buffer
        draw.text(
            (global_x, current_y), f'CompNow #: {compnow_id}', font=font, fill='black')

    # Save the final image
    ticket_image_path = f'queue/ticket_{ticket_number}.png'
    template_img.save(ticket_image_path)


# print_ticket function
def print_ticket(ticket_number):
    api_token = os.getenv('API_TOKEN')
    headers = {'Authorization': f'Bearer {api_token}'}
    files = {'file': open(f'queue/ticket_{ticket_number}.png', 'rb')}
    try:
        response = requests.post(
            'http://127.0.0.1:5001/print_image', headers=headers, files=files, timeout=10)
        if response.status_code != 200:
            raise ValueError("Failed to print?")
    except:
        raise ValueError("Failed to connect to printer")


if __name__ == '__main__':
    app.run()
