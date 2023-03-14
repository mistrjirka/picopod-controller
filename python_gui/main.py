import tkinter as tk
import sys
import glob
import serial
from time import sleep
import json

SLEEP_TIME = 0.03
BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"


FONT = "Helvetica 13"
FONT_BOLD = "Helvetica 12 bold"


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class PicopodControler:
    def __init__(self, root,  port_object, chat_field, entry, my_id, reciever_id, channel):
        self.s = None
        self.port = port_object
        self.chat_field = chat_field
        self.entry = entry
        self.root = root
        root.bind('<Return>', self.que_message)
        self.my_id = my_id
        self.reciever_id = reciever_id
        self.channel = channel
        self.queue = []
        self.connect_queue = []

    def loop(self, ports):
        while True:
            sleep(SLEEP_TIME)
            self.run_tk()
            self.get_messages()
            if (len(self.connect_queue) > 0):
                self.connect_to_port(self.connect_queue[0])
                self.connect_queue.pop(0)

            if (len(self.queue) > 0):
                self.send_message(self.queue[0])
                self.queue.pop(0)

    def run_tk(self):
        self.root.update()

    def que_connection(self):
        port = self.port.get()
        self.connect_queue.append(port)

    def connect_to_port(self, port):
        if self.s is not None:
            self.s.close()
        if (port != "Select an Option"):
            self.s = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
            sleep(2)
            self.set_my_id()

    def que_message(self, e=None):
        message = self.entry.get()
        self.queue.append(message)
        self.entry.set("")

    def send_message(self, message):
        if self.s is not None:
            self.s.write(b"c")
            self.s.write(f"{self.my_id.get()}".encode())
            sleep(0.1)
            self.s.write(b"s")
            self.s.write(b"3")
            self.s.write(b"2")
            self.s.write(f"{self.reciever_id.get()}".encode())
            self.s.write(f"{self.my_id.get()}".encode())
            self.s.write(f"{self.channel.get()}".encode())
            self.s.write(f"{message}>".encode())
            self.s.flush()
            self.chat_field.insert(tk.END, f"You -> {message}\n")

    def get_messages(self):
        if self.s != None:
            if (self.s.in_waiting > 0):
                print("noice")
                serialString = self.s.readline().replace(b"\r", b"").replace(b"\n", b"")
                print("recieved raw", serialString)
                    
                try:
                    serialString = serialString.decode(
                    'utf_8')
                    message = json.loads(serialString.replace(
                        "\r", "").replace("\n", ""))
                    print("recieved message", message)
                    if (message["type"] == 2):
                        self.chat_field.insert(
                            tk.END, f"recieved confirmation {message['sender']} -> {message['rssi']} db\n")
                    elif message["type"] == 3:
                        self.chat_field.insert(
                            tk.END, f"com {message['sender']} -> {message['content']} (RSSI: {message['rssi']}db) \n")
                    elif message["type"] == -3:
                        self.my_id.set(message["data"])
                    elif message["type"] == -1:
                        self.chat_field.insert(
                            tk.END, f"|sending finished|\n")
                    else:
                        print(message)
                except Exception as e:
                    print(e)
              
    def set_my_id(self):
        if self.s is not None:
            print("trying to get name")
            self.s.write(b"g")
            self.s.flush()


def main():
    root = tk.Tk()
    root.title("Picopod comunicator")
    root.geometry('1200x900')
    frame_messages = tk.Frame(root)

    frame_port_select = tk.Frame(root)
    frame_port_select.pack(side=tk.BOTTOM)

    port_selected = tk.StringVar(frame_port_select)
    txt = tk.Text(frame_messages, bg=BG_COLOR,
                  fg=TEXT_COLOR, font=FONT, width=60)
    txt.grid(row=1, column=0, columnspan=2)
    scrollbar = tk.Scrollbar(txt)
    scrollbar.place(relheight=1, relx=0.974)

    port_selected.set("Select an Option")
    ports = serial_ports()
    ports_menu = tk.OptionMenu(frame_port_select, port_selected, *ports)
    ports_menu.pack(side=tk.LEFT)
    message = tk.StringVar(root)

    e = tk.Entry(frame_messages, bg="#2C3E50",
                 fg=TEXT_COLOR, font=FONT, width=55, textvariable=message)
    e.grid(row=2, column=0)
    frame_messages.pack()
    # Submit button
    # Whenever we click the submit button, our submitted
    # option is printed ---Testing purpose
    my_id = tk.StringVar()
    my_id_entry = tk.Entry(frame_port_select, textvariable=my_id)
    my_id.set("0")
    reciever_id = tk.StringVar()
    reciever_id_entry = tk.Entry(frame_port_select, textvariable=reciever_id)
    reciever_id.set("1")
    channel = tk.StringVar()
    channel_entry = tk.Entry(frame_port_select, textvariable=channel)
    channel.set("3")
    id_str = tk.StringVar(root)
    id_label = tk.Label(frame_port_select, textvariable=id_str)
    id_str.set("My id: ")

    rec_id_str = tk.StringVar(root)
    my_id_entry.pack(side=tk.RIGHT)
    id_label.pack(side=tk.RIGHT)

    rec_label = tk.Label(frame_port_select, textvariable=rec_id_str)
    rec_id_str.set("Reciever id: ")

    reciever_id_entry.pack(side=tk.RIGHT)
    rec_label.pack(side=tk.RIGHT)

    channel_str = tk.StringVar(root)
    channel_label = tk.Label(frame_port_select, textvariable=channel_str)
    channel_str.set("Channel:")
    channel_entry.pack(side=tk.RIGHT)
    channel_label.pack(side=tk.RIGHT)

    driver = PicopodControler(root, port_selected, txt,
                              message, my_id, reciever_id, channel)

    send = tk.Button(frame_messages, text="Send", font=FONT_BOLD, bg=BG_GRAY,
                     command=driver.que_message).grid(row=2, column=1)

    submit_button = tk.Button(
        frame_port_select, text='Select port', command=driver.que_connection)
    submit_button.pack(side=tk.LEFT)

    driver.loop(ports)


if __name__ == '__main__':
    main()
