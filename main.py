from flask import Flask, request, jsonify
import os
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


# main run block
def run(ticket_number):
    # Freshservice API Key
    freshservice_api_key = os.getenv('FRESHSERVICE_API_KEY')

    # Make the API request to get the ticket details
    url = f'https://woodleigh.freshservice.com/api/v2/tickets/{ticket_number}?include=requester'
    headers = {'Content-Type': 'application/json'}
    auth = (f'{freshservice_api_key}', 'X')
    response = requests.get(url, headers=headers, auth=auth)

    # Check the response status code
    if response.status_code != 200:
        raise ValueError(f"Invalid Ticket: {ticket_number}")

    # Generate required data to paste in the output
    ticket_data = response.json()
    ticket_url = f'https://servicedesk.woodleigh.vic.edu.au/a/tickets/{ticket_number}'
    requester_name = ticket_data.get(
        'ticket', {}).get('requester', {}).get('name')
    compnow_id = ticket_data.get('ticket', {}).get(
        'custom_fields', {}).get('compnow_ticket_no')

    # make sure queue path exists
    if not os.path.exists("queue"):
        os.makedirs("queue")

    # Generate the image to print
    generate_ticket(ticket_number, ticket_url, requester_name, compnow_id)

    # Print the generated image
    print_ticket(ticket_number)


# generate_ticket function
def generate_ticket(ticket_number, ticket_url, requester_name, compnow_id):
    # Create a QR code for the ticket URL
    qr = qrcode.QRCode(version=1, box_size=16, border=0)
    qr.add_data(ticket_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Load the template image, Paste QR Code
    template_img = Image.open('assets/template.png')
    template_img.paste(qr_img, (19, 19))
    draw = ImageDraw.Draw(template_img)

    # Add the ticket number(s) to the right of the QR code
    font = ImageFont.truetype('assets/Arial Bold.ttf', size=48)
    draw.text(
        (566, 170), f'HelpDesk Ticket: #{ticket_number}', font=font, fill='black')
    if compnow_id is not None and compnow_id != '':
        draw.text(
            (566, 512), f'CompNow Ticket: #{compnow_id}', font=font, fill='black')

    # Add the requester's name underneath the ticket number
    max_width = 596
    max_height = 316
    font_size = 50
    font = ImageFont.truetype('assets/Arial.ttf', size=font_size)
    name_lines = []
    name_line = ""
    for word in requester_name.split():
        if font.getsize(name_line + word)[0] <= max_width:
            name_line += word + " "
        else:
            name_lines.append(name_line.strip())
            name_line = word + " "
    if name_line:
        name_lines.append(name_line.strip())

    name_x = 566
    name_y = 231
    for name_line in name_lines:
        name_width, name_height = font.getsize(name_line)
        while name_width > max_width:
            font_size -= 1
            font = ImageFont.truetype('assets/Arial.ttf', size=font_size)
            name_width, name_height = font.getsize(name_line)
        if name_height > max_height:
            name_y = 231 + (max_height - name_height) // 2
        draw.text((name_x, name_y), name_line, font=font, fill='black')
        name_y += name_height

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
            'http://127.0.0.1:5001/print_image', headers=headers, files=files)
        if response.status_code != 200:
            raise ValueError(f"Failed to print?")
    except:
        raise ValueError(f"Failed to connect to printer")


if __name__ == '__main__':
    app.run()
